# -*- coding: utf-8 -*-

# Copyright (c) 2012-2018, Camptocamp SA
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
from pyramid.testing import DummyRequest

from c2c.template.config import config
import c2cgeoportal_geoportal
from c2cgeoportal_geoportal import call_hook, set_user_validator, \
    default_user_validator, create_get_user_from_request, is_valid_referer


class TestIncludeme(TestCase):

    config = None

    def setup_method(self, _):
        # the c2cgeoportal includeme function requires a number
        # of settings
        self.config = testing.setUp(settings={
            "sqlalchemy.url": "postgresql://www-data:www-data@db:5432/geomapfish_tests",
            "srid": 3857,
            "schema": "main",
            "schema_static": "main_static",
            "default_max_age": 86400,
            "app.cfg": "/src/geoportal/tests/config.yaml",
            "package": "c2cgeoportal",
            "enable_admin_interface": False,
        })

    def test_set_user_validator_directive(self):
        self.config.include(c2cgeoportal_geoportal.includeme)
        self.assertTrue(
            self.config.set_user_validator.__func__.__docobj__ is
            set_user_validator
        )

    def test_default_user_validator(self):
        self.config.include(c2cgeoportal_geoportal.includeme)
        self.assertEqual(
            self.config.registry.validate_user,
            default_user_validator
        )

    def test_user_validator_overwrite(self):
        self.config.include(c2cgeoportal_geoportal.includeme)

        def custom_validator(username, password):
            del username  # Unused
            del password  # Unused
            return False  # pragma: no cover
        self.config.set_user_validator(custom_validator)
        self.assertEqual(self.config.registry.validate_user, custom_validator)


class TestReferer(TestCase):
    """
    Check that accessing something with a bad HTTP referer is equivalent to a
    not authenticated query.
    """
    BASE1 = "http://example.com/app"
    BASE2 = "http://friend.com/app2"
    SETTINGS = {"authorized_referers": [
        BASE1,
        BASE2
    ]}
    USER = "toto"

    def _get_user(self, to, ref, method="GET"):
        class MockRequest:
            def __init__(self, to, ref, method):
                self.path_qs = to
                self.referer = ref
                self.user_ = TestReferer.USER
                self.method = method

        config._config = {
            'schema': 'main',
            'schema_static': 'main_static',
            'srid': 21781
        }
        get_user = create_get_user_from_request(self.SETTINGS)
        return get_user(MockRequest(to=to, ref=ref, method=method))

    def test_match_url(self):
        def match(reference, value, expected):
            r = DummyRequest()
            r.referer = value
            self.assertEqual(is_valid_referer(r, {
                "authorized_referers": [reference]
            }), expected)

        match("http://example.com/app/", "http://example.com/app?k=v", True)
        match("http://example.com/app/", "http://example.com/app?k=v#link", True)
        match("http://example.com/app/", "http://example.com/app#link", True)
        match("http://example.com/app/", "http://example.com/app", True)
        match("http://example.com/app", "http://example.com/app/", True)
        match("http://example.com/app", "http://example.com/app/x/y", True)
        match("http://example.com", "http://example.com/app/x/y", True)
        match("http://example.com", "http://other.com", False)
        match("http://example.com", "https://example.com", False)
        match("http://example.com/app", "http://example.com/", False)
        match("http://example.com", "http://example.com.bad.org/app/x/y", False)

    def test_positive(self):
        self.assertEqual(
            self._get_user(to=self.BASE1 + "/1", ref=self.BASE1), self.USER)
        self.assertEqual(
            self._get_user(to=self.BASE1 + "/2", ref=self.BASE1 + "/3"), self.USER)
        self.assertEqual(
            self._get_user(to=self.BASE1 + "/4", ref=self.BASE2 + "/5"), self.USER)

    def test_no_ref(self):
        self.assertEqual(self._get_user(to=self.BASE1, ref=None), self.USER)
        self.assertIsNone(self._get_user(to=self.BASE1, ref=""))

        self.assertEqual(self._get_user(to=self.BASE1, ref=None, method="POST"), self.USER)
        self.assertIsNone(self._get_user(to=self.BASE1, ref="", method="POST"))

    def test_bad_ref(self):
        self.assertIsNone(self._get_user(
            to=self.BASE1,
            ref="http://bad.com/hacker"))


def hook(tracer):
    tracer["called"] = True


class TestHooks(TestCase):
    settings = {
        "hooks": {
            "test": "tests.test_init.hook",
            "bad": "c2cgeoportal_geoportal.not_here"
        }
    }

    def test_existing(self):
        tracer = {"called": False}
        call_hook(self.settings, "test", tracer)
        self.assertTrue(tracer["called"])

    def test_no_hook(self):
        call_hook(self.settings, "test2")

    @staticmethod
    def test_no_hooks():
        call_hook({}, "test")

    def test_bad_hook(self):
        self.assertRaises(AttributeError, call_hook, self.settings, "bad")


class TestInit(TestCase):
    def test_add_url_params(self):
        from c2cgeoportal_geoportal.lib import add_url_params
        from urllib.parse import urlparse, parse_qs
        params = {"Name": "Bob", "Age": 18, "Nationality": "Việt Nam"}
        result = add_url_params("http://test/", params)
        presult = urlparse(result)
        self.assertEqual(presult.scheme, "http")
        self.assertEqual(presult.netloc, "test")
        self.assertEqual(presult.path, "/")
        self.assertEqual(presult.params, "")
        self.assertEqual(presult.fragment, "")
        self.assertEqual(parse_qs(presult.query), {
            "Name": ["Bob"],
            "Age": ["18"],
            "Nationality": ["Việt Nam"],
        })
