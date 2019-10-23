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
from urllib.parse import parse_qs, urlparse

from c2cgeoportal_geoportal.lib import add_url_params


class TestLib(TestCase):
    def test_add_url_params_encode1(self):
        presult = urlparse(add_url_params("http://example.com/toto", {"à": "é"}))
        self.assertEqual(presult.scheme, "http")
        self.assertEqual(presult.netloc, "example.com")
        self.assertEqual(presult.path, "/toto")
        self.assertEqual(presult.params, "")
        self.assertEqual(presult.fragment, "")
        self.assertEqual(parse_qs(presult.query), {"à": ["é"]})

    def test_add_url_params_encode2(self):
        presult = urlparse(add_url_params("http://example.com/toto?à=é", {"1": "2"}))
        self.assertEqual(presult.scheme, "http")
        self.assertEqual(presult.netloc, "example.com")
        self.assertEqual(presult.path, "/toto")
        self.assertEqual(presult.params, "")
        self.assertEqual(presult.fragment, "")
        self.assertEqual(parse_qs(presult.query), {"à": ["é"], "1": ["2"]})

    def test_add_url_params_encode3(self):
        presult = urlparse(add_url_params("http://example.com/toto?%C3%A0=%C3%A9", {"1": "2"}))
        self.assertEqual(presult.scheme, "http")
        self.assertEqual(presult.netloc, "example.com")
        self.assertEqual(presult.path, "/toto")
        self.assertEqual(presult.params, "")
        self.assertEqual(presult.fragment, "")
        self.assertEqual(parse_qs(presult.query), {"à": ["é"], "1": ["2"]})

    def test_add_url_params_port(self):
        presult = urlparse(add_url_params("http://example.com:8480/toto", {"1": "2"}))
        self.assertEqual(presult.scheme, "http")
        self.assertEqual(presult.netloc, "example.com:8480")
        self.assertEqual(presult.path, "/toto")
        self.assertEqual(presult.params, "")
        self.assertEqual(presult.fragment, "")
        self.assertEqual(parse_qs(presult.query), {"1": ["2"]})

    def test_add_url_params_noparam(self):
        self.assertEqual(add_url_params("http://example.com/", {}), "http://example.com/")
