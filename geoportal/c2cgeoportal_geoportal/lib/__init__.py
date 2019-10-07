# -*- coding: utf-8 -*-

# Copyright (c) 2011-2019, Camptocamp SA
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


import datetime
import json
import urllib.parse
from string import Formatter

import dateutil
from pyramid.interfaces import IRoutePregenerator
from zope.interface import implementer

from c2cgeoportal_geoportal.lib.caching import get_region

CACHE_REGION_OBJ = get_region('obj')


def get_types_map(types_array):
    return {type_["name"]: type_ for type_ in types_array}


def get_url2(name, url, request, errors):
    url_split = urllib.parse.urlsplit(url)
    if url_split.scheme == "":
        if url_split.netloc == "" and url_split.path not in ("", "/"):
            # Relative URL like: /dummy/static/url or dummy/static/url
            return urllib.parse.urlunsplit(url_split)
        errors.add(
            "{}='{}' is not an URL."
            .format(name, url)
        )
        return None
    elif url_split.scheme in ("http", "https"):
        if url_split.netloc == "":
            errors.add(
                "{}='{}' is not a valid URL."
                .format(name, url)
            )
            return None
        return urllib.parse.urlunsplit(url_split)
    elif url_split.scheme == "static":
        if url_split.path in ("", "/"):
            errors.add(
                "{}='{}' cannot have an empty path."
                .format(name, url)
            )
            return None
        proj = url_split.netloc
        package = request.registry.settings["package"]
        if proj in ("", "static"):
            proj = "/etc/geomapfish/static"
        elif ":" not in proj:
            if proj == "static-ngeo":
                errors.add(
                    "{}='{}' static-ngeo shouldn't be used out of webpack because it don't has "
                    "cache bustering.".format(name, url)
                )
            proj = "{}_geoportal:{}".format(package, proj)
        return request.static_url(
            "{}{}".format(proj, url_split.path)
        )
    elif url_split.scheme == "config":
        if url_split.netloc == "":
            errors.add(
                "{}='{}' cannot have an empty netloc."
                .format(name, url)
            )
            return None
        server = request.registry.settings.get("servers", {}).get(url_split.netloc)
        if server is None:
            errors.add(
                "{}: The server '{}' ({}) is not found in the config: [{}]".format(
                    name, url_split.netloc, url,
                    ', '.join(request.registry.settings.get("servers", {}).keys())
                )
            )
            return None
        if url_split.path != "":
            if server[-1] != "/":
                server += "/"
            url = urllib.parse.urljoin(server, url_split.path[1:])
        else:
            url = server
        return url if len(url_split.query) == 0 else "{}?{}".format(
            url, url_split.query,
        )


def get_typed(name, value, types, request, errors, layer_name=None):
    prefix = "Layer '{}': ".format(layer_name) if layer_name is not None else ""
    type_ = {
        "type": "not init"
    }
    try:
        if name not in types:
            errors.add("{}Type '{}' not defined.".format(prefix, name))
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
                    "{}The boolean attribute '{}'='{}' is not in "
                    "[yes, y, on, 1, true, no, n, off, 0, false].".format(
                        prefix, name, value.lower()
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
                errors.add("{}The date attribute '{}'='{}' should not have any time".format(
                    prefix, name, value,
                ))
            else:
                return datetime.date.strftime(
                    date.date(), "%Y-%m-%d"
                )
        elif type_["type"] == "time":
            date = dateutil.parser.parse(
                value, default=datetime.datetime(1, 1, 1, 0, 0, 0)
            )
            if date.date() != datetime.date(1, 1, 1):
                errors.add("{}The time attribute '{}'='{}' should not have any date".format(
                    prefix, name, value,
                ))
            else:
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
            return get_url2("{}The attribute '{}'".format(prefix, name), value, request, errors)
        elif type_["type"] == "json":
            try:
                return json.loads(value)
            except Exception as e:
                errors.append("{}The attribute '{}'='{}' has an error: {}".format(
                    prefix, name, value, str(e),
                ))
        else:
            errors.add("{}Unknown type '{}'.".format(prefix, type_["type"]))
    except Exception as e:
        errors.add(
            "{}Unable to parse the attribute '{}'='{}' with the type '{}', error:\n{}"
            .format(
                prefix, name, value, type_.get("type", "string"), str(e)
            )
        )
    return None


def add_url_params(url, params):
    if len(params) == 0:
        return url
    return add_spliturl_params(urllib.parse.urlsplit(url), params)


def add_spliturl_params(spliturl, params):
    query = dict([(k, v[-1]) for k, v in list(urllib.parse.parse_qs(spliturl.query).items())])
    for key, value in list(params.items()):
        query[key] = value

    return urllib.parse.urlunsplit((
        spliturl.scheme, spliturl.netloc, spliturl.path,
        urllib.parse.urlencode(query), spliturl.fragment
    ))


def get_setting(settings, path, default=None):
    value = settings
    for p in path:
        if value and p in value:
            value = value[p]
        else:
            return default
    return value if value else default


@CACHE_REGION_OBJ.cache_on_arguments()
def get_ogc_server_wms_url_ids(request):
    from c2cgeoportal_commons.models import DBSession
    from c2cgeoportal_commons.models.main import OGCServer

    errors = set()
    servers = dict()
    for ogc_server in DBSession.query(OGCServer).all():
        url = get_url2(ogc_server.name, ogc_server.url, request, errors)
        servers.setdefault(url, []).append(ogc_server.id)
    return servers


@CACHE_REGION_OBJ.cache_on_arguments()
def get_ogc_server_wfs_url_ids(request):
    from c2cgeoportal_commons.models import DBSession
    from c2cgeoportal_commons.models.main import OGCServer

    errors = set()
    servers = dict()
    for ogc_server in DBSession.query(OGCServer).all():
        url = get_url2(ogc_server.name, ogc_server.url_wfs or ogc_server.url, request, errors)
        servers.setdefault(url, []).append(ogc_server.id)
    return servers


@implementer(IRoutePregenerator)
class C2CPregenerator:  # pragma: no cover
    def __init__(self, version=True, role=False):
        self.version = version
        self.role = role

    def __call__(self, request, elements, kw):
        query = kw.get("_query", {})

        if self.version:
            from c2cgeoportal_geoportal.lib.cacheversion import get_cache_version
            query["cache_version"] = get_cache_version()

        if self.role and request.user:
            # The templates change if the user is logged in or not. Usually it is
            # the role that is making a difference, but the username is put in
            # some JS files. So we add the username to hit different cache entries.
            query["username"] = request.user.username

        kw["_query"] = query
        return elements, kw


_formatter = Formatter()
