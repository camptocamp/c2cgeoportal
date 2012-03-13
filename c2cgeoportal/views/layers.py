from geoalchemy import Geometry
from pyramid.httpexceptions import HTTPInternalServerError, HTTPNotFound
from pyramid.view import view_config
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from papyrus.renderers import XSD
from papyrus.protocol import Protocol

from c2cgeoportal.lib.dbreflection import get_class
from c2cgeoportal.models import DBSession, Layer


def _get_class_for_request(request):
    layer_id = int(request.matchdict['layer_id'])
    try:
        table_name, = DBSession.query(Layer.geoTable).filter(Layer.id == layer_id).one()
    except NoResultFound:
        raise HTTPNotFound("Layer not found")
    except MultipleResultsFound: # pragma: no cover
        raise HTTPInternalServerError() # pragma: no cover
    return get_class(str(table_name))


def _get_geom_attr_for_mapped_class(mapped_class):
    # This function assumes that the names of geometry attributes
    # in the mapped class are the same as those of geometry columns.
    for column in mapped_class.__table__.columns:
        if isinstance(column.type, Geometry):
            return column.name
    raise HTTPInternalServerError() # pragma: no cover


def _get_protocol(request):
    mapped_class = _get_class_for_request(request)
    geom_attr = _get_geom_attr_for_mapped_class(mapped_class)
    return Protocol(DBSession, mapped_class, geom_attr)


@view_config(route_name='layers_read_many', renderer='geojson')
def read_many(request):
    protocol = _get_protocol(request)
    return protocol.read(request)


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
    mapped_class = _get_class_for_request(request)
    return mapped_class.__table__
