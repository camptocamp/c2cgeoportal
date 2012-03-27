from pyramid.httpexceptions import (HTTPInternalServerError, HTTPNotFound,
                                    HTTPBadRequest)
from pyramid.view import view_config
from pyramid.security import authenticated_userid

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.sql import and_

from geoalchemy import functions, Geometry, DBSpatialElement

from geojson.feature import FeatureCollection

from papyrus.renderers import XSD
from papyrus.protocol import Protocol, create_filter

from c2cgeoportal.lib.dbreflection import get_class
from c2cgeoportal.models import (DBSession, Layer, RestrictionArea,
                                 User, Role)


def _get_geom_attr(mapped_class):
    # This function assumes that the names of geometry attributes
    # in the mapped class are the same as those of geometry columns.
    for column in mapped_class.__table__.columns:
        if isinstance(column.type, Geometry):
            return column.name
    raise HTTPInternalServerError()  # pragma: no cover


def _get_layer(layer_id):
    """ Return a ``Layer`` object for ``layer_id``. """
    layer_id = int(layer_id)
    try:
        layer, geo_table = DBSession.query(Layer, Layer.geoTable) \
                                    .filter(Layer.id == layer_id) \
                                    .one()
    except NoResultFound:
        raise HTTPNotFound("Layer %d not found" % layer_id)
    except MultipleResultsFound:  # pragma: no cover
        raise HTTPInternalServerError()  # pragma: no cover
    if not geo_table:
        raise HTTPNotFound("Layer %d has no geo table" % layer_id)
    return layer


def _get_layers_for_request(request):
    """ A generator function that yields ``Layer`` objects based
    on the layer ids found in the ``layer_id`` matchdict. """
    try:
        layer_ids = (int(layer_id) for layer_id in \
                         request.matchdict['layer_id'].split(',') if layer_id)
        for layer_id in layer_ids:
            yield _get_layer(layer_id)
    except ValueError:
        raise HTTPBadRequest()  # pragma: no cover


def _get_protocol_for_layer(layer):
    """ Returns a papyrus ``Protocol`` for the ``Layer`` object. """
    cls = get_class(str(layer.geoTable))
    return Protocol(DBSession, cls, _get_geom_attr(cls))


def _get_protocol_for_request(request):
    """ Returns a papyrus ``Protocol`` for the first layer
    found in the ``layer_id`` matchdict. """
    layer = next(_get_layers_for_request(request))
    return _get_protocol_for_layer(layer)


def _get_class_for_request(request):
    """ Return an SQLAlchemy mapped class for the first
    found in the ``layer_id`` matchdict. """
    layer = next(_get_layers_for_request(request))
    return get_class(str(layer.geoTable))


def _proto_read(layer, request):
    """ Read features for the layer based on the request. """
    if layer.public:
        return _get_protocol_for_layer(layer).read(request)
    if request.user is None:
        return FeatureCollection([])
    user = request.user
    proto = _get_protocol_for_layer(layer)
    cls = proto.mapped_class
    geom_attr = _get_geom_attr(cls)
    polygon = DBSession.query(
                           RestrictionArea.area.collect) \
                       .join(RestrictionArea.roles) \
                       .join(RestrictionArea.layers) \
                       .filter(RestrictionArea.area.area > 0) \
                       .filter(Role.id == user.role.id) \
                       .filter(Layer.id == layer.id).scalar()
    polygon = DBSpatialElement(polygon)
    filter_ = and_(create_filter(request, cls, geom_attr),
                   polygon.gcontains(getattr(cls, geom_attr))
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
    feature_id = request.matchdict.get('feature_id', None)
    protocol = _get_protocol_for_request(request)
    return protocol.read(request, id=feature_id)


@view_config(route_name='layers_count', renderer='string')
def count(request):
    protocol = _get_protocol_for_request(request)
    return protocol.count(request)


@view_config(route_name='layers_create', renderer='geojson')
def create(request):
    protocol = _get_protocol_for_request(request)
    return protocol.create(request)


@view_config(route_name='layers_update', renderer='geojson')
def update(request):
    feature_id = request.matchdict.get('feature_id', None)
    protocol = _get_protocol_for_request(request)
    return protocol.update(request, feature_id)


@view_config(route_name='layers_delete')
def delete(request):
    feature_id = request.matchdict.get('feature_id', None)
    protocol = _get_protocol_for_request(request)
    return protocol.delete(request, feature_id)


@view_config(route_name='layers_metadata', renderer='xsd')
def metadata(request):
    mapped_class = _get_class_for_request(request)
    return mapped_class.__table__
