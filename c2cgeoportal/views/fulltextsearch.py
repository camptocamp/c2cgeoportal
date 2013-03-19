# -*- coding: utf-8 -*-

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


from pyramid.httpexceptions import HTTPBadRequest, HTTPInternalServerError
from pyramid.view import view_config

from shapely.wkb import loads as wkb_loads
from geojson import Feature, FeatureCollection
from sqlalchemy import func, desc, or_, and_

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

    maxlimit = request.registry.settings.get('fulltextsearch_maxlimit', 200)

    try:
        limit = int(request.params.get(
            'limit',
            request.registry.settings.get('fulltextsearch_defaultlimit', 30)))
    except ValueError:
        return HTTPBadRequest(detail='limit value is incorrect')
    if limit > maxlimit:
        limit = maxlimit

    try:
        partitionlimit = int(request.params.get('partitionlimit', 0))
    except ValueError:
        return HTTPBadRequest(detail='partitionlimit value is incorrect')
    if partitionlimit > maxlimit:
        partitionlimit = maxlimit

    terms = '&'.join(w + ':*' for w in query.split(' ') if w != '')
    _filter = "%(tsvector)s @@ to_tsquery('%(lang)s', '%(terms)s')" % \
        {'tsvector': 'ts', 'lang': lang, 'terms': terms}

    # flake8 does not like `== True`
    if request.user is None:
        _filter = and_(_filter, FullTextSearch.public == True)  # NOQA
    else:
        _filter = and_(
                _filter,
                or_(FullTextSearch.public == True,
                    FullTextSearch.role_id == None,
                    FullTextSearch.role_id == request.user.role.id))  # NOQA

    # The numbers used in ts_rank_cd() below indicate a normalization method.
    # Several normalization methods can be combined using |.
    # 2 divides the rank by the document length
    # 8 divides the rank by the number of unique words in document
    # By combining them, shorter results seem to be preferred over longer ones
    # with the same ratio of matching words. But this relies only on testing it
    # and on some assumptions about how it might be calculated
    # (the normalization is applied two times with the combination of 2 and 8,
    # so the effect on at least the one-word-results is therefore stronger).
    rank = "ts_rank_cd(%(tsvector)s, " \
        "to_tsquery('%(lang)s', '%(terms)s'), 2|8)" % {
            'tsvector': 'ts',
            'lang': lang,
            'terms': terms
        }

    if partitionlimit:
        # Here we want to partition the search results based on
        # layer_name and limit each partition.
        row_number = func.row_number() \
            .over(
                partition_by=FullTextSearch.layer_name,
                order_by=(desc(rank), FullTextSearch.label)) \
            .label('row_number')
        subq = DBSession.query(FullTextSearch) \
            .add_columns(row_number).filter(_filter).subquery()
        query = DBSession.query(subq.c.id, subq.c.label,
                                subq.c.layer_name, subq.c.the_geom)
        query = query.filter(subq.c.row_number <= partitionlimit)
    else:
        query = DBSession.query(FullTextSearch).filter(_filter)
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
