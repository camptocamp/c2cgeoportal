# Copyright (c) 2018-2025, Camptocamp SA
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

import pyramid.url
from c2cgeoportal_geoportal.lib.caching import init_region
from pyramid import testing
from pyramid.testing import testConfig

from tests import DummyRequest
from tests.functional import setup_common as setup_module
from tests.functional import teardown_common as teardown_module


def use(item):
    pass


use(setup_module)
use(teardown_module)


class TestDynamicView(TestCase):
    def setup_method(self, _):
        import transaction
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import FullTextSearch
        from geoalchemy2 import WKTElement
        from sqlalchemy import func

        entry1 = FullTextSearch()
        entry1.label = "label 1"
        entry1.layer_name = "layer1"
        entry1.ts = func.to_tsvector("french", "soleil travail")
        entry1.the_geom = WKTElement("POINT(-90 -45)", 21781)
        entry1.public = True

        entry2 = FullTextSearch()
        entry2.label = "label 2"
        entry2.layer_name = "layer2"
        entry2.ts = func.to_tsvector("french", "pluie semaine")
        entry2.the_geom = WKTElement("POINT(-90 -45)", 21781)
        entry1.public = True

        entry3 = FullTextSearch()
        entry3.label = "label 3"
        entry3.layer_name = "layer2"
        entry3.ts = func.to_tsvector("french", "vent neige")
        entry3.the_geom = WKTElement("POINT(-90 -45)", 21781)
        entry1.public = True

        DBSession.add_all([entry1, entry2, entry3])
        transaction.commit()

        init_region({"backend": "dogpile.cache.memory"}, "std")
        init_region({"backend": "dogpile.cache.memory"}, "obj")
        init_region({"backend": "dogpile.cache.memory"}, "ogc-server")

    def teardown_method(self, _):
        testing.tearDown()

        import transaction
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import FullTextSearch

        DBSession.query(FullTextSearch).filter(FullTextSearch.label == "label 1").delete()
        DBSession.query(FullTextSearch).filter(FullTextSearch.label == "label 2").delete()
        DBSession.query(FullTextSearch).filter(FullTextSearch.label == "label 3").delete()

        transaction.commit()

    @staticmethod
    def _get_settings(settings):
        return {
            "interfaces": [{"name": "test", "default": True}],
            "available_locale_names": ["fr"],
            "package": "package_name",
            "interfaces_config": settings,
        }

    @staticmethod
    def _request(query=None):
        if query is None:
            query = {}
        query_ = {"interface": "test"}
        query_.update(query)
        request = DummyRequest(query_)
        request.route_url = lambda url, _query=None: (
            f"/dummy/route/url/{url}"
            if _query is None
            else f"/dummy/route/url/{url}?{pyramid.url.urlencode(_query)}"
        )
        request.static_url = lambda url, _query=None: (
            f"/dummy/static/url/{url}"
            if _query is None
            else f"/dummy/static/url/{url}?{pyramid.url.urlencode(_query)}"
        )
        request.get_organization_interface = lambda interface: interface
        return request

    def test_constant(self):
        from c2cgeoportal_geoportal.views.dynamic import DynamicView

        request = self._request()
        request.registry.settings = self._get_settings({"test": {"constants": {"XTest": "TOTO"}}})
        dynamic = DynamicView(request).dynamic()

        assert "XTest" in dynamic["constants"], dynamic
        assert dynamic["constants"]["XTest"] == "TOTO"

    def test_constant_default(self):
        from c2cgeoportal_geoportal.views.dynamic import DynamicView

        request = self._request()
        request.registry.settings = self._get_settings(
            {"default": {"constants": {"XTest": "TOTO"}}, "test": {"extends": "default"}}
        )
        dynamic = DynamicView(request).dynamic()

        assert "XTest" in dynamic["constants"], dynamic
        assert dynamic["constants"]["XTest"] == "TOTO"

    def test_constant_json(self):
        from c2cgeoportal_geoportal.views.dynamic import DynamicView

        request = self._request()
        request.registry.settings = self._get_settings({"test": {"constants": {"XTest": ["TOTO"]}}})
        dynamic = DynamicView(request).dynamic()

        assert "XTest" in dynamic["constants"], dynamic
        assert dynamic["constants"]["XTest"] == ["TOTO"]

    def test_constant_dynamic_interface(self):
        from c2cgeoportal_geoportal.views.dynamic import DynamicView

        request = self._request()
        request.registry.settings = self._get_settings(
            {"test": {"dynamic_constants": {"XTest": "interface"}}}
        )
        dynamic = DynamicView(request).dynamic()

        assert "XTest" in dynamic["constants"], dynamic
        assert dynamic["constants"]["XTest"] == "test"

    def test_constant_dynamic_cache_version(self):
        from c2cgeoportal_geoportal.views.dynamic import DynamicView

        request = self._request()
        request.registry.settings = self._get_settings(
            {"test": {"dynamic_constants": {"XTest": "cache_version"}}}
        )
        dynamic = DynamicView(request).dynamic()

        assert "XTest" in dynamic["constants"], dynamic
        from c2cgeoportal_geoportal.lib.cacheversion import get_cache_version

        assert dynamic["constants"]["XTest"] == get_cache_version()

    def test_constant_dynamic_lang_urls(self):
        from c2cgeoportal_geoportal.views.dynamic import DynamicView

        request = self._request()
        request.static_url = lambda url, _query=None: (
            f"/dummy/static/url/{url}"
            if _query is None
            else "/dummy/static/url/{}?{}".format(url, "&".join(["=".join(e) for e in _query.items()]))
        )
        request.registry.settings = self._get_settings(
            {"test": {"dynamic_constants": {"XTest": "lang_urls"}}}
        )
        dynamic = DynamicView(request).dynamic()

        assert "XTest" in dynamic["constants"], dynamic
        assert "fr" in dynamic["constants"]["XTest"], dynamic
        assert dynamic["constants"]["XTest"]["fr"] == "/dummy/static/url//etc/geomapfish/static/fr.json"

    def test_constant_dynamic_fulltextsearch_groups(self):
        from c2cgeoportal_geoportal.views.dynamic import DynamicView

        request = self._request()
        request.static_url = lambda url, _query=None: (
            f"/dummy/static/url/{url}"
            if _query is None
            else "/dummy/static/url/{}?{}".format(url, "&".join(["=".join(e) for e in _query.items()]))
        )
        request.registry.settings = self._get_settings(
            {"test": {"dynamic_constants": {"XTest": "fulltextsearch_groups"}}}
        )
        dynamic = DynamicView(request).dynamic()

        assert "XTest" in dynamic["constants"], dynamic
        assert set(dynamic["constants"]["XTest"]) == {"layer1", "layer2"}

    def test_static(self):
        from c2cgeoportal_geoportal.views.dynamic import DynamicView

        request = self._request()
        request.registry.settings = self._get_settings(
            {"test": {"static": {"XTest": {"name": "test", "append": "/{{name}}.yaml"}}}}
        )
        dynamic = DynamicView(request).dynamic()

        assert "XTest" in dynamic["constants"], dynamic
        assert dynamic["constants"]["XTest"] == "/dummy/static/url/test/{{name}}.yaml"

    def test_route(self):
        from c2cgeoportal_geoportal.views.dynamic import DynamicView

        request = self._request()
        request.registry.settings = self._get_settings(
            {"test": {"routes": {"XTest": {"name": "test", "params": {"test": "value"}}}}}
        )
        dynamic = DynamicView(request).dynamic()

        assert "XTest" in dynamic["constants"], dynamic
        assert dynamic["constants"]["XTest"] == "/dummy/route/url/test?test=value"

    def test_route_with_keywords(self):
        from c2cgeoportal_geoportal.views.dynamic import DynamicView

        with testConfig(
            settings=self._get_settings(
                {
                    "test": {
                        "routes": {
                            "XTest": {"name": "route_with_keywords", "kw": {"key1": "v1", "key2": "v2"}}
                        }
                    }
                }
            )
        ) as config:
            config.add_static_view(name="static", path="/etc/geomapfish/static")
            config.add_route("base", "/", static=True)
            config.add_route("test", "/test")
            config.add_route("route_with_keywords", "/test/{key1}/{key2}")
            request = DummyRequest({"interface": "test"})
            request.get_organization_interface = lambda interface: interface
            dynamic = DynamicView(request).dynamic()

        assert "XTest" in dynamic["constants"], dynamic
        assert dynamic["constants"]["XTest"] == "http://example.com/test/v1/v2"

    def test_route_with_segments(self):
        from c2cgeoportal_geoportal.views.dynamic import DynamicView

        with testConfig(
            settings=self._get_settings(
                {"test": {"routes": {"XTest": {"name": "route_with_segments", "elements": ["s1", "s2"]}}}}
            )
        ) as config:
            config.add_static_view(name="static", path="/etc/geomapfish/static")
            config.add_route("base", "/", static=True)
            config.add_route("test", "/test")
            config.add_route("route_with_segments", "/test")
            request = DummyRequest({"interface": "test"})
            request.get_organization_interface = lambda interface: interface
            dynamic = DynamicView(request).dynamic()

        assert "XTest" in dynamic["constants"], dynamic
        assert dynamic["constants"]["XTest"] == "http://example.com/test/s1/s2"

    def test_route_with_all(self):
        from c2cgeoportal_geoportal.views.dynamic import DynamicView

        with testConfig(
            settings=self._get_settings(
                {
                    "test": {
                        "routes": {
                            "XTest": {
                                "name": "route_with_all",
                                "kw": {"key1": "v1", "key2": "v2"},
                                "elements": ["s1", "s2"],
                                "params": {"test": "value"},
                            }
                        }
                    }
                }
            )
        ) as config:
            config.add_static_view(name="static", path="/etc/geomapfish/static")
            config.add_route("base", "/", static=True)
            config.add_route("test", "/test")
            config.add_route("route_with_all", "/test/{key1}/{key2}")
            request = DummyRequest({"interface": "test"})
            request.get_organization_interface = lambda interface: interface
            dynamic = DynamicView(request).dynamic()

        assert "XTest" in dynamic["constants"], dynamic
        assert dynamic["constants"]["XTest"] == "http://example.com/test/v1/v2/s1/s2?test=value"

    def test_route_dynamic(self):
        from c2cgeoportal_geoportal.views.dynamic import DynamicView

        request = self._request()
        request.registry.settings = self._get_settings(
            {"test": {"routes": {"XTest": {"name": "test", "dynamic_params": {"test": "interface"}}}}}
        )
        dynamic = DynamicView(request).dynamic()

        assert "XTest" in dynamic["constants"], dynamic
        assert dynamic["constants"]["XTest"] == "/dummy/route/url/test?test=test"

    def test_redirect(self):
        from c2cgeoportal_geoportal.views.dynamic import DynamicView

        request = self._request()
        request.registry.settings = self._get_settings({"test": {"redirect_interface": "test_redirect"}})
        dynamic = DynamicView(request).dynamic()

        assert dynamic == {
            "constants": {"redirectUrl": "/dummy/route/url/test_redirect?no_redirect=t"},
            "doRedirect": False,
            "redirectUrl": "/dummy/route/url/test_redirect?",
        }

    def test_doredirect(self):
        from c2cgeoportal_geoportal.views.dynamic import DynamicView

        request = self._request()
        request.registry.settings = self._get_settings(
            {"test": {"redirect_interface": "test_redirect", "do_redirect": True}}
        )
        dynamic = DynamicView(request).dynamic()

        assert dynamic == {
            "constants": {},
            "doRedirect": True,
            "redirectUrl": "/dummy/route/url/test_redirect?",
        }

    def test_noredirect(self):
        from c2cgeoportal_geoportal.views.dynamic import DynamicView

        request = self._request({"no_redirect": "t"})
        request.registry.settings = self._get_settings(
            {"test": {"redirect_interface": "test_redirect", "do_redirect": True}}
        )
        dynamic = DynamicView(request).dynamic()

        assert dynamic == {
            "constants": {},
            "doRedirect": True,
            "redirectUrl": "/dummy/route/url/test_redirect?",
        }

    def test_redirect_space(self):
        from c2cgeoportal_geoportal.views.dynamic import DynamicView

        request = self._request({"query": "?test=_%20_"})
        request.registry.settings = self._get_settings(
            {"test": {"redirect_interface": "test_redirect", "do_redirect": True}}
        )
        dynamic = DynamicView(request).dynamic()

        assert dynamic == {
            "constants": {},
            "doRedirect": True,
            "redirectUrl": "/dummy/route/url/test_redirect?test=_%20_",
        }

    def test_cross_overrid_1(self):
        from c2cgeoportal_geoportal.views.dynamic import DynamicView

        request = self._request()
        request.registry.settings = self._get_settings(
            {
                "default": {"constants": {"XTest": "TOTO"}},
                "test": {"dynamic_constants": {"XTest": "interface"}},
            }
        )
        dynamic = DynamicView(request).dynamic()

        assert "XTest" in dynamic["constants"], dynamic
        assert dynamic["constants"]["XTest"] == "test"

    def test_cross_overrid_2(self):
        from c2cgeoportal_geoportal.views.dynamic import DynamicView

        request = self._request()
        request.registry.settings = self._get_settings(
            {
                "default": {"dynamic_constants": {"XTest": "interface"}},
                "test": {"constants": {"XTest": "TOTO"}},
            }
        )
        dynamic = DynamicView(request).dynamic()

        assert "XTest" in dynamic["constants"], dynamic
        assert dynamic["constants"]["XTest"] == "TOTO"

    def test_currentInterface(self):
        from c2cgeoportal_geoportal.views.dynamic import DynamicView

        request = self._request()
        request.registry.settings = self._get_settings(
            {"test": {"routes": {"test_ci": {"currentInterface": True}}}}
        )
        dynamic = DynamicView(request).dynamic()

        assert dynamic["constants"] == {"test_ci": "/dummy/route/url/test?"}
