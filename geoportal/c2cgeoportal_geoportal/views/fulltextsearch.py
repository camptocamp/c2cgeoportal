# -*- coding: utf-8 -*-

# Copyright (c) 2011-2018, Camptocamp SA
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

from geojson import Feature, FeatureCollection
from sqlalchemy import func, desc, or_, and_
from geoalchemy2.shape import to_shape
import re

from c2cgeoportal_geoportal import locale_negotiator
from c2cgeoportal_commons.models import DBSession
from c2cgeoportal_commons.models.main import FullTextSearch, Interface
from c2cgeoportal_geoportal.lib.caching import get_region, set_common_headers, NO_CACHE

cache_region = get_region()

IGNORED_CHARS_RE = re.compile(r"[()&|!:]")


class FullTextSearchView:

    def __init__(self, request):
        self.request = request
        set_common_headers(request, "fulltextsearch", NO_CACHE)
        self.settings = request.registry.settings.get("fulltextsearch", {})
        self.languages = self.settings.get("languages", {})

    @staticmethod
    @cache_region.cache_on_arguments()
    def _get_interface_id(interface):
        return DBSession.query(Interface).filter_by(name=interface).one().id

    @view_config(route_name="fulltextsearch", renderer="geojson")
    def fulltextsearch(self):
        lang = locale_negotiator(self.request)

        try:
            language = self.languages[lang]
        except KeyError:
            return HTTPInternalServerError(
                detail="{0!s} not defined in languages".format(lang))

        if "query" not in self.request.params:
            return HTTPBadRequest(detail="no query")
        terms = self.request.params.get("query")

        maxlimit = self.settings.get("maxlimit", 200)

        try:
            limit = int(self.request.params.get(
                "limit",
                self.settings.get("defaultlimit", 30)))
        except ValueError:
            return HTTPBadRequest(detail="limit value is incorrect")
        if limit > maxlimit:
            limit = maxlimit

        try:
            partitionlimit = int(self.request.params.get("partitionlimit", 0))
        except ValueError:
            return HTTPBadRequest(detail="partitionlimit value is incorrect")
        if partitionlimit > maxlimit:
            partitionlimit = maxlimit

        terms_ts = "&".join(w + ":*"
                            for w in IGNORED_CHARS_RE.sub(" ", terms).split(" ") if w != "")
        _filter = FullTextSearch.ts.op("@@")(func.to_tsquery(language, terms_ts))

        if self.request.user is None or self.request.user.role is None:
            _filter = and_(_filter, FullTextSearch.public.is_(True))
        else:
            _filter = and_(
                _filter,
                or_(
                    FullTextSearch.public.is_(True),
                    FullTextSearch.role_id.is_(None),
                    FullTextSearch.role_id == self.request.user.role.id
                )
            )

        if "interface" in self.request.params:
            _filter = and_(_filter, or_(
                FullTextSearch.interface_id.is_(None),
                FullTextSearch.interface_id == self._get_interface_id(
                    self.request.params["interface"]
                )
            ))
        else:
            _filter = and_(_filter, FullTextSearch.interface_id.is_(None))

        _filter = and_(_filter, or_(
            FullTextSearch.lang.is_(None),
            FullTextSearch.lang == lang,
        ))

        rank_system = self.request.params.get("ranksystem")
        if rank_system == "ts_rank_cd":
            # The numbers used in ts_rank_cd() below indicate a normalization method.
            # Several normalization methods can be combined using |.
            # 2 divides the rank by the document length
            # 8 divides the rank by the number of unique words in document
            # By combining them, shorter results seem to be preferred over longer ones
            # with the same ratio of matching words. But this relies only on testing it
            # and on some assumptions about how it might be calculated
            # (the normalization is applied two times with the combination of 2 and 8,
            # so the effect on at least the one-word-results is therefore stronger).
            rank = func.ts_rank_cd(FullTextSearch.ts, func.to_tsquery(language, terms_ts), 2 | 8)
        else:
            # Use similarity ranking system from module pg_trgm.
            rank = func.similarity(FullTextSearch.label, terms)

        if partitionlimit:
            # Here we want to partition the search results based on
            # layer_name and limit each partition.
            row_number = func.row_number().over(
                partition_by=FullTextSearch.layer_name,
                order_by=(desc(rank), FullTextSearch.label)
            ).label("row_number")
            subq = DBSession.query(FullTextSearch) \
                .add_columns(row_number).filter(_filter).subquery()
            query = DBSession.query(
                subq.c.id, subq.c.label, subq.c.params, subq.c.layer_name,
                subq.c.the_geom, subq.c.actions
            )
            query = query.filter(subq.c.row_number <= partitionlimit)
        else:
            query = DBSession.query(FullTextSearch).filter(_filter)
            query = query.order_by(desc(rank))
            query = query.order_by(FullTextSearch.label)

        query = query.limit(limit)
        objs = query.all()

        features = []
        for o in objs:
            properties = {
                "label": o.label,
            }
            if o.layer_name is not None:
                properties["layer_name"] = o.layer_name
            if o.params is not None:
                properties["params"] = o.params
            if o.actions is not None:
                properties["actions"] = o.actions
            if o.actions is None and o.layer_name is not None:
                properties["actions"] = [{
                    "action": "add_layer",
                    "data": o.layer_name,
                }]

            if o.the_geom is not None:
                geom = to_shape(o.the_geom)
                feature = Feature(
                    id=o.id, geometry=geom,
                    properties=properties, bbox=geom.bounds
                )
                features.append(feature)
            else:
                feature = Feature(
                    id=o.id, properties=properties
                )
                features.append(feature)

        # TODO: add callback function if provided in self.request, else return geojson
        return FeatureCollection(features)
