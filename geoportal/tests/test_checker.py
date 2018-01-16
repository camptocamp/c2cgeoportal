# -*- coding: utf-8 -*-

# Copyright (c) 2013-2018, Camptocamp SA
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

from pyramid.testing import DummyRequest

from c2cgeoportal_geoportal.lib.checker import build_url


class TestExportCSVView(TestCase):

    @staticmethod
    def _create_dummy_request():
        request = DummyRequest()
        request.environ = {
            "SERVER_NAME": "example.com"
        }
        return request

    def test_build_url_http(self):
        self.assertEqual(
            build_url(
                "Test",
                "http://example.com/toto?titi#tutu",
                self._create_dummy_request()
            ),
            {
                "url": "http://localhost/toto?titi#tutu",
                "headers": {
                    "Cache-Control": "no-cache",
                    "Host": "example.com"
                }
            }
        )

    def test_build_url_https(self):
        self.assertEqual(
            build_url(
                "Test",
                "https://example.com/toto?titi#tutu",
                self._create_dummy_request()
            ),
            {
                "url": "http://localhost/toto?titi#tutu",
                "headers": {
                    "Cache-Control": "no-cache",
                    "Host": "example.com"
                }
            }
        )

    def test_build_url_other(self):
        self.assertEqual(
            build_url(
                "Test",
                "https://camptocamp.com/toto?titi#tutu",
                self._create_dummy_request()
            ),
            {
                "url": "https://camptocamp.com/toto?titi#tutu",
                "headers": {
                    "Cache-Control": "no-cache",
                }
            }
        )

    def test_build_url_forward_headers(self):
        request = DummyRequest()
        request.environ = {
            "SERVER_NAME": "example.com"
        }
        request.registry.settings = {
            "checker": {
                "forward_headers": ["Cookie"]
            }
        }
        request.headers["Cookie"] = "test"
        self.assertEqual(
            build_url(
                "Test",
                "https://camptocamp.com/toto?titi#tutu",
                request
            ),
            {
                "url": "https://camptocamp.com/toto?titi#tutu",
                "headers": {
                    "Cache-Control": "no-cache",
                    "Cookie": "test",
                }
            }
        )
