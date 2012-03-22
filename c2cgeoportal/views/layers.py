from pyramid.httpexceptions import (HTTPInternalServerError, HTTPNotFound,
                                    HTTPBadRequest)
from pyramid.view import view_config

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from geoalchemy import Geometry

from geojson.feature import FeatureCollection

from papyrus.renderers import XSD
from papyrus.protocol import Protocol

from c2cgeoportal.lib.dbreflection import get_class
from c2cgeoportal.models import DBSession, Layer

def _get_class(layer_id):
    """ Return an SQLAlchemy mapped class for the layer
    identified by ``layer_id``. """
    layer_id = int(layer_id)
    try:
        table_name, = DBSession.query(Layer.geoTable) \
                               .filter(Layer.id == layer_id) \
                               .one()
    except NoResultFound:
        raise HTTPNotFound("Layer not found")
    except MultipleResultsFound: # pragma: no cover
        raise HTTPInternalServerError() # pragma: no cover
    return get_class(str(table_name))


def _get_classes(request):
    """ A generator function that yields ``(layer_id, class)``
    tuples. """
    try:
        layer_ids = (int(layer_id) for layer_id in \
                         request.matchdict['layer_id'].split(',') if layer_id)
        for layer_id in layer_ids:
            yield (layer_id, _get_class(layer_id))
    except ValueError:
        raise HTTPBadRequest() # pragma: no cover


def _get_geom_attr(mapped_class):
    # This function assumes that the names of geometry attributes
    # in the mapped class are the same as those of geometry columns.
    for column in mapped_class.__table__.columns:
        if isinstance(column.type, Geometry):
            return column.name
    raise HTTPInternalServerError() # pragma: no cover


def _get_protocols(request):
    """ A generator function that yields ``(layer_id, protocol)``
    tuples. """
    for layer_id, cls in _get_classes(request):
        geom_attr = _get_geom_attr(cls)
        yield (layer_id, Protocol(DBSession, cls, geom_attr))


def _get_protocol(request):
    try:
        return next(p for _, p in _get_protocols(request))
    except StopIteration: # pragma: no cover
        raise HTTPInternalServerError() # pragma: no cover


@view_config(route_name='layers_read_many', renderer='geojson')
def read_many(request):
    features = []
    for layer_id, proto in _get_protocols(request):
        collection = proto.read(request)
        for feature in collection.features:
            feature.properties['__layer_id__'] = layer_id
            features.append(feature)
    return FeatureCollection(features)


@view_config(route_name='layers_read_one', renderer='geojson')
def read_one(request):
    feature_id = request.matchdict.get('feature_id', None)
    protocol = _get_protocol(request)
    return protocol.read(request, id=feature_id)


@view_config(route_name='layers_count', renderer='string')
def count(request):
    protocol = _get_protocol(request)
    return protocol.count(request)


@view_config(route_name='layers_create', renderer='geojson')
def create(request):
    protocol = _get_protocol(request)
    return protocol.create(request)


@view_config(route_name='layers_update', renderer='geojson')
def update(request):
    feature_id = request.matchdict.get('feature_id', None)
    protocol = _get_protocol(request)
    return protocol.update(request, feature_id)


@view_config(route_name='layers_delete')
def delete(request):
    feature_id = request.matchdict.get('feature_id', None)
    protocol = _get_protocol(request)
    return protocol.delete(request, feature_id)


@view_config(route_name='layers_metadata', renderer='xsd')
def metadata(request):
    mapped_class = _get_class(request.matchdict['layer_id'])
    return mapped_class.__table__
