# -*- coding: utf-8 -*-

from pyramid import testing


def test_lang_param():
    from c2cgeoportal import locale_negotiator

    request = testing.DummyRequest(params=dict(lang='fr'))
    lang = locale_negotiator(request)
    assert lang == 'fr'


def test_lang_is_not_available():
    from c2cgeoportal import locale_negotiator
    from pyramid.threadlocal import get_current_registry
    from pyramid.request import Request

    request = Request.blank('/')
    request.registry = get_current_registry()
    request.registry.settings = {
            'default_language': 'de',
            'available_languages': 'de es'
            }
    request.accept_language = 'en-us,en;q=0.3,fr;q=0.7'
    lang = locale_negotiator(request)
    assert lang == 'de'


def test_lang_is_available():
    from c2cgeoportal import locale_negotiator
    from pyramid.threadlocal import get_current_registry
    from pyramid.request import Request

    request = Request.blank('/')
    request.registry = get_current_registry()
    request.registry.settings = {
            'default_language': 'de',
            'available_languages': 'de es'
            }
    request.accept_language = 'en-us,en;q=0.3,es;q=0.7'
    lang = locale_negotiator(request)
    assert lang == 'es'
