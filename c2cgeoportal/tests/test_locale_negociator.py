# -*- coding: utf-8 -*-

# Copyright (c) 2012-2013 by Camptocamp SA


from unittest import TestCase
from pyramid import testing

class TestLocalNegociator(TestCase):
    def test_lang_param(self):
        from c2cgeoportal import locale_negotiator

        request = testing.DummyRequest(params=dict(lang='fr'))
        lang = locale_negotiator(request)
        self.assertEquals(lang, 'fr')


    def test_lang_is_not_available(self):
        from c2cgeoportal import locale_negotiator
        from pyramid.threadlocal import get_current_registry
        from pyramid.request import Request

        request = Request.blank('/')
        request.registry = get_current_registry()
        request.registry.settings = {
            'default_locale_name': 'de',
            'available_locale_names': ['de', 'es']
        }

        request.headers['accept-language'] = 'en-us,en;q=0.3,fr;q=0.7'
        lang = locale_negotiator(request)
        self.assertEquals(lang, None)


    def test_lang_is_available(self):
        from c2cgeoportal import locale_negotiator
        from pyramid.threadlocal import get_current_registry
        from pyramid.request import Request

        request = Request.blank('/')
        request.registry = get_current_registry()
        request.registry.settings = {
            'default_locale_name': 'de',
            'available_locale_names': ['de', 'es']
        }
        request.accept_language = 'en-us,en;q=0.3,es;q=0.7'
        lang = locale_negotiator(request)
        self.assertEquals(lang, 'es')
