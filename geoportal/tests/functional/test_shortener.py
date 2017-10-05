# -*- coding: utf-8 -*-

# Copyright (c) 2013-2017, Camptocamp SA
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


from unittest import TestCase

from pyramid import testing

from tests.functional import (  # noqa
    teardown_common as teardown_module, setup_common as setup_module
)


class TestshortenerView(TestCase):

    def teardown_method(self, _):
        testing.tearDown()

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import Shorturl
        import transaction
        DBSession.query(Shorturl).delete()
        transaction.commit()

    def test_shortener(self):
        from pyramid.testing import DummyRequest
        from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest
        from c2cgeoportal_geoportal.views.shortener import Shortener

        def route_url(name, *elements, **kw):
            return "https://example.com/short/" + kw["ref"]

        request = DummyRequest()
        request.user = None
        request.host = "example.com:443"
        request.server_name = "example.com"
        request.route_url = route_url
        request.registry.settings["shortener"] = {
            "base_url": "https://example.com/s/"
        }
        shortener = Shortener(request)

        request.params = {}
        request.matchdict = {
            "ref": "AAAAAA"
        }
        self.assertRaises(HTTPNotFound, shortener.get)

        request.params = {}
        request.matchdict = {}
        self.assertRaises(HTTPBadRequest, shortener.create)

        request.params = {
            "url": "https://other-site.com/hi"
        }
        self.assertRaises(HTTPBadRequest, shortener.create)

    def test_shortener_create_1(self):
        from pyramid.testing import DummyRequest
        from pyramid.httpexceptions import HTTPFound
        from c2cgeoportal_geoportal.views.shortener import Shortener

        def route_url(name, *elements, **kw):
            return "https://example.com/short/" + kw["ref"]

        request = DummyRequest()
        request.user = None
        request.host = "example.com:443"
        request.server_name = "example.com"
        request.route_url = route_url
        request.registry.settings["shortener"] = {
            "base_url": "https://example.com/s/"
        }
        shortener = Shortener(request)

        request.params = {
            "url": "https://example.com/hi"
        }
        result = shortener.create()
        index = result["short_url"].rfind("/")
        self.assertEqual(
            result["short_url"][:index],
            "https://example.com/s"
        )

        request.params = {}
        request.matchdict = {
            "ref": result["short_url"][index + 1:]
        }
        result = shortener.get()
        self.assertEqual(type(result), HTTPFound)
        self.assertEqual(result.location, "https://example.com/hi")

    def test_shortener_create_2(self):
        from pyramid.testing import DummyRequest
        from pyramid.httpexceptions import HTTPFound
        from c2cgeoportal_geoportal.views.shortener import Shortener

        def route_url(name, *elements, **kw):
            return "https://example.com/short/" + kw["ref"]

        request = DummyRequest()
        request.user = None
        request.host = "example.com:443"
        request.server_name = "example.com"
        request.route_url = route_url
        request.registry.settings["shortener"] = {}
        shortener = Shortener(request)

        request.params = {
            "url": "https://example.com/hi"
        }
        result = shortener.create()
        index = result["short_url"].rfind("/")
        self.assertEqual(
            result["short_url"][:index],
            "https://example.com/short"
        )

        request.params = {}
        request.matchdict = {
            "ref": result["short_url"][index + 1:]
        }
        result = shortener.get()
        self.assertEqual(type(result), HTTPFound)
        self.assertEqual(result.location, "https://example.com/hi")

    def test_shortener_noreplace_1(self):
        from pyramid.testing import DummyRequest
        from c2cgeoportal_geoportal.views.shortener import Shortener

        def route_url(name, *elements, **kw):
            return "https://example.com/short/" + kw["ref"]

        request = DummyRequest()
        request.user = None
        request.host = "example.com:443"
        request.server_name = "example.com"
        request.route_url = route_url
        request.registry.settings["shortener"] = {
            "base_url": "https://example.com/s/"
        }
        shortener = Shortener(request)

        request.params = {
            "url": "https://example.com/short/truite"
        }
        result = shortener.create()
        self.assertEqual(result["short_url"], "https://example.com/s/truite")

    def test_shortener_noreplace_2(self):
        from pyramid.testing import DummyRequest
        from c2cgeoportal_geoportal.views.shortener import Shortener

        def route_url(name, *elements, **kw):
            return "https://example.com/short/" + kw["ref"]

        request = DummyRequest()
        request.user = None
        request.host = "example.com:443"
        request.server_name = "example.com"
        request.route_url = route_url
        request.registry.settings["shortener"] = {
            "base_url": "https://example.com/s/"
        }
        shortener = Shortener(request)

        request.params = {
            "url": "https://example.com/s/truite"
        }
        result = shortener.create()
        self.assertEqual(result["short_url"], "https://example.com/s/truite")

    def test_shortener_baseurl(self):
        from pyramid.testing import DummyRequest
        from c2cgeoportal_geoportal.views.shortener import Shortener

        def route_url(name, *elements, **kw):
            return "https://example.com/short/" + kw["ref"]

        request = DummyRequest()
        request.user = None
        request.host = "example.com:443"
        request.server_name = "example.com"
        request.route_url = route_url
        request.registry.settings["shortener"] = {
            "base_url": "http://my_host/my_short/"
        }
        shortener = Shortener(request)

        request.params = {
            "url": "https://example.com/hi"
        }
        result = shortener.create()
        index = result["short_url"].rfind("/")
        self.assertEqual(
            result["short_url"][:index],
            "http://my_host/my_short"
        )
