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
from pyramid import testing


class TestLocalNegociator(TestCase):
    def test_lang_param(self):
        from c2cgeoportal_geoportal import locale_negotiator

        request = testing.DummyRequest(params=dict(lang="fr"))
        lang = locale_negotiator(request)
        self.assertEqual(lang, "fr")

    def test_lang_is_not_available(self):
        from c2cgeoportal_geoportal import locale_negotiator
        from pyramid.threadlocal import get_current_registry
        from pyramid.request import Request

        request = Request.blank("/")
        request.registry = get_current_registry()
        request.registry.settings = {
            "default_locale_name": "de",
            "available_locale_names": ["de", "es"]
        }

        request.headers["accept-language"] = "en-us,en;q=0.3,fr;q=0.7"
        lang = locale_negotiator(request)
        self.assertEqual(lang, "de")

    def test_lang_is_available(self):
        from c2cgeoportal_geoportal import locale_negotiator
        from pyramid.threadlocal import get_current_registry
        from pyramid.request import Request

        request = Request.blank("/")
        request.registry = get_current_registry()
        request.registry.settings = {
            "default_locale_name": "de",
            "available_locale_names": ["de", "es"]
        }
        request.accept_language = "en-us,en;q=0.3,es;q=0.7"
        lang = locale_negotiator(request)
        self.assertEqual(lang, "es")
