# -*- coding: utf-8 -*-

"""
This module provides callables that can be used as view
callables for the mobile application.
"""

from pyramid.i18n import get_locale_name


def _common(request):
    _vars = {
        "lang": get_locale_name(request)
    }
    return _vars


def index(request):
    """
    View callable for the mobile application's index.html file.
    """
    return _common(request)


def config(request):
    """
    View callable for the mobile application's config.js file.
    """
    request.response.content_type = 'application/javascript'
    return _common(request)
