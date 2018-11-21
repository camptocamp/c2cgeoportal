# -*- coding: utf-8 -*-

# Copyright (c) 2012-2018, Camptocamp SA
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

from datetime import datetime

from pyramid.httpexceptions import HTTPInternalServerError, \
    HTTPNotFound, HTTPBadRequest, HTTPForbidden
from pyramid.view import view_config

from sqlalchemy import Enum, exc, func, distinct, Numeric, String, Text, Unicode, UnicodeText
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
from papyrus.xsd import XSDGenerator

from c2cgeoportal_commons import models
from c2cgeoportal_commons.models.main import Layer, RestrictionArea, Role
from c2cgeoportal_geoportal.lib.caching import get_region, \
    set_common_headers, NO_CACHE, PUBLIC_CACHE, PRIVATE_CACHE
from c2cgeoportal_geoportal.lib.dbreflection import get_class, get_table, _AssociationProxy

import logging
log = logging.getLogger(__name__)

cache_region = get_region()


class Layers:

    def __init__(self, request):
        self.request = request
        self.settings = request.registry.settings.get("layers", {})
        self.layers_enum_config = self.settings.get("enum")

    @staticmethod
    def _get_geom_col_info(layer):
        """ Return information about the layer's geometry column, namely
        a ``(name, srid)`` tuple, where ``name`` is the name of the
        geometry column, and ``srid`` its srid.

        This function assumes that the names of geometry attributes
        in the mapped class are the same as those of geometry columns.
        """
        mapped_class = get_layer_class(layer)
        for p in class_mapper(mapped_class).iterate_properties:
            if not isinstance(p, ColumnProperty):
                continue  # pragma: no cover
            col = p.columns[0]
            if isinstance(col.type, Geometry):
                return col.name, col.type.srid
        raise HTTPInternalServerError(
            'Failed getting geometry column info for table "{0!s}".'.format(
                layer.geo_table
            )
        )  # pragma: no cover

    @staticmethod
    def _get_layer(layer_id):
        """ Return a ``Layer`` object for ``layer_id``. """
        layer_id = int(layer_id)
        try:
            query = models.DBSession.query(Layer, Layer.geo_table)
            query = query.filter(Layer.id == layer_id)
            layer, geo_table = query.one()
        except NoResultFound:
            raise HTTPNotFound("Layer {0:d} not found".format(layer_id))
        except MultipleResultsFound:  # pragma: no cover
            raise HTTPInternalServerError(
                "Too many layers found with id {0:d}".format(layer_id)
            )
        if not geo_table:  # pragma: no cover
            raise HTTPNotFound("Layer {0:d} has no geo table".format(layer_id))
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
                "A Layer id in '{0!s}' is not an integer".format(
                    self.request.matchdict["layer_id"]
                )
            )  # pragma: no cover

    def _get_layer_for_request(self):
        """ Return a ``Layer`` object for the first layer id found
        in the ``layer_id`` matchdict. """
        return next(self._get_layers_for_request())

    def _get_protocol_for_layer(self, layer, **kwargs):
        """ Returns a papyrus ``Protocol`` for the ``Layer`` object. """
        cls = get_layer_class(layer)
        geom_attr = self._get_geom_col_info(layer)[0]
        return Protocol(models.DBSession, cls, geom_attr, **kwargs)

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
        ras = models.DBSession.query(RestrictionArea.area, RestrictionArea.area.ST_SRID())
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
        feature_id = self.request.matchdict.get("feature_id")
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
        allowed = models.DBSession.query(func.count(RestrictionArea.id))
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

        def check_geometry(_, feature, obj):
            del obj  # unused
            geom = feature.geometry
            if geom and not isinstance(geom, geojson.geometry.Default):
                shape = asShape(geom)
                srid = self._get_geom_col_info(layer)[1]
                spatial_elt = from_shape(shape, srid=srid)
                allowed = models.DBSession.query(func.count(RestrictionArea.id))
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
                if self._get_validation_setting(layer):
                    self._validate_geometry(spatial_elt)

        protocol = self._get_protocol_for_layer(layer, before_create=check_geometry)
        try:
            features = protocol.create(self.request)
            for feature in features.features:
                self._log_last_update(layer, feature)
            return features
        except TopologicalError as e:
            self.request.response.status_int = 400
            return {"error_type": "validation_error",
                    "message": str(e)}
        except exc.IntegrityError as e:
            log.error(str(e))
            self.request.response.status_int = 400
            return {"error_type": "integrity_error",
                    "message": str(e.orig.diag.message_primary)}

    @view_config(route_name="layers_update", renderer="geojson")
    def update(self):
        set_common_headers(self.request, "layers", NO_CACHE)

        if self.request.user is None:
            raise HTTPForbidden()

        self.request.response.cache_control.no_cache = True

        feature_id = self.request.matchdict.get("feature_id")
        layer = self._get_layer_for_request()

        def check_geometry(_, feature, obj):
            # we need both the "original" and "new" geometry to be
            # within the restriction area
            geom_attr, srid = self._get_geom_col_info(layer)
            geom_attr = getattr(obj, geom_attr)
            geom = feature.geometry
            allowed = models.DBSession.query(func.count(RestrictionArea.id))
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
            if self._get_validation_setting(layer):
                self._validate_geometry(spatial_elt)

        protocol = self._get_protocol_for_layer(layer, before_update=check_geometry)
        try:
            feature = protocol.update(self.request, feature_id)
            self._log_last_update(layer, feature)
            return feature
        except TopologicalError as e:
            self.request.response.status_int = 400
            return {"error_type": "validation_error",
                    "message": str(e)}
        except exc.IntegrityError as e:
            log.error(str(e))
            self.request.response.status_int = 400
            return {"error_type": "integrity_error",
                    "message": str(e.orig.diag.message_primary)}

    @staticmethod
    def _validate_geometry(geom):
        if geom is not None:
            simple = models.DBSession.query(func.ST_IsSimple(geom)).scalar()
            if not simple:
                raise TopologicalError("Not simple")
            valid = models.DBSession.query(func.ST_IsValid(geom)).scalar()
            if not valid:
                reason = models.DBSession.query(func.ST_IsValidReason(geom)).scalar()
                raise TopologicalError(reason)

    def _log_last_update(self, layer, feature):
        last_update_date = self.get_metadata(layer, "lastUpdateDateColumn")
        if last_update_date is not None:
            setattr(feature, last_update_date, datetime.now())

        last_update_user = self.get_metadata(layer, "lastUpdateUserColumn")
        if last_update_user is not None:
            setattr(feature, last_update_user, self.request.user.id)

    @staticmethod
    def get_metadata(layer, key, default=None):
        metadatas = layer.get_metadatas(key)
        if len(metadatas) == 1:
            metadata = metadatas[0]
            return metadata.value
        return default

    def _get_validation_setting(self, layer):
        # The validation UIMetadata is stored as a string, not a boolean
        should_validate = self.get_metadata(layer, "geometryValidation", None)
        if should_validate:
            return should_validate.lower() != "false"
        return self.settings.get("geometry_validation", False)

    @view_config(route_name="layers_delete")
    def delete(self):
        if self.request.user is None:
            raise HTTPForbidden()

        feature_id = self.request.matchdict.get("feature_id")
        layer = self._get_layer_for_request()

        def security_cb(_, obj):
            geom_attr = getattr(obj, self._get_geom_col_info(layer)[0])
            allowed = models.DBSession.query(func.count(RestrictionArea.id))
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
        response = protocol.delete(self.request, feature_id)
        set_common_headers(
            self.request, "layers", NO_CACHE,
            response=response,
        )
        return response

    @view_config(route_name="layers_metadata", renderer="xsd")
    def metadata(self):
        set_common_headers(self.request, "layers", PRIVATE_CACHE)

        layer = self._get_layer_for_request()
        if not layer.public and self.request.user is None:
            raise HTTPForbidden()

        return get_layer_class(layer, with_exclude=True)

    @view_config(route_name="layers_enumerate_attribute_values", renderer="json")
    def enumerate_attribute_values(self):
        set_common_headers(self.request, "layers", PUBLIC_CACHE)

        if self.layers_enum_config is None:  # pragma: no cover
            raise HTTPInternalServerError("Missing configuration")
        layername = self.request.matchdict["layer_name"]
        fieldname = self.request.matchdict["field_name"]
        # TODO check if layer is public or not

        return self._enumerate_attribute_values(
            layername, fieldname
        )

    @cache_region.cache_on_arguments()
    def _enumerate_attribute_values(self, layername, fieldname):
        if layername not in self.layers_enum_config:  # pragma: no cover
            raise HTTPBadRequest("Unknown layer: {0!s}".format(layername))

        layerinfos = self.layers_enum_config[layername]
        if fieldname not in layerinfos["attributes"]:  # pragma: no cover
            raise HTTPBadRequest("Unknown attribute: {0!s}".format(fieldname))
        dbsession_name = layerinfos.get("dbsession", "dbsession")
        dbsession = models.DBSessions.get(dbsession_name)
        if dbsession is None:  # pragma: no cover
            raise HTTPInternalServerError(
                "No dbsession found for layer '{0!s}' ({1!s})".format(layername, dbsession_name)
            )
        values = self.query_enumerate_attribute_values(dbsession, layerinfos, fieldname)
        enum = {
            "items": [{"label": value[0], "value": value[0]} for value in values]
        }
        return enum

    @staticmethod
    def query_enumerate_attribute_values(dbsession, layerinfos, fieldname):
        attrinfos = layerinfos["attributes"][fieldname]
        table = attrinfos["table"]
        layertable = get_table(table, session=dbsession)
        column = attrinfos.get("column_name", fieldname)
        attribute = getattr(layertable.columns, column)
        # For instance if `separator` is a "," we consider that the column contains a
        # comma separate list of values e.g.: "value1,value2".
        if "separator" in attrinfos:
            separator = attrinfos["separator"]
            attribute = func.unnest(func.string_to_array(
                func.string_agg(attribute, separator), separator
            ))
        return dbsession.query(distinct(attribute)).order_by(attribute).all()


def get_layer_class(layer, with_exclude=False):
    if with_exclude:
        # Exclude the columns used to record the last features update
        exclude = [] if layer.exclude_properties is None else layer.exclude_properties.split(",")
        last_update_date = Layers.get_metadata(layer, "lastUpdateDateColumn")
        if last_update_date is not None:
            exclude.append(last_update_date)
        last_update_user = Layers.get_metadata(layer, "lastUpdateUserColumn")
        if last_update_user is not None:
            exclude.append(last_update_user)
    else:
        exclude = []

    primary_key = Layers.get_metadata(layer, "geotablePrimaryKey")
    return get_class(
        str(layer.geo_table),
        exclude_properties=exclude,
        primary_key=primary_key
    )


def get_layer_metadatas(layer):
    cls = get_layer_class(layer, with_exclude=True)
    edit_columns = []

    for column_property in class_mapper(cls).iterate_properties:
        if isinstance(column_property, ColumnProperty):

            if len(column_property.columns) != 1:
                raise NotImplementedError  # pragma: no cover

            column = column_property.columns[0]

            # Exclude columns that are primary keys
            if not column.primary_key:
                properties = _convert_column_type(column.type)
                properties["name"] = column.key

                if column.nullable:
                    properties["nillable"] = True
                edit_columns.append(properties)
        else:
            for k, p in cls.__dict__.items():
                if not isinstance(p, _AssociationProxy):
                    continue

                relationship_property = class_mapper(cls) \
                    .get_property(p.target)
                target_cls = relationship_property.argument
                query = models.DBSession.query(getattr(target_cls, p.value_attr))
                properties = {}
                if column.nullable:
                    properties["nillable"] = True

                properties["name"] = k
                properties["restriction"] = "enumeration"
                properties["type"] = "xsd:string"
                properties["enumeration"] = []
                for value in query:
                    properties["enumeration"].append(value[0])

                edit_columns.append(properties)
    return edit_columns


def _convert_column_type(column_type):
    # SIMPLE_XSD_TYPES
    for cls, xsd_type in XSDGenerator.SIMPLE_XSD_TYPES.items():
        if isinstance(column_type, cls):
            return {"type": xsd_type}

    # Geometry type
    if isinstance(column_type, Geometry):
        geometry_type = column_type.geometry_type
        if geometry_type in XSDGenerator.SIMPLE_GEOMETRY_XSD_TYPES:
            xsd_type = XSDGenerator.SIMPLE_GEOMETRY_XSD_TYPES[geometry_type]
            return {"type": xsd_type, "srid": int(column_type.srid)}
        if geometry_type == "GEOMETRY":
            xsd_type = "gml:GeometryPropertyType"
            return {"type": xsd_type, "srid": int(column_type.srid)}

        raise NotImplementedError  # pragma: no cover

    # Enumeration type
    if isinstance(column_type, Enum):
        restriction = {}
        restriction["restriction"] = "enumeration"
        restriction["type"] = "xsd:string"
        restriction["enumeration"] = []
        for enum in column_type.enums:
            restriction["enumeration"].append(enum)
        return restriction

    # String type
    if isinstance(column_type, (String, Text, Unicode, UnicodeText)):
        if column_type.length is None:
            return {"type": "xsd:string"}
        else:
            return {"type": "xsd:string", "maxLength": int(column_type.length)}

    # Numeric Type
    if isinstance(column_type, Numeric):
        xsd_type = {"type": "xsd:decimal"}
        if column_type.scale is None and column_type.precision is None:
            return xsd_type

        else:
            if column_type.scale is not None:
                xsd_type["fractionDigits"] = int(column_type.scale)
            if column_type.precision is not None:
                xsd_type["totalDigits"] = int(column_type.precision)
            return xsd_type

    raise NotImplementedError  # pragma: no cover
