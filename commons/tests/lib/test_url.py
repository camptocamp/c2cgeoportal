# Copyright (c) 2013-2023, Camptocamp SA
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

# pylint: disable=missing-docstring

from unittest import TestCase

from pyramid.testing import DummyRequest

from c2cgeoportal_commons.lib.url import Url, get_url2


class TestUrl(TestCase):
    def test_url(self):
        url = Url("http://test/")
        url.add_query({"Name": "Bob", "Age": "18", "Nationality": "Việt Name"})
        assert url.scheme == "http"
        assert url.netloc == "test"
        assert url.path == "/"
        assert url.fragment == ""
        self.assertEqual(url.query, {"Name": "Bob", "Age": "18", "Nationality": "Việt Name"})

    def test_url_encode1(self):
        url = Url("http://example.com/toto")
        url.add_query({"à": "é"})
        assert url.scheme == "http"
        assert url.netloc == "example.com"
        assert url.path == "/toto"
        assert url.fragment == ""
        assert url.query == {"à": "é"}

    def test_url_encode2(self):
        url = Url("http://example.com/toto?à=é")
        url.add_query({"1": "2"})
        assert url.scheme == "http"
        assert url.netloc == "example.com"
        assert url.path == "/toto"
        assert url.fragment == ""
        self.assertEqual(url.query, {"à": "é", "1": "2"})

    def test_url_encode3(self):
        url = Url("http://example.com/toto?%C3%A0=%C3%A9")
        url.add_query({"1": "2"})
        assert url.scheme == "http"
        assert url.netloc == "example.com"
        assert url.path == "/toto"
        assert url.fragment == ""
        self.assertEqual(url.query, {"à": "é", "1": "2"})

    def test_url_port(self):
        url = Url("http://example.com:8480/toto")
        url.add_query({"1": "2"})
        assert url.scheme == "http"
        assert url.hostname == "example.com"
        assert url.netloc == "example.com:8480"
        assert url.path == "/toto"
        assert url.fragment == ""
        assert url.query == {"1": "2"}

    def test_url_noparam(self):
        url = Url("http://example.com/")
        url.add_query({})
        assert url.url() == "http://example.com/"

    def test_url_update(self):
        url = Url("http://test:123/toto?map=123#456")
        url.hostname = "example"
        assert url.netloc == "example:123"
        assert url.port == 123
        assert url.url() == "http://example:123/toto?map=123#456"

        url = Url("http://test:123/toto?map=123#456")
        url.netloc = "example"
        assert url.hostname == "example"
        assert url.port is None
        assert url.url() == "http://example/toto?map=123#456"

        url = Url("http://test:123/toto?map=123#456")
        url.netloc = "example:234"
        assert url.hostname == "example"
        assert url.port == 234
        assert url.url() == "http://example:234/toto?map=123#456"

        url = Url("http://test:123/toto?map=123#456")
        url.port = 345
        assert url.netloc == "test:345"
        assert url.hostname == "test"
        assert url.url() == "http://test:345/toto?map=123#456"

        url = Url("http://test:123/toto?map=123#456")
        url.port = None
        assert url.netloc == "test"
        assert url.hostname == "test"
        assert url.url() == "http://test/toto?map=123#456"

    def test_get_url2(self):
        request = DummyRequest()
        request.registry.settings = {
            "package": "my_project",
            "servers": {
                "srv": "https://example.com/test",
                "srv_alt": "https://example.com/test/",
                "full_url": "https://example.com/test.xml",
                "srv_no_path": "https://example.com",
            },
        }
        request.scheme = "https"

        def static_url(path, **kwargs):
            del kwargs  # Unused
            return "http://server.org/" + path

        request.static_url = static_url

        self.assertEqual(
            get_url2("test", "static://pr:st/icon.png", request, set()).url(),
            "http://server.org/pr:st/icon.png",
        )
        self.assertEqual(
            get_url2("test", "static:///icon.png", request, set()).url(),
            "http://server.org//etc/geomapfish/static/icon.png",
        )
        self.assertEqual(
            get_url2("test", "config://srv/icon.png", request, set()).url(),
            "https://example.com/test/icon.png",
        )
        self.assertEqual(get_url2("test", "config://srv/", request, set()).url(), "https://example.com/test/")
        self.assertEqual(get_url2("test", "config://srv", request, set()).url(), "https://example.com/test")
        self.assertEqual(
            get_url2("test", "config://srv/icon.png?test=aaa", request, set()).url(),
            "https://example.com/test/icon.png?test=aaa",
        )
        self.assertEqual(
            get_url2("test", "config://srv_alt/icon.png", request, set()).url(),
            "https://example.com/test/icon.png",
        )
        self.assertEqual(
            get_url2("test", "config://full_url", request, set()).url(), "https://example.com/test.xml"
        )
        self.assertEqual(
            get_url2("test", "http://example.com/icon.png", request, set()).url(),
            "http://example.com/icon.png",
        )
        self.assertEqual(
            get_url2("test", "https://example.com/icon.png", request, set()).url(),
            "https://example.com/icon.png",
        )
        errors: set[str] = set()
        self.assertEqual(get_url2("test", "config://srv2/icon.png", request, errors=errors), None)
        self.assertEqual(
            errors,
            {
                "test: The server 'srv2' (config://srv2/icon.png) is not found in the config: [srv, srv_alt, full_url, srv_no_path]",
            },
        )
        self.assertEqual(
            get_url2("test", "config://srv_no_path/icon.png", request, errors=errors).url(),
            "https://example.com/icon.png",
        )
        self.assertEqual(
            get_url2("test", "config://srv_no_path", request, errors=errors).url(), "https://example.com"
        )

    def test_get_url2_dict(self):
        request = DummyRequest()
        request.registry.settings = {
            "package": "my_project",
            "servers": {"srv": {"url": "https://example.com/test_params", "params": {"MAP": "éàè"}}},
        }
        request.scheme = "https"

        self.assertEqual(
            get_url2("test", "config://srv/icon.png?SALT=456", request, set()).url(),
            "https://example.com/test_params/icon.png?MAP=%C3%A9%C3%A0%C3%A8&SALT=456",
        )
