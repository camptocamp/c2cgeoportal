# -*- coding: utf-8 -*-

from pyramid.i18n import get_localizer, TranslationStringFactory
from pyramid.events import subscriber, BeforeRender, NewRequest


@subscriber(BeforeRender)
def add_renderer_globals(event):
    request = event.get('request')
    if request:
        event['_'] = request.translate
        event['localizer'] = request.localizer

tsf = TranslationStringFactory('c2cgeoportal')


@subscriber(NewRequest)
def add_localizer(event):
    request = event.request
    localizer = get_localizer(request)

    def auto_translate(string):
        return localizer.translate(tsf(string))

    request.localizer = localizer
    request.translate = auto_translate
