# -*- coding: utf-8 -*-

from pyramid.httpexceptions import HTTPBadRequest, HTTPInternalServerError
from pyramid.view import view_config

from shapely.wkb import loads as wkb_loads
from geojson import Feature, FeatureCollection
from sqlalchemy import desc, or_, and_

from c2cgeoportal.models import DBSession, FullTextSearch


_language_dict = {
    'fr': 'french',
    'en': 'english',
    'de': 'german',
}


@view_config(route_name='fulltextsearch', renderer='geojson')
def fulltextsearch(request):

    try:
        lang = request.registry.settings['default_locale_name']
    except KeyError:
        return HTTPInternalServerError(
            detail='default_locale_name not defined in settings')
    try:
        lang = _language_dict[lang]
    except KeyError:
        return HTTPInternalServerError(
            detail='%s not defined in _language_dict' % lang)

    if 'query' not in request.params:
        return HTTPBadRequest(detail='no query')
    query = request.params.get('query')

    try:
        limit = int(request.params.get(
            'limit',
            request.registry.settings.get('fulltextsearch_defaultlimit', 30)))
        lang = request.registry.settings['default_locale_name']
    except ValueError:
        return HTTPBadRequest(detail='limit value is incorrect')
    maxlimit = request.registry.settings.get('fulltextsearch_maxlimit', 200)
    if limit > maxlimit:
        limit = maxlimit

    terms = '&'.join(w + ':*' for w in
                         query.split(' ') if w != '')
    ts_filter = "%(tsvector)s @@ to_tsquery('%(lang)s', '%(terms)s')" % \
        {'tsvector': 'ts', 'lang': lang, 'terms': terms}

    if request.user is None:
        user_filter = FullTextSearch.public == True
    else:
        user_filter = or_(FullTextSearch.public == True,
                          FullTextSearch.role_id == None,
                          FullTextSearch.role_id == request.user.role.id)

    # The numbers used in ts_rank_cd() below indicate a normalization method.
    # Several normalization methods can be combined using |.
    # 2 divides the rank by the document length
    # 8 divides the rank by the number of unique words in document
    # By combining them, shorter results seem to be preferred over longer ones
    # with the same ratio of matching words. But this relies only on testing it
    # and on some assumptions about how it might be calculated
    # (the normalization is applied two times with the combination of 2 and 8,
    # so the effect on at least the one-word-results is therefore stronger).
    rank = "ts_rank_cd(%(tsvector)s, to_tsquery('%(lang)s', '%(terms)s'), 2|8)" % \
        {'tsvector': 'ts', 'lang': lang, 'terms': terms}

    query = DBSession.query(FullTextSearch)
    query = query.filter(and_(ts_filter, user_filter))
    query = query.order_by(desc(rank))
    query = query.order_by(FullTextSearch.label)
    query = query.limit(limit)
    objs = query.all()

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
