# -*- coding: utf-8 -*-

# Copyright (c) 2011-2016, Camptocamp SA
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


import re
import urlparse
import datetime
import dateutil
from urlparse import urlsplit, urlunsplit, urljoin
from urllib import quote

from pyramid.interfaces import IRoutePregenerator, IStaticURLInfo
from zope.interface import implementer
from pyramid.compat import WIN
from pyramid.config.views import StaticURLInfo


def get_types_map(types_array):
    types_map = {}
    for type_ in types_array:
        if isinstance(type_, basestring):
            types_map[type_] = {
                "name": type_,
            }
        else:
            types_map[type_["name"]] = type_
    return types_map


def get_url(url, request, default=None, errors=None):
    if url is None:
        return default

    if re.match("^[a-z]*://", url) is None:
        return url

    obj = urlsplit(url)
    if obj.scheme == "static":
        netloc = obj.netloc
        if netloc == "":
            netloc = "c2cgeoportal:project"

        return request.static_url(netloc + obj.path)

    if obj.scheme == "config":
        server = request.registry.settings.get("servers", {}).get(obj.netloc, None)
        if server is None:
            if default is None and errors is not None:
                errors.add("The server '%s' isn't found in the config" % obj.netloc)
            return default
        else:
            return "%s%s?%s" % (server, obj.path, obj.query)

    else:
        return url


def get_url2(name, value, request, errors):
    url = urlparse.urlsplit(value)
    if url.scheme == "":
        if url.netloc == "" and url.path not in ("", "/"):
            # Relative URL like: /dummy/static/url or dummy/static/url
            return urlparse.urlunsplit(url)
        errors.add(
            "The attribute '{}'='{}' isn't an URL."
            .format(name, value)
        )
        return None
    elif url.scheme in ("http", "https"):
        if url.netloc == "":
            errors.add(
                "The attribute '{}'='{}' isn't a valid URL."
                .format(name, value)
            )
            return None
        return urlparse.urlunsplit(url)
    elif url.scheme == "static":
        if url.path in ("", "/"):
            errors.add(
                "The attribute '{}'='{}' can't have an empty path."
                .format(name, value)
            )
            return None
        proj = url.netloc
        package = request.registry.settings["package"]
        if proj == "":
            proj = "{}:static".format(package)
        elif ":" not in proj:
            proj = "{}:{}".format(package, proj)
        return request.static_url(
            "{}{}".format(proj, url.path)
        )
    elif url.scheme == "config":
        if url.netloc == "":
            errors.add(
                "The attribute '{}'='{}' can't have an empty netloc."
                .format(name, value)
            )
            return None
        server = request.registry.settings.get("servers", {}).get(url.netloc, None)
        if server is None:
            errors.add(
                "The server '{}' isn't found in the config".format(url.netloc)
            )
            return None
        return u"{}{}?{}".format(server, url.path, url.query)


def get_typed(name, value, types, request, errors):
    try:
        if name not in types:
            # ignore
            return None
        type_ = types[name]
        if type_.get("type", "string") == "string":
            return value
        elif type_["type"] == "list":
            return [v.strip() for v in value.split(",")]
        elif type_["type"] == "boolean":
            value = value.lower()
            if value in ["yes", "y", "on", "1", "true"]:
                return True
            elif value in ["no", "n", "off", "0", "false"]:
                return False
            else:
                errors.add(
                    "The boolean attribute '{}'='{}' is not in "
                    "[yes, y, on, 1, true, no, n, off, 0, false].".format(
                        name, value.lower()
                    )
                )
        elif type_["type"] == "integer":
            return int(value)
        elif type_["type"] == "float":
            return float(value)
        elif type_["type"] == "date":
            date = dateutil.parser.parse(
                value, default=datetime.datetime(1, 1, 1, 0, 0, 0)
            )
            if date.time() != datetime.time(0, 0, 0):
                errors.add("The date attribute '{}'='{}' shouldn't have any time")
                return None
            return datetime.date.strftime(
                date.date(), "%Y-%m-%d"
            )
        elif type_["type"] == "time":
            date = dateutil.parser.parse(
                value, default=datetime.datetime(1, 1, 1, 0, 0, 0)
            )
            if date.date() != datetime.date(1, 1, 1):
                errors.add("The time attribute '{}'='{}' shouldn't have any date")
                return None
            return datetime.time.strftime(
                date.time(), "%H:%M:%S"
            )
        elif type_["type"] == "datetime":
            date = dateutil.parser.parse(
                value, default=datetime.datetime(1, 1, 1, 0, 0, 0)
            )
            return datetime.datetime.strftime(
                date, "%Y-%m-%dT%H:%M:%S"
            )
        elif type_["type"] == "url":
            return get_url2(name, value, request, errors)
        else:
            errors.add("Unknown type '{}'.".format(type_["type"]))
    except Exception as e:
        errors.add(
            "Unable to parse the attribute '{}'='{}' with the type '{}', error:\n{}"
            .format(
                name, value, type_.get("type", "string"), str(e)
            )
        )
    return None


def add_url_params(url, params):
    return add_spliturl_params(urlsplit(url), params)


def add_spliturl_params(spliturl, params):
    query = []
    if spliturl.query != "":
        query.append(spliturl.query)
    query.extend(["%s=%s" % param for param in params.items()])

    return urlunsplit((
        spliturl.scheme, spliturl.netloc, spliturl.path,
        "&".join(query), spliturl.fragment
    ))


def get_setting(settings, path, default=None):
    value = settings
    for p in path:
        if value and p in value:
            value = value[p]
        else:
            return default
    return value if value else default


def _get_layers_query(role_id, what=None, version=1):
    from c2cgeoportal.models import DBSession, LayerV1, \
        Layer, RestrictionArea, Role, layer_ra, role_ra, \
        LayerWMS, LayerWMTS

    if version == 1:
        q = DBSession.query(what if what is not None else LayerV1)
    else:
        q = DBSession.query(Layer).with_polymorphic(
            [LayerWMS, LayerWMTS]
        )
    q = q.join(
        (layer_ra, Layer.id == layer_ra.c.layer_id),
        (RestrictionArea,
            RestrictionArea.id == layer_ra.c.restrictionarea_id),
        (role_ra, role_ra.c.restrictionarea_id == RestrictionArea.id),
        (Role, Role.id == role_ra.c.role_id))
    q = q.filter(Role.id == role_id)

    return q


def get_protected_layers_query(role_id, what=None, version=1):
    from c2cgeoportal.models import Layer
    q = _get_layers_query(role_id, what, version)
    return q.filter(Layer.public.is_(False))


def get_writable_layers_query(role_id, what=None, version=1):
    from c2cgeoportal.models import RestrictionArea
    q = _get_layers_query(role_id, what, version)
    return q.filter(RestrictionArea.readwrite.is_(True))


@implementer(IRoutePregenerator)
class C2CPregenerator:  # pragma: no cover
    def __init__(self, subdomain=False, version=True, role=False):
        self.subdomain = subdomain
        self.version = version
        self.role = role

    def __call__(self, request, elements, kw):
        if self.subdomain and "subdomain" in kw:
            if "subdomain_url_template" in request.registry.settings:
                subdomain_url_template = \
                    request.registry.settings["subdomain_url_template"]
            else:
                subdomain_url_template = "http://%(sub)s.%(host)s"

            kw["_app_url"] = subdomain_url_template % {
                "sub": kw["subdomain"],
                "host": request.host,
            } + request.script_name

        query = kw.get("_query", {})

        if self.version:
            from c2cgeoportal.lib.cacheversion import get_cache_version
            query["cache_version"] = get_cache_version()

        if self.role and request.user:
            # The templates change if the user is logged in or not. Usually it's
            # the role that is making a difference, but the username is put in
            # some JS files. So we add the username to hit different cache entries.
            query["username"] = request.user.username

        kw["_query"] = query
        return elements, kw


@implementer(IStaticURLInfo)
class MultiDomainStaticURLInfo(StaticURLInfo):  # pragma: no cover
    def generate(self, path, request, **kw):
        if WIN:
            path = path.replace("\\", "/")
        for (url, spec, route_name) in self.registrations:
            if WIN:
                spec = spec.replace("\\", "/")
            if path.startswith(spec):
                subpath = path[len(spec):]
                if self.cache_busters:
                    subpath, kw = self._bust_asset_path(
                        request, spec, subpath, kw)
                if url is None:
                    kw["subpath"] = subpath
                    if "subdomains" in request.registry.settings:
                        subdomains = request.registry.settings["subdomains"]
                        return request.route_url(
                            route_name,
                            subdomain=subdomains[hash(subpath) % len(subdomains)],
                            **kw
                        )
                    else:
                        return request.route_url(route_name, **kw)
                else:
                    subpath = quote(subpath)
                    return urljoin(url, subpath)
        raise ValueError("No static URL definition matching %s" % path)

    def add(self, config, name, spec, **extra):
        if "pregenerator" not in extra:
            extra["pregenerator"] = C2CPregenerator(subdomain=True, version=False)
        return super(MultiDomainStaticURLInfo, self) \
            .add(config, name, spec, **extra)
