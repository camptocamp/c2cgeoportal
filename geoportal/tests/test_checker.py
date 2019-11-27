# -*- coding: utf-8 -*-

# Copyright (c) 2013-2019, Camptocamp SA
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

from c2cgeoportal_geoportal.lib.checker import build_url
from tests import DummyRequest


class TestExportCSVView(TestCase):
    def test_build_url_docker(self):
        request = DummyRequest()
        request.registry.settings = {"checker": {"base_internal_url": "http://localhost:8080"}}
        self.assertEqual(
            build_url("Test", "/toto?titi#tutu", request),
            {"url": "http://localhost:8080/toto?titi#tutu", "headers": {"Cache-Control": "no-cache"}},
        )

    def test_build_url_http(self):
        request = DummyRequest()
        request.registry.settings = {
            "checker": {"base_internal_url": "http://localhost", "forward_host": True}
        }
        self.assertEqual(
            build_url("Test", "/toto?titi#tutu", request),
            {
                "url": "http://localhost/toto?titi#tutu",
                "headers": {"Cache-Control": "no-cache", "Host": "example.com:80"},
            },
        )

    def test_build_url_https(self):
        request = DummyRequest()
        request.registry.settings = {
            "checker": {"base_internal_url": "https://localhost", "forward_host": True}
        }
        self.assertEqual(
            build_url("Test", "/toto?titi#tutu", request),
            {
                "url": "https://localhost/toto?titi#tutu",
                "headers": {"Cache-Control": "no-cache", "Host": "example.com:80"},
            },
        )

    def test_build_url_forward_headers(self):
        request = DummyRequest()
        request.registry.settings = {
            "checker": {"base_internal_url": "http://localhost", "forward_headers": ["Cookie"]}
        }
        request.headers["Cookie"] = "test"
        self.assertEqual(
            build_url("Test", "/toto?titi#tutu", request),
            {
                "url": "http://localhost/toto?titi#tutu",
                "headers": {"Cache-Control": "no-cache", "Cookie": "test"},
            },
        )
