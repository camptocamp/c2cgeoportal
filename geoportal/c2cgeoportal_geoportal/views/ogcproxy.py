# Copyright (c) 2011-2025, Camptocamp SA
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

import pyramid.request
from c2cgeoportal_commons.lib.url import Url, get_url2
from c2cgeoportal_commons.models import DBSession, main
from pyramid.httpexceptions import HTTPBadRequest
from sqlalchemy.orm.exc import NoResultFound  # type: ignore[attr-defined]

from c2cgeoportal_geoportal.lib.caching import get_region
from c2cgeoportal_geoportal.views.proxy import Proxy

_CACHE_REGION = get_region("std")
_LOG = logging.getLogger(__name__)


class OGCProxy(Proxy):
    """
    Proxy implementation that manly manage the ogcserver parameter.

    Then load the corresponding OGCServer.
    """

    def __init__(self, request: pyramid.request.Request, has_default_ogc_server: bool = False) -> None:
        Proxy.__init__(self, request)

        # params hold the parameters we"re going to send to backend
        self.params = dict(self.request.params)

        # reset possible value of role_id and user_id
        if "role_id" in self.params:
            del self.params["role_id"]
        if "user_id" in self.params:
            del self.params["user_id"]

        main_ogc_server = self.request.registry.settings.get("main_ogc_server")

        self.lower_params = self._get_lower_params(self.params)

        # We need original case for OGCSERVER parameter value
        self.lower_key_params = {k.lower(): v for k, v in self.params.items()}

        if "ogcserver" in request.matchdict:
            self.ogc_server = self._get_ogcserver_byname(request.matchdict["ogcserver"])
        elif "ogcserver" in self.lower_key_params:
            self.ogc_server = self._get_ogcserver_byname(self.lower_key_params["ogcserver"])
        elif main_ogc_server is not None:
            self.ogc_server = self._get_ogcserver_byname(main_ogc_server)
        elif not has_default_ogc_server:
            raise HTTPBadRequest("The querystring argument 'ogcserver' is required")

    @_CACHE_REGION.cache_on_arguments()
    def _get_ogcserver_byname(self, name: str) -> main.OGCServer:
        assert DBSession is not None

        try:
            result = DBSession.query(main.OGCServer).filter(main.OGCServer.name == name).one()
            DBSession.expunge(result)
        except NoResultFound:
            raise HTTPBadRequest(  # pylint: disable=raise-missing-from
                f"The OGC Server '{name}' does not exist (existing: "
                f"{','.join([t[0] for t in DBSession.query(main.OGCServer.name).all()])}).",
            )
        else:
            return result

    def _get_wms_url(self, errors: set[str]) -> Url | None:
        ogc_server = self.ogc_server
        url = get_url2(f"The OGC server '{ogc_server.name}'", ogc_server.url, self.request, errors)
        if errors:
            _LOG.error("\n".join(errors))
        return url

    def _get_wfs_url(self, errors: set[str]) -> Url | None:
        ogc_server = self.ogc_server
        url = get_url2(
            f"The OGC server (WFS) '{ogc_server.name}'",
            ogc_server.url_wfs or ogc_server.url,
            self.request,
            errors,
        )
        if errors:
            _LOG.error("\n".join(errors))
        return url

    def get_headers(self) -> dict[str, str]:
        headers: dict[str, str] = super().get_headers()
        if self.ogc_server.type == main.OGCSERVER_TYPE_QGISSERVER:
            if self.request.matched_route.name.endswith("_path"):
                headers["X-Qgis-Service-Url"] = self.request.current_route_url(path=[], _query={})
            else:
                headers["X-Qgis-Service-Url"] = self.request.current_route_url(
                    _query={"ogcserver": self.ogc_server.name},
                )
        return headers
