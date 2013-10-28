# Copyright (c) 2013, Camptocamp SA
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

from pyramid.httpexceptions import (HTTPInternalServerError, HTTPNotFound,
                                    HTTPBadRequest, HTTPForbidden)
from pyramid.view import view_config

from sqlalchemy import func, distinct
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.sql import and_, or_
from sqlalchemy.orm.util import class_mapper
from sqlalchemy.orm.properties import ColumnProperty

from geoalchemy import Geometry, WKBSpatialElement, functions

import geojson
from geojson.feature import FeatureCollection, Feature

from shapely import wkb
from shapely.geometry import asShape
from shapely.ops import cascaded_union

from papyrus.protocol import Protocol, create_filter

from c2cgeoportal.lib.dbreflection import get_class, get_table
from c2cgeoportal.models import DBSessions, DBSession, Layer, RestrictionArea, Role


def _get_geom_col_info(layer):
    """ Return information about the layer's geometry column, namely
    a ``(name, srid)`` tuple, where ``name`` is the name of the
    geometry column, and ``srid`` its srid.

    This function assumes that the names of geometry attributes
    in the mapped class are the same as those of geometry columns.
    """
    mapped_class = get_class(str(layer.geoTable))
    for p in class_mapper(mapped_class).iterate_properties:
        if not isinstance(p, ColumnProperty):
            continue  # pragma: no cover
        col = p.columns[0]
        if isinstance(col.type, Geometry):
            return col.name, col.type.srid
    raise HTTPInternalServerError(
        'Failed getting geometry column info for table "%s".' %
        str(layer.geoTable)
    )  # pragma: no cover


def _get_layer(layer_id):
    """ Return a ``Layer`` object for ``layer_id``. """
    layer_id = int(layer_id)
    try:
        query = DBSession.query(Layer, Layer.geoTable)
        query = query.filter(Layer.id == layer_id)
        layer, geo_table = query.one()
    except NoResultFound:
        raise HTTPNotFound("Layer %d not found" % layer_id)
    except MultipleResultsFound:  # pragma: no cover
        raise HTTPInternalServerError(
            'Too many layers found with id %i' % layer_id
        )
    if not geo_table:  # pragma: no cover
        raise HTTPNotFound("Layer %d has no geo table" % layer_id)
    return layer


def _get_layers_for_request(request):
    """ A generator function that yields ``Layer`` objects based
    on the layer ids found in the ``layer_id`` matchdict. """
    try:
        layer_ids = (
            int(layer_id) for layer_id in
            request.matchdict['layer_id'].split(',') if layer_id)
        for layer_id in layer_ids:
            yield _get_layer(layer_id)
    except ValueError:
        raise HTTPBadRequest(
            'A Layer id in "%s" is not an integer' %
            request.matchdict['layer_id']
        )  # pragma: no cover


def _get_layer_for_request(request):
    """ Return a ``Layer`` object for the first layer id found
    in the ``layer_id`` matchdict. """
    return next(_get_layers_for_request(request))


def _get_protocol_for_layer(layer, **kwargs):
    """ Returns a papyrus ``Protocol`` for the ``Layer`` object. """
    cls = get_class(str(layer.geoTable))
    geom_attr = _get_geom_col_info(layer)[0]
    return Protocol(DBSession, cls, geom_attr, **kwargs)


def _get_protocol_for_request(request, **kwargs):
    """ Returns a papyrus ``Protocol`` for the first layer
    id found in the ``layer_id`` matchdict. """
    layer = _get_layer_for_request(request)
    return _get_protocol_for_layer(layer, **kwargs)


def _proto_read(layer, request):
    """ Read features for the layer based on the request. """
    proto = _get_protocol_for_layer(layer)
    if layer.public:
        return proto.read(request)
    user = request.user
    if user is None:
        raise HTTPForbidden()
    cls = proto.mapped_class
    geom_attr = proto.geom_attr
    ras = DBSession.query(RestrictionArea.area, functions.srid(RestrictionArea.area))
    ras = ras.join(RestrictionArea.roles)
    ras = ras.join(RestrictionArea.layers)
    ras = ras.filter(Role.id == user.role.id)
    ras = ras.filter(Layer.id == layer.id)
    collect_ra = []
    use_srid = -1
    for ra, srid in ras.all():
        if ra is None:
            return proto.read(request)
        else:
            use_srid = srid
            collect_ra.append(wkb.loads(str(ra.geom_wkb)))
    if len(collect_ra) == 0:  # pragma: no cover
        raise HTTPForbidden()

    ra = cascaded_union(collect_ra)
    filter_ = and_(
        create_filter(request, cls, geom_attr),
        functions.gcontains(
            func.st_geomfromtext(ra.wkt, use_srid),
            getattr(cls, geom_attr)
        )
    )

    return proto.read(request, filter=filter_)


@view_config(route_name='layers_read_many', renderer='geojson')
def read_many(request):
    features = []
    for layer in _get_layers_for_request(request):
        for f in _proto_read(layer, request).features:
            f.properties['__layer_id__'] = layer.id
            features.append(f)
    return FeatureCollection(features)


@view_config(route_name='layers_read_one', renderer='geojson')
def read_one(request):
    layer = _get_layer_for_request(request)
    protocol = _get_protocol_for_layer(layer)
    feature_id = request.matchdict.get('feature_id', None)
    feature = protocol.read(request, id=feature_id)
    if not isinstance(feature, Feature):
        return feature
    if layer.public:
        return feature
    if request.user is None:
        raise HTTPForbidden()
    geom = feature.geometry
    if not geom or isinstance(geom, geojson.geometry.Default):  # pragma: no cover
        return feature
    shape = asShape(geom)
    srid = _get_geom_col_info(layer)[1]
    spatial_elt = WKBSpatialElement(buffer(shape.wkb), srid=srid)
    none = None  # the only way I found to remove the pep8 warning
    allowed = DBSession.query(func.count(RestrictionArea.id))
    allowed = allowed.join(RestrictionArea.roles)
    allowed = allowed.join(RestrictionArea.layers)
    allowed = allowed.filter(Role.id == request.user.role.id)
    allowed = allowed.filter(Layer.id == layer.id)
    allowed = allowed.filter(or_(
        RestrictionArea.area == none,
        RestrictionArea.area.gcontains(spatial_elt)
    ))
    if allowed.scalar() == 0:
        raise HTTPForbidden()
    return feature


@view_config(route_name='layers_count', renderer='string')
def count(request):
    protocol = _get_protocol_for_request(request)
    return protocol.count(request)


@view_config(route_name='layers_create', renderer='geojson')
def create(request):
    if request.user is None:
        raise HTTPForbidden()
    layer = _get_layer_for_request(request)

    def security_cb(r, feature, o):
        geom = feature.geometry
        if geom and not isinstance(geom, geojson.geometry.Default):
            shape = asShape(geom)
            srid = _get_geom_col_info(layer)[1]
            spatial_elt = WKBSpatialElement(buffer(shape.wkb), srid=srid)
            none = None  # the only way I found to remove the pep8 warning
            allowed = DBSession.query(func.count(RestrictionArea.id))
            allowed = allowed.join(RestrictionArea.roles)
            allowed = allowed.join(RestrictionArea.layers)
            allowed = allowed.filter(RestrictionArea.readwrite == True)
            allowed = allowed.filter(Role.id == request.user.role.id)
            allowed = allowed.filter(Layer.id == layer.id)
            allowed = allowed.filter(or_(
                RestrictionArea.area == none,
                RestrictionArea.area.gcontains(spatial_elt)
            ))
            if allowed.scalar() == 0:
                raise HTTPForbidden()

    protocol = _get_protocol_for_layer(layer, before_create=security_cb)
    return protocol.create(request)


@view_config(route_name='layers_update', renderer='geojson')
def update(request):
    if request.user is None:
        raise HTTPForbidden()
    feature_id = request.matchdict.get('feature_id', None)
    layer = _get_layer_for_request(request)

    def security_cb(r, feature, o):
        # we need both the "original" and "new" geometry to be
        # within the restriction area
        geom_attr, srid = _get_geom_col_info(layer)
        geom_attr = getattr(o, geom_attr)
        geom = feature.geometry
        allowed = DBSession.query(func.count(RestrictionArea.id))
        allowed = allowed.join(RestrictionArea.roles)
        allowed = allowed.join(RestrictionArea.layers)
        allowed = allowed.filter(RestrictionArea.readwrite == True)
        allowed = allowed.filter(Role.id == request.user.role.id)
        allowed = allowed.filter(Layer.id == layer.id)
        none = None  # the only way I found to remove the pep8 warning
        allowed = allowed.filter(or_(
            RestrictionArea.area == none,
            RestrictionArea.area.gcontains(geom_attr)
        ))
        if geom and not isinstance(geom, geojson.geometry.Default):
            shape = asShape(geom)
            spatial_elt = WKBSpatialElement(buffer(shape.wkb), srid=srid)
            allowed = allowed.filter(or_(
                RestrictionArea.area == none,
                RestrictionArea.area.gcontains(spatial_elt)
            ))
        if allowed.scalar() == 0:
            raise HTTPForbidden()

    protocol = _get_protocol_for_layer(layer, before_update=security_cb)
    return protocol.update(request, feature_id)


@view_config(route_name='layers_delete')
def delete(request):
    if request.user is None:
        raise HTTPForbidden()
    feature_id = request.matchdict.get('feature_id', None)
    layer = _get_layer_for_request(request)

    def security_cb(r, o):
        geom_attr = getattr(o, _get_geom_col_info(layer)[0])
        none = None  # the only way I found to remove the pep8 warning
        allowed = DBSession.query(func.count(RestrictionArea.id))
        allowed = allowed.join(RestrictionArea.roles)
        allowed = allowed.join(RestrictionArea.layers)
        allowed = allowed.filter(RestrictionArea.readwrite == True)
        allowed = allowed.filter(Role.id == request.user.role.id)
        allowed = allowed.filter(Layer.id == layer.id)
        allowed = allowed.filter(or_(
            RestrictionArea.area == none,
            RestrictionArea.area.gcontains(geom_attr)
        ))
        if allowed.scalar() == 0:
            raise HTTPForbidden()

    protocol = _get_protocol_for_layer(layer, before_delete=security_cb)
    return protocol.delete(request, feature_id)


@view_config(route_name='layers_metadata', renderer='xsd')
def metadata(request):
    layer = _get_layer_for_request(request)
    if not layer.public and request.user is None:
        raise HTTPForbidden()
    return get_class(str(layer.geoTable))


@view_config(route_name='layers_enumerate_attribute_values', renderer='json')
def enumerate_attribute_values(request):
    config = request.registry.settings.get('layers_enum', None)
    if config is None:
        raise HTTPInternalServerError('Missing configuration')
    general_dbsession_name = config.get('dbsession', 'dbsession')
    layername = request.matchdict['layer_name']
    fieldname = request.matchdict['field_name']
    # TODO check if layer is public or not

    if layername not in config:
        raise HTTPBadRequest('Unknown layer: %s' % layername)

    layerinfos = config[layername]
    if fieldname not in layerinfos['attributes']:
        raise HTTPBadRequest('Unknown attribute: %s' % fieldname)
    dbsession = DBSessions.get(
        layerinfos.get('dbsession', general_dbsession_name), None
    )
    if dbsession is None:
        raise HTTPInternalServerError(
            'No dbsession found for layer "%s"' % layername
        )

    layer_table = layerinfos.get('table', None)
    attrinfos = layerinfos['attributes'][fieldname]
    attrinfos = {} if attrinfos is None else attrinfos

    table = attrinfos.get('table', layer_table)
    if table is None:
        raise HTTPInternalServerError(
            'No config table found for layer "%s"' % layername
        )
    layertable = get_table(table, DBSession=dbsession)

    column = attrinfos['column_name'] \
        if 'column_name' in attrinfos else fieldname
    values = dbsession.query(distinct(getattr(
        layertable.columns, column
    ))).all()
    enum = {
        'items': [{'label': value[0], 'value': value[0]} for value in values]
    }
    return enum
