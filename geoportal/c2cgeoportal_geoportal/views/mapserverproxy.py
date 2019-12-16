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


import logging
from typing import Any, Dict  # noqa, pylint: disable=unused-import

from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_config

from c2cgeoportal_commons.models import main
from c2cgeoportal_geoportal.lib import get_roles_id, get_roles_name
from c2cgeoportal_geoportal.lib.caching import NO_CACHE, PRIVATE_CACHE, PUBLIC_CACHE, get_region
from c2cgeoportal_geoportal.lib.filter_capabilities import filter_capabilities
from c2cgeoportal_geoportal.lib.functionality import get_mapserver_substitution_params
from c2cgeoportal_geoportal.views.ogcproxy import OGCProxy

CACHE_REGION = get_region("std")
LOG = logging.getLogger(__name__)


class MapservProxy(OGCProxy):

    params: Dict[str, str] = {}

    def __init__(self, request: Request) -> None:
        OGCProxy.__init__(self, request)
        self.user = self.request.user

    @view_config(route_name="mapserverproxy")
    @view_config(route_name="mapserverproxy_post")
    def proxy(self) -> Response:

        if self.user is None and "authentication_required" in self.request.params:
            LOG.debug("proxy() detected authentication_required")
            raise HTTPUnauthorized(headers={"WWW-Authenticate": 'Basic realm="Access to restricted layers"'})

        # We have a user logged in. We need to set group_id and possible layer_name in the params. We set
        # layer_name when either QUERY_PARAMS or LAYERS is set in the WMS params, i.e. for GetMap and
        # GetFeatureInfo requests. For GetLegendGraphic requests we do not send layer_name, but MapServer
        # should not use the DATA string for GetLegendGraphic.

        if self.ogc_server.auth == main.OGCSERVER_AUTH_STANDARD:
            self.params["role_ids"] = ",".join([str(e) for e in get_roles_id(self.request)])

            # In some application we want to display the features owned by a user than we need his id.
            self.params["user_id"] = self.user.id if self.user is not None else "-1"  # pragma: no cover

        # Do not allows direct variable substitution
        for k in list(self.params.keys()):
            if k[:2].capitalize() == "S_":
                LOG.warning("Direct substitution not allowed (%s=%s).", k, self.params[k])
                del self.params[k]

        # add functionalities params
        self.params.update(get_mapserver_substitution_params(self.request))

        # get method
        method = self.request.method

        # we want the browser to cache GetLegendGraphic and
        # DescribeFeatureType requests
        use_cache = False

        if method == "GET":
            # For GET requests, params are added only if the self.request
            # parameter is actually provided.
            if "request" not in self.lower_params:
                self.params = {}  # pragma: no cover
            else:
                if self.ogc_server.type != main.OGCSERVER_TYPE_QGISSERVER or "user_id" not in self.params:

                    use_cache = self.lower_params["request"] in ("getlegendgraphic",)

                    # no user_id and role_id or cached queries
                    if use_cache and "user_id" in self.params:
                        del self.params["user_id"]
                    if use_cache and "role_ids" in self.params:
                        del self.params["role_ids"]

            if "service" in self.lower_params and self.lower_params["service"] == "wfs":
                _url = self._get_wfs_url()
            else:
                _url = self._get_wms_url()
        else:
            # POST means WFS
            _url = self._get_wfs_url()

        cache_control = PRIVATE_CACHE
        if method == "GET" and "service" in self.lower_params and self.lower_params["service"] == "wms":
            if self.lower_params.get("request") in ("getmap", "getfeatureinfo"):
                cache_control = NO_CACHE
            elif self.lower_params.get("request") == "getlegendgraphic":
                cache_control = PUBLIC_CACHE
        elif method == "GET" and "service" in self.lower_params and self.lower_params["service"] == "wfs":
            if self.lower_params.get("request") == "getfeature":
                cache_control = NO_CACHE
        elif method != "GET":
            cache_control = NO_CACHE

        headers = self._get_headers()
        # Add headers for Geoserver
        if self.ogc_server.auth == main.OGCSERVER_AUTH_GEOSERVER:
            headers["sec-username"] = self.user.username
            headers["sec-roles"] = ";".join(get_roles_name(self.request))

        response = self._proxy_callback(
            cache_control,
            url=_url,
            params=self.params,
            cache=use_cache,
            headers=headers,
            body=self.request.body,
        )

        if (
            self.lower_params.get("request") == "getmap"
            and not response.content_type.startswith("image/")
            and response.status_code < 400
        ):
            response.status_code = 400

        return response

    def _proxy_callback(self, cache_control: int, url: str, params: dict, **kwargs: Any) -> Response:
        response = self._proxy(url=url, params=params, **kwargs)

        content = response.content
        if self.lower_params.get("request") == "getcapabilities":
            content = filter_capabilities(
                response.text,
                self.lower_params.get("service") == "wms",
                url,
                self.request.headers,
                self.request,
            ).encode("utf-8")

        content_type = response.headers["Content-Type"]

        return self._build_response(response, content, cache_control, "mapserver", content_type=content_type)
