# -*- coding: utf-8 -*-

# Copyright (c) 2013, Camptocamp SA
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
class MultiDomainPregenerator:
    def __call__(self, request, elements, kw):
        if 'subdomain' in kw:
            if 'subdomain_url_template' in request.registry.settings:
                subdomain_url_template = request.registry. \
                        settings['subdomain_url_template']
            else:
                subdomain_url_template = 'http://%(sub)s.%(host)s'

            kw['_app_url'] = subdomain_url_template % {
                'sub': kw['subdomain'],
                'host': request.host,
            } + request.script_name
        return elements, kw

@implementer(IStaticURLInfo)
class MultiDomainStaticURLInfo(StaticURLInfo):
    def generate(self, path, request, **kw):
        registry = request.registry
        for (url, spec, route_name) in self._get_registrations(registry):
            if path.startswith(spec):
                subpath = path[len(spec):]
                if WIN:
                    subpath = subpath.replace('\\', '/') # windows
                if url is None:
                    kw['subpath'] = subpath
                    if 'subdomains' in request.registry.settings:
                        subdomains = request.registry.settings['subdomains']
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
            extra['pregenerator'] = MultiDomainPregenerator()
        return super(MultiDomainStaticURLInfo, self) \
            .add(config, name, spec, **extra)
