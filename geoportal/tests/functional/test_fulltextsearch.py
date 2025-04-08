# Copyright (c) 2013-2025, Camptocamp SA
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

# pylint: disable=missing-docstring,attribute-defined-outside-init,protected-access


from unittest import TestCase

import webob.acceptparse
from pyramid import testing
from pyramid.response import Response

from tests.functional import create_dummy_request
from tests.functional import setup_common as setup_module  # noqa
from tests.functional import teardown_common as teardown_module  # noqa


class TestFulltextsearchView(TestCase):
    def setup_method(self, _) -> None:
        import transaction
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import FullTextSearch, Interface, Role
        from c2cgeoportal_commons.models.static import User
        from geoalchemy2 import WKTElement
        from sqlalchemy import func

        role1 = Role(name="__test_role1", description="__test_role1")
        user1 = User(username="__test_user1", password="__test_user1", settings_role=role1, roles=[role1])

        role2 = Role(name="__test_role2", description="__test_role2")
        user2 = User(username="__test_user2", password="__test_user2", settings_role=role2, roles=[role2])

        entry1 = FullTextSearch()
        entry1.label = "label1"
        entry1.layer_name = "layer1"
        entry1.ts = func.to_tsvector("french", "soleil travail")
        entry1.the_geom = WKTElement("POINT(-90 -45)", 21781)
        entry1.public = True

        entry2 = FullTextSearch()
        entry2.label = "label2"
        entry2.layer_name = "layer2"
        entry2.ts = func.to_tsvector("french", "pluie semaine")
        entry2.the_geom = WKTElement("POINT(-90 -45)", 21781)
        entry2.public = False

        entry3 = FullTextSearch()
        entry3.label = "label3"
        entry3.layer_name = "layer3"
        entry3.ts = func.to_tsvector("french", "vent neige")
        entry3.the_geom = WKTElement("POINT(-90 -45)", 21781)
        entry3.public = False
        entry3.role = role2

        entry4 = FullTextSearch()
        entry4.label = "label4"
        entry4.layer_name = "layer1"
        entry4.ts = func.to_tsvector("french", "soleil travail")
        entry4.the_geom = WKTElement("POINT(-90 -45)", 21781)
        entry4.public = True

        entry5 = FullTextSearch()
        entry5.label = "label5"
        entry5.ts = func.to_tsvector("french", "lausanne")
        entry5.public = True
        entry5.params = {"floor": 5}
        entry5.actions = [{"action": "add_layer", "data": "layer1"}]

        entry6 = FullTextSearch()
        entry6.label = "label6"
        entry6.ts = func.to_tsvector("french", "lausanne")
        entry6.interface = Interface("main")
        entry6.public = True

        # To test the similarity ranking method
        entry7 = FullTextSearch()
        entry7.label = "A 7 simi"
        entry7.ts = func.to_tsvector("french", "A 7 simi")
        entry7.public = True

        entry70 = FullTextSearch()
        entry70.label = "A 70 simi"
        entry70.ts = func.to_tsvector("french", "A 70 simi")
        entry70.public = True

        entry71 = FullTextSearch()
        entry71.label = "A 71 simi"
        entry71.ts = func.to_tsvector("french", "A 71 simi")
        entry71.public = True

        DBSession.add_all(
            [
                user1,
                user2,
                role1,
                role2,
                entry1,
                entry2,
                entry3,
                entry4,
                entry5,
                entry6,
                entry71,
                entry70,
                entry7,
            ],
        )
        transaction.commit()

    def teardown_method(self, _) -> None:
        testing.tearDown()

        import transaction
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import FullTextSearch, Interface, Role
        from c2cgeoportal_commons.models.static import User

        DBSession.delete(DBSession.query(User).filter(User.username == "__test_user1").one())
        DBSession.delete(DBSession.query(User).filter(User.username == "__test_user2").one())

        DBSession.query(FullTextSearch).filter(FullTextSearch.label == "label1").delete()
        DBSession.query(FullTextSearch).filter(FullTextSearch.label == "label2").delete()
        DBSession.query(FullTextSearch).filter(FullTextSearch.label == "label3").delete()
        DBSession.query(FullTextSearch).filter(FullTextSearch.label == "label4").delete()
        DBSession.query(FullTextSearch).filter(FullTextSearch.label == "label5").delete()
        DBSession.query(FullTextSearch).filter(FullTextSearch.label == "label6").delete()
        DBSession.query(FullTextSearch).filter(FullTextSearch.label == "A 7 simi").delete()
        DBSession.query(FullTextSearch).filter(FullTextSearch.label == "A 70 simi").delete()
        DBSession.query(FullTextSearch).filter(FullTextSearch.label == "A 71 simi").delete()

        DBSession.query(Interface).filter(Interface.name == "main").delete()

        DBSession.query(Role).filter(Role.name == "__test_role1").delete()
        DBSession.query(Role).filter(Role.name == "__test_role2").delete()

        transaction.commit()

    @staticmethod
    def _create_dummy_request(username=None, params=None):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User

        request = create_dummy_request(
            {"fulltextsearch": {"languages": {"fr": "french", "en": "english", "de": "german"}}},
            params=params,
        )
        request.response = Response()
        request.user = None
        if username:
            request.user = DBSession.query(User).filter_by(username=username).one()
        return request

    def test_no_default_laguage(self) -> None:
        from c2cgeoportal_geoportal.views.fulltextsearch import FullTextSearchView
        from pyramid.httpexceptions import HTTPInternalServerError

        request = self._create_dummy_request()
        del request.registry.settings["default_locale_name"]
        request.accept_language = webob.acceptparse.create_accept_language_header("es")

        fts = FullTextSearchView(request)
        response = fts.fulltextsearch()
        assert isinstance(response, HTTPInternalServerError)

    def test_unknown_laguage(self) -> None:
        from c2cgeoportal_geoportal.views.fulltextsearch import FullTextSearchView
        from pyramid.httpexceptions import HTTPInternalServerError

        request = self._create_dummy_request()
        request.registry.settings["default_locale_name"] = "it"
        request.accept_language = webob.acceptparse.create_accept_language_header("es")
        fts = FullTextSearchView(request)
        response = fts.fulltextsearch()
        assert isinstance(response, HTTPInternalServerError)

    def test_badrequest_noquery(self) -> None:
        from c2cgeoportal_geoportal.views.fulltextsearch import FullTextSearchView
        from pyramid.httpexceptions import HTTPBadRequest

        request = self._create_dummy_request()
        fts = FullTextSearchView(request)
        response = fts.fulltextsearch()
        assert isinstance(response, HTTPBadRequest)

    def test_badrequest_limit(self) -> None:
        from c2cgeoportal_geoportal.views.fulltextsearch import FullTextSearchView
        from pyramid.httpexceptions import HTTPBadRequest

        request = self._create_dummy_request(params=dict(query="text", limit="bad"))
        fts = FullTextSearchView(request)
        response = fts.fulltextsearch()
        assert isinstance(response, HTTPBadRequest)

    def test_badrequest_partitionlimit(self) -> None:
        from c2cgeoportal_geoportal.views.fulltextsearch import FullTextSearchView
        from pyramid.httpexceptions import HTTPBadRequest

        request = self._create_dummy_request(params=dict(query="text", partitionlimit="bad"))
        fts = FullTextSearchView(request)
        response = fts.fulltextsearch()
        assert isinstance(response, HTTPBadRequest)

    def test_limit(self) -> None:
        from c2cgeoportal_geoportal.views.fulltextsearch import FullTextSearchView
        from geojson.feature import FeatureCollection

        request = self._create_dummy_request(params=dict(query="tra sol", limit=1))
        fts = FullTextSearchView(request)
        response = fts.fulltextsearch()
        assert isinstance(response, FeatureCollection)
        assert len(response.features) == 1
        assert response.features[0].properties["label"] == "label1"
        assert response.features[0].properties["layer_name"] == "layer1"

    def test_toobig_limit(self) -> None:
        from c2cgeoportal_geoportal.views.fulltextsearch import FullTextSearchView
        from geojson.feature import FeatureCollection

        request = self._create_dummy_request(params=dict(query="tra sol", limit=2000))
        fts = FullTextSearchView(request)
        response = fts.fulltextsearch()
        assert isinstance(response, FeatureCollection)
        assert len(response.features) == 2
        assert response.features[0].properties["label"] == "label1"
        assert response.features[0].properties["layer_name"] == "layer1"
        assert response.features[1].properties["label"] == "label4"
        assert response.features[1].properties["layer_name"] == "layer1"

    def test_toobig_partitionlimit(self) -> None:
        from c2cgeoportal_geoportal.views.fulltextsearch import FullTextSearchView
        from geojson.feature import FeatureCollection

        request = self._create_dummy_request(params=dict(query="tra sol", partitionlimit=2000))
        fts = FullTextSearchView(request)
        response = fts.fulltextsearch()
        assert isinstance(response, FeatureCollection)
        assert len(response.features) == 2
        assert response.features[0].properties["label"] == "label1"
        assert response.features[0].properties["layer_name"] == "layer1"
        assert response.features[1].properties["label"] == "label4"
        assert response.features[1].properties["layer_name"] == "layer1"

    def test_match(self) -> None:
        from c2cgeoportal_geoportal.views.fulltextsearch import FullTextSearchView
        from geojson.feature import FeatureCollection

        request = self._create_dummy_request(params=dict(query="tra sol", limit=40))
        fts = FullTextSearchView(request)
        response = fts.fulltextsearch()
        assert isinstance(response, FeatureCollection)
        assert len(response.features) == 2
        assert response.features[0].properties["label"] == "label1"
        assert response.features[0].properties["layer_name"] == "layer1"
        assert response.features[1].properties["label"] == "label4"
        assert response.features[1].properties["layer_name"] == "layer1"

    def test_nomatch(self) -> None:
        from c2cgeoportal_geoportal.views.fulltextsearch import FullTextSearchView
        from geojson.feature import FeatureCollection

        request = self._create_dummy_request(params=dict(query="foo"))
        fts = FullTextSearchView(request)
        response = fts.fulltextsearch()
        assert isinstance(response, FeatureCollection)
        assert len(response.features) == 0

    def test_private_nomatch(self) -> None:
        from c2cgeoportal_geoportal.views.fulltextsearch import FullTextSearchView
        from geojson.feature import FeatureCollection

        request = self._create_dummy_request(params=dict(query="pl sem", limit=40))
        fts = FullTextSearchView(request)
        response = fts.fulltextsearch()
        assert isinstance(response, FeatureCollection)
        assert len(response.features) == 0

    def test_private_match(self) -> None:
        from c2cgeoportal_geoportal.views.fulltextsearch import FullTextSearchView
        from geojson.feature import FeatureCollection

        request = self._create_dummy_request(params=dict(query="pl sem", limit=40), username="__test_user1")
        fts = FullTextSearchView(request)
        response = fts.fulltextsearch()
        assert isinstance(response, FeatureCollection)
        assert len(response.features) == 1
        assert response.features[0].properties["label"] == "label2"
        assert response.features[0].properties["layer_name"] == "layer2"

    def test_private_with_role_nomatch(self) -> None:
        from c2cgeoportal_geoportal.views.fulltextsearch import FullTextSearchView
        from geojson.feature import FeatureCollection

        request = self._create_dummy_request(params=dict(query="ven nei", limit=40), username="__test_user1")
        fts = FullTextSearchView(request)
        response = fts.fulltextsearch()
        assert isinstance(response, FeatureCollection)
        assert len(response.features) == 0

    def test_private_with_role_match(self) -> None:
        from c2cgeoportal_geoportal.views.fulltextsearch import FullTextSearchView
        from geojson.feature import FeatureCollection

        request = self._create_dummy_request(params=dict(query="ven nei", limit=40), username="__test_user2")
        fts = FullTextSearchView(request)
        response = fts.fulltextsearch()
        assert isinstance(response, FeatureCollection)
        assert len(response.features) == 1
        assert response.features[0].properties["label"] == "label3"
        assert response.features[0].properties["layer_name"] == "layer3"

    def test_match_partitionlimit(self) -> None:
        from c2cgeoportal_geoportal.views.fulltextsearch import FullTextSearchView
        from geojson.feature import FeatureCollection

        request = self._create_dummy_request(params=dict(query="tra sol", limit=40, partitionlimit=1))
        fts = FullTextSearchView(request)
        response = fts.fulltextsearch()
        assert isinstance(response, FeatureCollection)
        assert len(response.features) == 1
        assert response.features[0].properties["label"] == "label1"
        assert response.features[0].properties["layer_name"] == "layer1"

    def test_params_actions(self) -> None:
        from c2cgeoportal_geoportal.views.fulltextsearch import FullTextSearchView
        from geojson.feature import FeatureCollection

        request = self._create_dummy_request(params=dict(query="lausanne", limit=10))
        fts = FullTextSearchView(request)
        response = fts.fulltextsearch()
        assert isinstance(response, FeatureCollection)
        assert len(response.features) == 1
        assert response.features[0].properties["label"] == "label5"
        assert response.features[0].properties["params"] == {"floor": 5}
        assert response.features[0].properties["actions"] == [{"action": "add_layer", "data": "layer1"}]

    def test_interface(self) -> None:
        from c2cgeoportal_geoportal.views.fulltextsearch import FullTextSearchView
        from geojson.feature import FeatureCollection

        request = self._create_dummy_request(params=dict(query="lausanne", limit=10, interface="main"))
        fts = FullTextSearchView(request)
        response = fts.fulltextsearch()
        assert isinstance(response, FeatureCollection)
        assert {feature.properties["label"] for feature in response.features} == {"label5", "label6"}

    def test_rank_order_with_similarity(self) -> None:
        from c2cgeoportal_geoportal.views.fulltextsearch import FullTextSearchView
        from geojson.feature import FeatureCollection

        request = self._create_dummy_request(params=dict(query="simi", limit=3))
        fts = FullTextSearchView(request)
        response = fts.fulltextsearch()
        assert isinstance(response, FeatureCollection)
        assert len(response.features) == 3
        assert response.features[0].properties["label"] == "A 7 simi"
        assert response.features[1].properties["label"] == "A 70 simi"
        assert response.features[2].properties["label"] == "A 71 simi"

    def test_rank_order_with_ts_rank_cd(self) -> None:
        from c2cgeoportal_geoportal.views.fulltextsearch import FullTextSearchView
        from geojson.feature import FeatureCollection

        request = self._create_dummy_request(params=dict(query="simi", limit=3, ranksystem="ts_rank_cd"))
        fts = FullTextSearchView(request)
        response = fts.fulltextsearch()
        assert isinstance(response, FeatureCollection)
        assert isinstance(response.features, list)
        assert len(response.features) == 3
        # Order change with new version of PostgreSQL...
        assert [f.properties["label"] for f in response.features] == ["A 7 simi", "A 70 simi", "A 71 simi"]

    def test_extra_quote(self) -> None:
        from c2cgeoportal_geoportal.views.fulltextsearch import FullTextSearchView
        from geojson.feature import FeatureCollection

        request = self._create_dummy_request(params=dict(query="tra 'sol"))
        fts = FullTextSearchView(request)
        response = fts.fulltextsearch()
        assert isinstance(response, FeatureCollection)
        assert len(response.features) == 2
        assert response.features[0].properties["label"] == "label1"
        assert response.features[0].properties["layer_name"] == "layer1"
        assert response.features[1].properties["label"] == "label4"
        assert response.features[1].properties["layer_name"] == "layer1"
