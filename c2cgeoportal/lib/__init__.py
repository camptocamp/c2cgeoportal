# -*- coding: utf-8 -*-

# Copyright (c) 2012-2013 by Camptocamp SA


from pyramid.interfaces import IRoutePregenerator, \
    IStaticURLInfo
from zope.interface import implementer
from random import randint
from pyramid.compat import WIN
from pyramid.config.views import StaticURLInfo


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

@implementer(IStaticURLInfo)
class MultiDommainStaticURLInfo(StaticURLInfo):
    def generate(self, path, request, **kw):
        registry = request.registry
        for (url, spec, route_name) in self._get_registrations(registry):
            if path.startswith(spec):
                subpath = path[len(spec):]
                if WIN:
                    subpath = subpath.replace('\\', '/') # windows
                if url is None:
                    kw['subpath'] = subpath
                    sub_url = request.registry.settings['sub_url']
                    if isinstance(sub_url, list):
                        return request.route_url(
                            route_name,
                            subdomain=sub_url[hash(subpath) % len(sub_url)],
                            **kw)
                    else:
                        return request.route_url(route_name, **kw)
                else:
                    subpath = url_quote(subpath)
                    return urljoin(url, subpath)
        raise ValueError('No static URL definition matching %s' % path)

    def add(self, config, name, spec, **extra):
        if 'pregenerator' not in extra:
            extra['pregenerator'] = MultiDommainPregenerator()
        return super(MultiDommainStaticURLInfo, self) \
            .add(config, name, spec, **extra)
