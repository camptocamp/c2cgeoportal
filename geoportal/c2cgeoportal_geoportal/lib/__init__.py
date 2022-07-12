# Copyright (c) 2011-2021, Camptocamp SA
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


import logging
from string import Formatter
from typing import Any, Dict, Iterable, List, Set, Tuple, cast

import pyramid.request
import pyramid.response
from pyramid.interfaces import IRoutePregenerator
from zope.interface import implementer

from c2cgeoportal_commons.lib import is_intranet
from c2cgeoportal_commons.lib.caching import get_region
from c2cgeoportal_commons.lib.url import get_url2
from c2cgeoportal_geoportal.lib.cacheversion import get_cache_version

LOG = logging.getLogger(__name__)
CACHE_REGION = get_region("std")
CACHE_REGION_OBJ = get_region("obj")


def get_setting(settings: Any, path: Iterable[str], default: Any = None) -> Any:
    """Get the settings."""
    value = settings
    for p in path:
        if value and p in value:
            value = value[p]
        else:
            return default
    return value if value else default


@CACHE_REGION_OBJ.cache_on_arguments()  # type: ignore
def get_ogc_server_wms_url_ids(request: pyramid.request.Request) -> Dict[str, List[int]]:
    """Get the OGCServer ids mapped on the WMS URL."""
    from c2cgeoportal_commons.models import DBSession  # pylint: disable=import-outside-toplevel
    from c2cgeoportal_commons.models.main import OGCServer  # pylint: disable=import-outside-toplevel

    errors: Set[str] = set()
    servers: Dict[str, List[int]] = {}
    for ogc_server in DBSession.query(OGCServer).all():
        url = get_url2(ogc_server.name, ogc_server.url, request, errors)
        if url is not None:
            servers.setdefault(url.url(), []).append(ogc_server.id)
    return servers


@CACHE_REGION_OBJ.cache_on_arguments()  # type: ignore
def get_ogc_server_wfs_url_ids(request: pyramid.request.Request) -> Dict[str, List[int]]:
    """Get the OGCServer ids mapped on the WFS URL."""
    from c2cgeoportal_commons.models import DBSession  # pylint: disable=import-outside-toplevel
    from c2cgeoportal_commons.models.main import OGCServer  # pylint: disable=import-outside-toplevel

    errors: Set[str] = set()
    servers: Dict[str, List[int]] = {}
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

    def __call__(self, request: pyramid.request.Request, elements: Any, kw: Any) -> Tuple[Any, Any]:
        query = kw.get("_query", {})

        if self.version:
            query["cache_version"] = get_cache_version()

        if self.role and request.user:
            # The templates change if the user is logged in or not. Usually it is
            # the role that is making a difference, but the username is put in
            # some JS files. So we add the username to hit different cache entries.
            query["username"] = request.user.username

        kw["_query"] = query
        return elements, kw


@CACHE_REGION.cache_on_arguments()  # type: ignore
def get_role_id(name: str) -> int:
    """Get the role ID."""
    from c2cgeoportal_commons.models import DBSession, main  # pylint: disable=import-outside-toplevel

    return cast(int, DBSession.query(main.Role.id).filter(main.Role.name == name).one()[0])


def get_roles_id(request: pyramid.request.Request) -> List[int]:
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
