# -*- coding: utf-8 -*-

# Copyright (c) 2012-2013 by Camptocamp SA


from pyramid.interfaces import IRoutePregenerator, \
    IStaticURLInfo
from zope.interface import implementer
from random import randint


def get_setting(settings, path, default=None):
    value = settings
    for p in path:
        if value and p in value:
            value = value[p]
        else:
            return default
    return value if value else default

@implementer(IRoutePregenerator)
class MultiDommainPregenerator:
    def __call__(self, request, elements, kw):
        base_url = request.registry.settings['base_url']
        if base_url and 'subdomain' in kw:
            kw['_app_url'] = base_url % {
                'sub': kw['subdomain']
            } + request.script_name
        return elements, kw
