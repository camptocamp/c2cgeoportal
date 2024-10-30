# Copyright (c) 2012-2024, Camptocamp SA
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
from unittest.mock import patch

import pytest
from c2c.template.config import config
from pyramid import testing
from tests import DummyRequest

import c2cgeoportal_geoportal
from c2cgeoportal_geoportal import (
    call_hook,
    create_get_user_from_request,
    default_user_validator,
    is_valid_referrer,
    set_user_validator,
)


class TestIncludeme(TestCase):
    config = None

    def setup_method(self, _):
        # the c2cgeoportal includeme function requires a number
        # of settings
        self.config = testing.setUp(
            settings={
                "sqlalchemy.url": "postgresql://www-data:www-data@db:5432/geomapfish_tests",
                "srid": 3857,
                "schema": "main",
                "schema_static": "main_static",
                "default_max_age": 86400,
                "package": "c2cgeoportal",
                "enable_admin_interface": False,
                "getitfixed": {"enabled": False},
                "metrics": {
                    "memory_maps_rss": False,
                    "memory_maps_size": False,
                    "memory_cache": False,
                    "memory_cache_all": False,
                    "raster_data": False,
                    "total_python_object_memory": False,
                },
            }
        )
        config.init("/opt/c2cgeoportal/geoportal/tests/config.yaml")

    @patch("c2cgeoportal_geoportal.available_locale_names", return_value=["de", "en", "fr"])
    def test_available_locale_names(self, locales_mock):
        self.config.include(c2cgeoportal_geoportal.includeme)
        self.assertEqual(self.config.registry.settings["available_locale_names"], ["de", "en", "fr"])

    def test_set_user_validator_directive(self):
        self.config.include(c2cgeoportal_geoportal.includeme)
        self.assertTrue(self.config.set_user_validator.__func__.__docobj__ is set_user_validator)

    def test_default_user_validator(self):
        self.config.include(c2cgeoportal_geoportal.includeme)
        assert self.config.registry.validate_user == default_user_validator

    def test_user_validator_overwrite(self):
        self.config.include(c2cgeoportal_geoportal.includeme)

        def custom_validator(username, password):
            del username  # Unused
            del password  # Unused
            return False

        self.config.set_user_validator(custom_validator)
        assert self.config.registry.validate_user == custom_validator


@pytest.mark.parametrize(
    "authorized,value,expected",
    [
        ("https://example.com", "http://example.com/app", True),
        ("http://example.com", "https://example.com/app", True),
        ("example.com", "http://example.com/app?k=v", True),
        ("example.com", "http://example.com/app?k=v#link", True),
        ("example.com", "http://example.com/app#link", True),
        ("example.com", "http://example.com/app", True),
        ("example.com", "http://example.com/app/", True),
        ("example.com", "http://example.com/app/x/y", True),
        ("example.com", "http://example.com/app/x/y", True),
        ("example.com", "http://other.com", False),
        ("example.com", "http://example.com.bad.org/app/x/y", False),
        ("example.com:8080", "http://example.com:8080/app", True),
        ("example.com:8080", "http://example.com/app", False),
        ("example.com", "http://example.com:8080/app", False),
        ("other.com", "http://example-test.com", True),
    ],
)
def test_is_valid_referrer(authorized, value, expected):
    r = DummyRequest()
    r.referrer = value
    r.host = "example-test.com"
    assert is_valid_referrer(r, {"authorized_referers": [authorized]}) == expected


class TestReferer(TestCase):
    """
    Check that accessing something with a bad HTTP referrer is equivalent to a not authenticated query.
    """

    BASE1 = "http://example.com/app"
    BASE2 = "http://friend.com/app2"
    SETTINGS = {"authorized_referers": ["friend.com"]}
    USER = "toto"

    def _get_user(self, to, ref, method="GET", host="example.com"):
        class MockRequest:
            def __init__(self, to, ref, method):
                self.path_qs = to
                self.referrer = ref
                self.user_ = TestReferer.USER
                self.method = method
                self.host = host

        config._config = {
            "schema": "main",
            "schema_static": "main_static",
            "srid": 21781,
            "authorized_referers": ["example.com"],
        }
        get_user = create_get_user_from_request(self.SETTINGS)
        return get_user(MockRequest(to=to, ref=ref, method=method))

    def test_positive(self):
        assert self._get_user(to=self.BASE1 + "/1", ref=self.BASE1) == self.USER
        assert self._get_user(to=self.BASE1 + "/2", ref=self.BASE1 + "/3") == self.USER
        assert self._get_user(to=self.BASE1 + "/4", ref=self.BASE2 + "/5") == self.USER

    def test_no_ref(self):
        assert self._get_user(to=self.BASE1, ref=None) == self.USER
        assert self._get_user(to=self.BASE1, ref="") is None

        assert self._get_user(to=self.BASE1, ref=None, method="POST") == self.USER
        assert self._get_user(to=self.BASE1, ref="", method="POST") is None

    def test_bad_ref(self):
        self.assertIsNone(self._get_user(to=self.BASE1, ref="http://bad.com/hacker"))


def hook(tracer):
    tracer["called"] = True


class TestHooks(TestCase):
    settings = {"hooks": {"test": "tests.test_init.hook", "bad": "c2cgeoportal_geoportal.not_here"}}

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
