# -*- coding: utf-8 -*-

# Copyright (c) 2012-2016, Camptocamp SA
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

import c2cgeoportal


class TestIncludeme(TestCase):

    def setUp(self):  # noqa
        self.config = testing.setUp(
            # the c2cgeoportal includeme function requires a number
            # of settings
            settings={
                "sqlalchemy.url": "postgresql://u:p@h/d",
                "srid": 3857,
                "schema": "main",
                "parentschema": "",
                "default_max_age": 86400,
                "app.cfg": "c2cgeoportal/tests/config.yaml",
                "package": "c2cgeoportal",
                "enable_admin_interface": True,
            })

    def test_set_user_validator_directive(self):
        self.config.include(c2cgeoportal.includeme)
        self.failUnless(
            self.config.set_user_validator.im_func.__docobj__ is
            c2cgeoportal.set_user_validator
        )

    def test_default_user_validator(self):
        self.config.include(c2cgeoportal.includeme)
        self.assertEqual(self.config.registry.validate_user,
                         c2cgeoportal.default_user_validator)

    def test_user_validator_overwrite(self):
        self.config.include(c2cgeoportal.includeme)

        def custom_validator(username, password):
            return False  # pragma: nocover
        self.config.set_user_validator(custom_validator)
        self.assertEqual(self.config.registry.validate_user,
                         custom_validator)


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

    def _get_user(self, to, ref):
        class MockRequest(object):
            def __init__(self, to, ref):
                self.path_qs = to
                self.referer = ref
                self._user = TestReferer.USER

            def path_info_peek(self):
                return "main"

        get_user = c2cgeoportal._create_get_user_from_request(self.SETTINGS)
        return get_user(MockRequest(to=to, ref=ref))

    def test_match_url(self):
        def match(ref, val, expected):
            self.assertEqual(c2cgeoportal._match_url_start(ref, val), expected)

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
            self._get_user(to=self.BASE1 + "/2", ref=self.BASE1 + "/3"),
            self.USER)
        self.assertEqual(
            self._get_user(to=self.BASE1 + "/4", ref=self.BASE2 + "/5"),
            self.USER)

    def test_no_ref(self):
        self.assertIsNone(self._get_user(to=self.BASE1, ref=None))
        self.assertIsNone(self._get_user(to=self.BASE1, ref=""))

    def test_bad_ref(self):
        self.assertIsNone(self._get_user(to=self.BASE1,
                                         ref="http://bad.com/hacker"))


def hook(tracer):
    tracer["called"] = True


class TestHooks(TestCase):
    settings = {
        "hooks": {
            "test": "c2cgeoportal.tests.test_init.hook",
            "bad": "c2cgeoportal.not_here"
        }
    }

    def test_existing(self):
        tracer = {"called": False}
        c2cgeoportal.call_hook(self.settings, "test", tracer)
        self.assertTrue(tracer["called"])

    def test_no_hook(self):
        c2cgeoportal.call_hook(self.settings, "test2")

    def test_no_hooks(self):
        c2cgeoportal.call_hook({}, "test")

    def test_bad_hook(self):
        self.assertRaises(AttributeError, c2cgeoportal.call_hook, self.settings, "bad")
