# Copyright (c) 2011-2024, Camptocamp SA
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
import ipaddress
import json
import logging
import re
from collections.abc import Iterable
from string import Formatter
from typing import Any, cast

import dateutil
import pyramid.request
import pyramid.response
from pyramid.interfaces import IRoutePregenerator
from zope.interface import implementer

from c2cgeoportal_commons.lib.url import get_url2
from c2cgeoportal_geoportal.lib.cacheversion import get_cache_version
from c2cgeoportal_geoportal.lib.caching import get_region

_LOG = logging.getLogger(__name__)
_CACHE_REGION = get_region("std")
_CACHE_REGION_OBJ = get_region("obj")


def get_types_map(types_array: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Get the type name of a metadata or a functionality."""
    return {type_["name"]: type_ for type_ in types_array}


def get_typed(
    name: str,
    value: str,
    types: dict[str, Any],
    request: pyramid.request.Request,
    errors: set[str],
    layer_name: str | None = None,
) -> str | int | float | bool | None | list[Any] | dict[str, Any]:
    """Get the typed (parsed) value of a metadata or a functionality."""
    prefix = f"Layer '{layer_name}': " if layer_name is not None else ""
    type_ = {"type": "not init"}
    try:
        if name not in types:
            errors.add(f"{prefix}Type '{name}' not defined.")
            return None
        type_ = types[name]
        if type_.get("type", "string") == "string":
            return value
        if type_["type"] == "list":
            return [v.strip() for v in value.split(",")]
        if type_["type"] == "boolean":
            value = value.lower()
            if value in ["yes", "y", "on", "1", "true"]:
                return True
            if value in ["no", "n", "off", "0", "false"]:
                return False
            errors.add(
                f"{prefix}The boolean attribute '{name}'='{value.lower()}' is not in "
                "[yes, y, on, 1, true, no, n, off, 0, false]."
            )
        elif type_["type"] == "integer":
            return int(value)
        elif type_["type"] == "float":
            return float(value)
        elif type_["type"] == "date":
            date = dateutil.parser.parse(value, default=datetime.datetime(1, 1, 1, 0, 0, 0))
            if date.time() != datetime.time(0, 0, 0):
                errors.add(f"{prefix}The date attribute '{name}'='{value}' should not have any time")
            else:
                return datetime.date.strftime(date.date(), "%Y-%m-%d")
        elif type_["type"] == "time":
            date = dateutil.parser.parse(value, default=datetime.datetime(1, 1, 1, 0, 0, 0))
            if date.date() != datetime.date(1, 1, 1):
                errors.add(f"{prefix}The time attribute '{name}'='{value}' should not have any date")
            else:
                return datetime.time.strftime(date.time(), "%H:%M:%S")
        elif type_["type"] == "datetime":
            date = dateutil.parser.parse(value, default=datetime.datetime(1, 1, 1, 0, 0, 0))
            return datetime.datetime.strftime(date, "%Y-%m-%dT%H:%M:%S")
        elif type_["type"] == "url":
            url = get_url2(f"{prefix}The attribute '{name}'", value, request, errors)
            return url.url() if url else ""
        elif type_["type"] == "json":
            try:
                return cast(dict[str, Any], json.loads(value))
            except Exception as e:  # pylint: disable=broad-exception-caught
                errors.add(f"{prefix}The attribute '{name}'='{value}' has an error: {str(e)}")
        elif type_["type"] == "regex":
            pattern = type_["regex"]
            if re.match(pattern, value) is None:
                errors.add(
                    f"{prefix}The regex attribute '{name}'='{value}' "
                    f"does not match expected pattern '{pattern}'."
                )
            else:
                return value
        else:
            errors.add(f"{prefix}Unknown type '{type_['type']}'.")
    except Exception as e:  # pylint: disable=broad-exception-caught
        errors.add(
            f"{prefix}Unable to parse the attribute '{name}'='{value}' with the type "
            f"'{type_.get('type', 'string')}', error:\n{e!s}"
        )
    return None


def get_setting(settings: Any, path: Iterable[str], default: Any = None) -> Any:
    """Get the settings."""
    value = settings
    for p in path:
        if value and p in value:
            value = value[p]
        else:
            return default
    return value if value else default


@_CACHE_REGION_OBJ.cache_on_arguments()
def get_ogc_server_wms_url_ids(request: pyramid.request.Request, host: str) -> dict[str, list[int]]:
    """Get the OGCServer ids mapped on the WMS URL."""
    from c2cgeoportal_commons.models import DBSession  # pylint: disable=import-outside-toplevel
    from c2cgeoportal_commons.models.main import OGCServer  # pylint: disable=import-outside-toplevel

    del host  # used for cache
    assert DBSession is not None

    errors: set[str] = set()
    servers: dict[str, list[int]] = {}
    for ogc_server in DBSession.query(OGCServer).all():
        url = get_url2(ogc_server.name, ogc_server.url, request, errors)
        if url is not None:
            servers.setdefault(url.url(), []).append(ogc_server.id)
    return servers


@_CACHE_REGION_OBJ.cache_on_arguments()
def get_ogc_server_wfs_url_ids(request: pyramid.request.Request, host: str) -> dict[str, list[int]]:
    """Get the OGCServer ids mapped on the WFS URL."""
    from c2cgeoportal_commons.models import DBSession  # pylint: disable=import-outside-toplevel
    from c2cgeoportal_commons.models.main import OGCServer  # pylint: disable=import-outside-toplevel

    del host  # used for cache
    assert DBSession is not None

    errors: set[str] = set()
    servers: dict[str, list[int]] = {}
    for ogc_server in DBSession.query(OGCServer).all():
        url = get_url2(ogc_server.name, ogc_server.url_wfs or ogc_server.url, request, errors)
        if url is not None:
            servers.setdefault(url.url(), []).append(ogc_server.id)
    return servers


@implementer(IRoutePregenerator)
class C2CPregenerator:
    """The custom pyramid pregenerator that manage the cache version."""

    def __init__(self, version: bool = True, role: bool = False):
        self.version = version
        self.role = role

    def __call__(self, request: pyramid.request.Request, elements: Any, kw: Any) -> tuple[Any, Any]:
        query = {**kw.get("_query", {})}

        if self.version:
            query["cache_version"] = get_cache_version()

        if self.role and request.user:
            # The templates change if the user is logged in or not. Usually it is
            # the role that is making a difference, but the username is put in
            # some JS files. So we add the username to hit different cache entries.
            query["username"] = request.user.username

        kw["_query"] = query
        return elements, kw


_formatter = Formatter()


@_CACHE_REGION_OBJ.cache_on_arguments()
def _get_intranet_networks(
    request: pyramid.request.Request,
) -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    return [
        ipaddress.ip_network(network, strict=False)
        for network in request.registry.settings.get("intranet", {}).get("networks", [])
    ]


@_CACHE_REGION.cache_on_arguments()
def get_role_id(name: str) -> int:
    """Get the role ID."""
    from c2cgeoportal_commons.models import DBSession, main  # pylint: disable=import-outside-toplevel

    assert DBSession is not None

    return cast(int, DBSession.query(main.Role.id).filter(main.Role.name == name).one()[0])


def get_roles_id(request: pyramid.request.Request) -> list[int]:
    """Get the user roles ID."""
    result = [get_role_id(request.get_organization_role("anonymous"))]
    if is_intranet(request):
        result.append(get_role_id(request.get_organization_role("intranet")))
    if request.user is not None:
        result.append(get_role_id(request.get_organization_role("registered")))
        result.extend([r.id for r in request.user.roles])
    return result


def get_roles_name(request: pyramid.request.Request) -> pyramid.response.Response:
    """Get the user roles name."""
    result = [request.get_organization_role("anonymous")]
    if is_intranet(request):
        result.append(request.get_organization_role("intranet"))
    if request.user is not None:
        result.append(request.get_organization_role("registered"))
        result.extend([r.name for r in request.user.roles])
    return result


def is_intranet(request: pyramid.request.Request) -> bool:
    """Get if it's an intranet user."""
    address = ipaddress.ip_address(request.client_addr)
    for network in _get_intranet_networks(request):
        if address in network:
            return True
    return False
