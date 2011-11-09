# -*- coding: utf-8 -*-

from pyramid.httpexceptions import HTTPBadRequest
from pyramid.view import view_config

from shapely.wkb import loads as wkb_loads
from geojson import Feature, FeatureCollection

from c2cgeoportal.models import DBSession, FullTextSearch

@view_config(route_name='fulltextsearch', renderer='geojson')
def fulltextsearch(request):

    if 'query' not in request.params:
        return HTTPBadRequest(detail='no query')
    query = request.params.get('query')

    try:
        limit = int(request.params.get('limit', '30'))
    except ValueError:
        return HTTPBadRequest(detail='limit value is incorrect')
    if limit > 30:
        limit = 30

    terms = '&'.join([w + ':*' for w in 
            query.split(' ') if w != ''])
    filter = "%(tsvector)s @@ to_tsquery('german', '%(terms)s')" % \
        {'tsvector': 'ts', 'terms': terms}

    objs = DBSession.query(FullTextSearch).filter(filter) \
               .order_by(FullTextSearch.label).limit(limit).all()

    features = []
    for o in objs:
        if o.the_geom is not None:
            properties = {"label": o.label, "layer_name": o.layer_name}
            geom = wkb_loads(str(o.the_geom.geom_wkb))
            feature = Feature(id=o.id, geometry=geom,
                              properties=properties, bbox=geom.bounds)
            features.append(feature)

    # TODO: add callback function if provided in request, else return geojson
    return FeatureCollection(features)
