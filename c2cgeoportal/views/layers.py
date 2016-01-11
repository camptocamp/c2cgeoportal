# -*- coding: utf-8 -*-

# Copyright (c) 2012-2016, Camptocamp SA
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.

from pyramid.httpexceptions import HTTPInternalServerError, \
    HTTPNotFound, HTTPBadRequest, HTTPForbidden
from pyramid.view import view_config

from sqlalchemy import func, distinct
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.sql import and_, or_
from sqlalchemy.orm.util import class_mapper
from sqlalchemy.orm.properties import ColumnProperty

from geoalchemy2 import Geometry, func as ga_func
from geoalchemy2.shape import from_shape, to_shape

import geojson
from geojson.feature import FeatureCollection, Feature

from shapely.geometry import asShape
from shapely.ops import cascaded_union
from shapely.geos import TopologicalError

from papyrus.protocol import Protocol, create_filter

from c2cgeoportal.lib.caching import get_region, \
    set_common_headers, NO_CACHE, PUBLIC_CACHE, PRIVATE_CACHE
from c2cgeoportal.lib.dbreflection import get_class, get_table
from c2cgeoportal.models import DBSessions, DBSession, Layer, RestrictionArea, Role

cache_region = get_region()


class Layers(object):

    def __init__(self, request):
        self.request = request
        self.settings = request.registry.settings.get("layers", {})
        self.layers_enum_config = self.settings.get("enum", None)

    def _get_geom_col_info(self, layer):
        """ Return information about the layer's geometry column, namely
        a ``(name, srid)`` tuple, where ``name`` is the name of the
        geometry column, and ``srid`` its srid.

        This function assumes that the names of geometry attributes
        in the mapped class are the same as those of geometry columns.
        """
        mapped_class = get_class(str(layer.geo_table))
        for p in class_mapper(mapped_class).iterate_properties:
            if not isinstance(p, ColumnProperty):
                continue  # pragma: no cover
            col = p.columns[0]
            if isinstance(col.type, Geometry):
                return col.name, col.type.srid
        raise HTTPInternalServerError(
            'Failed getting geometry column info for table "%s".' %
            str(layer.geo_table)
        )  # pragma: no cover

    def _get_layer(self, layer_id):
        """ Return a ``Layer`` object for ``layer_id``. """
        layer_id = int(layer_id)
        try:
            query = DBSession.query(Layer, Layer.geo_table)
            query = query.filter(Layer.id == layer_id)
            layer, geo_table = query.one()
        except NoResultFound:
            raise HTTPNotFound("Layer %d not found" % layer_id)
        except MultipleResultsFound:  # pragma: no cover
            raise HTTPInternalServerError(
                "Too many layers found with id %i" % layer_id
            )
        if not geo_table:  # pragma: no cover
            raise HTTPNotFound("Layer %d has no geo table" % layer_id)
        return layer

    def _get_layers_for_request(self):
        """ A generator function that yields ``Layer`` objects based
        on the layer ids found in the ``layer_id`` matchdict. """
        try:
            layer_ids = (
                int(layer_id) for layer_id in
                self.request.matchdict["layer_id"].split(",") if layer_id)
            for layer_id in layer_ids:
                yield self._get_layer(layer_id)
        except ValueError:
            raise HTTPBadRequest(
                "A Layer id in '%s' is not an integer" %
                self.request.matchdict["layer_id"]
            )  # pragma: no cover

    def _get_layer_for_request(self):
        """ Return a ``Layer`` object for the first layer id found
        in the ``layer_id`` matchdict. """
        return next(self._get_layers_for_request())

    def _get_protocol_for_layer(self, layer, **kwargs):
        """ Returns a papyrus ``Protocol`` for the ``Layer`` object. """
        cls = get_class(str(layer.geo_table))
        geom_attr = self._get_geom_col_info(layer)[0]
        return Protocol(DBSession, cls, geom_attr, **kwargs)

    def _get_protocol_for_request(self, **kwargs):
        """ Returns a papyrus ``Protocol`` for the first layer
        id found in the ``layer_id`` matchdict. """
        layer = self._get_layer_for_request()
        return self._get_protocol_for_layer(layer, **kwargs)

    def _proto_read(self, layer):
        """ Read features for the layer based on the self.request. """
        proto = self._get_protocol_for_layer(layer)
        if layer.public:
            return proto.read(self.request)
        user = self.request.user
        if user is None:
            raise HTTPForbidden()
        cls = proto.mapped_class
        geom_attr = proto.geom_attr
        ras = DBSession.query(RestrictionArea.area, RestrictionArea.area.ST_SRID())
        ras = ras.join(RestrictionArea.roles)
        ras = ras.join(RestrictionArea.layers)
        ras = ras.filter(Role.id == user.role.id)
        ras = ras.filter(Layer.id == layer.id)
        collect_ra = []
        use_srid = -1
        for ra, srid in ras.all():
            if ra is None:
                return proto.read(self.request)
            else:
                use_srid = srid
                collect_ra.append(to_shape(ra))
        if len(collect_ra) == 0:  # pragma: no cover
            raise HTTPForbidden()

        filter1_ = create_filter(self.request, cls, geom_attr)
        ra = cascaded_union(collect_ra)
        filter2_ = ga_func.ST_Contains(
            from_shape(ra, use_srid),
            getattr(cls, geom_attr)
        )
        filter_ = filter2_ if filter1_ is None else and_(filter1_, filter2_)

        return proto.read(self.request, filter=filter_)

    @view_config(route_name="layers_read_many", renderer="geojson")
    def read_many(self):
        set_common_headers(self.request, "layers", NO_CACHE)

        features = []
        for layer in self._get_layers_for_request():
            for f in self._proto_read(layer).features:
                f.properties["__layer_id__"] = layer.id
                features.append(f)

        return FeatureCollection(features)

    @view_config(route_name="layers_read_one", renderer="geojson")
    def read_one(self):
        set_common_headers(self.request, "layers", NO_CACHE)

        layer = self._get_layer_for_request()
        protocol = self._get_protocol_for_layer(layer)
        feature_id = self.request.matchdict.get("feature_id", None)
        feature = protocol.read(self.request, id=feature_id)
        if not isinstance(feature, Feature):
            return feature
        if layer.public:
            return feature
        if self.request.user is None:
            raise HTTPForbidden()
        geom = feature.geometry
        if not geom or isinstance(geom, geojson.geometry.Default):  # pragma: no cover
            return feature
        shape = asShape(geom)
        srid = self._get_geom_col_info(layer)[1]
        spatial_elt = from_shape(shape, srid=srid)
        allowed = DBSession.query(func.count(RestrictionArea.id))
        allowed = allowed.join(RestrictionArea.roles)
        allowed = allowed.join(RestrictionArea.layers)
        allowed = allowed.filter(Role.id == self.request.user.role.id)
        allowed = allowed.filter(Layer.id == layer.id)
        allowed = allowed.filter(or_(
            RestrictionArea.area.is_(None),
            RestrictionArea.area.ST_Contains(spatial_elt)
        ))
        if allowed.scalar() == 0:
            raise HTTPForbidden()

        return feature

    @view_config(route_name="layers_count", renderer="string")
    def count(self):
        set_common_headers(self.request, "layers", NO_CACHE)

        protocol = self._get_protocol_for_request()
        return protocol.count(self.request)

    @view_config(route_name="layers_create", renderer="geojson")
    def create(self):
        set_common_headers(self.request, "layers", NO_CACHE)

        if self.request.user is None:
            raise HTTPForbidden()

        self.request.response.cache_control.no_cache = True

        layer = self._get_layer_for_request()

        def check_geometry(r, feature, o):
            geom = feature.geometry
            if geom and not isinstance(geom, geojson.geometry.Default):
                shape = asShape(geom)
                srid = self._get_geom_col_info(layer)[1]
                spatial_elt = from_shape(shape, srid=srid)
                allowed = DBSession.query(func.count(RestrictionArea.id))
                allowed = allowed.join(RestrictionArea.roles)
                allowed = allowed.join(RestrictionArea.layers)
                allowed = allowed.filter(RestrictionArea.readwrite.is_(True))
                allowed = allowed.filter(Role.id == self.request.user.role.id)
                allowed = allowed.filter(Layer.id == layer.id)
                allowed = allowed.filter(or_(
                    RestrictionArea.area.is_(None),
                    RestrictionArea.area.ST_Contains(spatial_elt)
                ))
                if allowed.scalar() == 0:
                    raise HTTPForbidden()

                # check if geometry is valid
                self._validate_geometry(spatial_elt)

        protocol = self._get_protocol_for_layer(layer, before_create=check_geometry)
        try:
            features = protocol.create(self.request)
            return features
        except TopologicalError, e:
            self.request.response.status_int = 400
            return {"validation_error": str(e)}

    @view_config(route_name="layers_update", renderer="geojson")
    def update(self):
        set_common_headers(self.request, "layers", NO_CACHE)

        if self.request.user is None:
            raise HTTPForbidden()

        self.request.response.cache_control.no_cache = True

        feature_id = self.request.matchdict.get("feature_id", None)
        layer = self._get_layer_for_request()

        def check_geometry(r, feature, o):
            # we need both the "original" and "new" geometry to be
            # within the restriction area
            geom_attr, srid = self._get_geom_col_info(layer)
            geom_attr = getattr(o, geom_attr)
            geom = feature.geometry
            allowed = DBSession.query(func.count(RestrictionArea.id))
            allowed = allowed.join(RestrictionArea.roles)
            allowed = allowed.join(RestrictionArea.layers)
            allowed = allowed.filter(RestrictionArea.readwrite.is_(True))
            allowed = allowed.filter(Role.id == self.request.user.role.id)
            allowed = allowed.filter(Layer.id == layer.id)
            allowed = allowed.filter(or_(
                RestrictionArea.area.is_(None),
                RestrictionArea.area.ST_Contains(geom_attr)
            ))
            spatial_elt = None
            if geom and not isinstance(geom, geojson.geometry.Default):
                shape = asShape(geom)
                spatial_elt = from_shape(shape, srid=srid)
                allowed = allowed.filter(or_(
                    RestrictionArea.area.is_(None),
                    RestrictionArea.area.ST_Contains(spatial_elt)
                ))
            if allowed.scalar() == 0:
                raise HTTPForbidden()

            # check is geometry is valid
            self._validate_geometry(spatial_elt)

        protocol = self._get_protocol_for_layer(layer, before_update=check_geometry)
        try:
            feature = protocol.update(self.request, feature_id)
            return feature
        except TopologicalError, e:
            self.request.response.status_int = 400
            return {"validation_error": str(e)}

    def _validate_geometry(self, geom):
        validate = self.settings.get("geometry_validation", False)
        if validate and geom is not None:
            simple = DBSession.query(func.ST_IsSimple(geom)).scalar()
            if not simple:
                raise TopologicalError("Not simple")
            valid = DBSession.query(func.ST_IsValid(geom)).scalar()
            if not valid:
                reason = DBSession.query(func.ST_IsValidReason(geom)).scalar()
                raise TopologicalError(reason)

    @view_config(route_name="layers_delete")
    def delete(self):
        set_common_headers(self.request, "layers", NO_CACHE)

        if self.request.user is None:
            raise HTTPForbidden()

        self.request.response.cache_control.no_cache = True

        feature_id = self.request.matchdict.get("feature_id", None)
        layer = self._get_layer_for_request()

        def security_cb(r, o):
            geom_attr = getattr(o, self._get_geom_col_info(layer)[0])
            allowed = DBSession.query(func.count(RestrictionArea.id))
            allowed = allowed.join(RestrictionArea.roles)
            allowed = allowed.join(RestrictionArea.layers)
            allowed = allowed.filter(RestrictionArea.readwrite.is_(True))
            allowed = allowed.filter(Role.id == self.request.user.role.id)
            allowed = allowed.filter(Layer.id == layer.id)
            allowed = allowed.filter(or_(
                RestrictionArea.area.is_(None),
                RestrictionArea.area.ST_Contains(geom_attr)
            ))
            if allowed.scalar() == 0:
                raise HTTPForbidden()

        protocol = self._get_protocol_for_layer(layer, before_delete=security_cb)
        return protocol.delete(self.request, feature_id)

    @view_config(route_name="layers_metadata", renderer="xsd")
    def metadata(self):
        set_common_headers(self.request, "layers", PRIVATE_CACHE)

        layer = self._get_layer_for_request()
        if not layer.public and self.request.user is None:
            raise HTTPForbidden()

        return self._metadata(str(layer.geo_table), layer.exclude_properties)

    @cache_region.cache_on_arguments()
    def _metadata(self, geo_table, exclude_properties):
        return get_class(
            geo_table,
            exclude_properties=exclude_properties
        )

    @view_config(route_name="layers_enumerate_attribute_values", renderer="json")
    def enumerate_attribute_values(self):
        set_common_headers(self.request, "layers", PUBLIC_CACHE)

        if self.layers_enum_config is None:  # pragma: no cover
            raise HTTPInternalServerError("Missing configuration")
        general_dbsession_name = self.layers_enum_config.get("dbsession", "dbsession")
        layername = self.request.matchdict["layer_name"]
        fieldname = self.request.matchdict["field_name"]
        # TODO check if layer is public or not

        return self._enumerate_attribute_values(
            general_dbsession_name, layername, fieldname
        )

    @cache_region.cache_on_arguments()
    def _enumerate_attribute_values(self, general_dbsession_name, layername, fieldname):
        if layername not in self.layers_enum_config:  # pragma: no cover
            raise HTTPBadRequest("Unknown layer: %s" % layername)

        layerinfos = self.layers_enum_config[layername]
        if fieldname not in layerinfos["attributes"]:  # pragma: no cover
            raise HTTPBadRequest("Unknown attribute: %s" % fieldname)
        dbsession = DBSessions.get(
            layerinfos.get("dbsession", general_dbsession_name), None
        )
        if dbsession is None:  # pragma: no cover
            raise HTTPInternalServerError(
                "No dbsession found for layer '%s'" % layername
            )

        layer_table = layerinfos.get("table", None)
        attrinfos = layerinfos["attributes"][fieldname]
        attrinfos = {} if attrinfos is None else attrinfos

        table = attrinfos.get("table", layer_table)
        if table is None:  # pragma: no cover
            raise HTTPInternalServerError(
                "No config table found for layer '%s'" % layername
            )
        layertable = get_table(table, session=dbsession)

        column = attrinfos["column_name"] \
            if "column_name" in attrinfos else fieldname
        attribute = getattr(layertable.columns, column)
        # For instance if `separator` is a "," we consider that the column contains a
        # comma separate list of values e.g.: "value1,value2".
        if "separator" in attrinfos:
            separator = attrinfos["separator"]
            attribute = func.unnest(func.string_to_array(
                func.string_agg(attribute, separator), separator
            ))
        values = dbsession.query(distinct(attribute)).order_by(attribute).all()
        enum = {
            "items": [{"label": value[0], "value": value[0]} for value in values]
        }

        return enum
