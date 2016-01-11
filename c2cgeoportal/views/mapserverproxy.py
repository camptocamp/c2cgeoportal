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


import logging

from pyramid.view import view_config

from c2cgeoportal.lib.caching import get_region, NO_CACHE, PUBLIC_CACHE, PRIVATE_CACHE
from c2cgeoportal.lib.functionality import get_mapserver_substitution_params
from c2cgeoportal.lib.filter_capabilities import filter_capabilities
from c2cgeoportal.views.proxy import Proxy

cache_region = get_region()
log = logging.getLogger(__name__)


class MapservProxy(Proxy):

    def __init__(self, request):
        Proxy.__init__(self, request)
        self.settings = request.registry.settings.get("mapserverproxy", {})

    def _get_wms_url(self):
        return self.settings.get("external_mapserv_url") if \
            self.external else \
            self.settings.get("mapserv_url")

    def _get_wfs_url(self):
        internal_url = self.settings.get(
            "mapserv_wfs_url",
            self.settings.get("mapserv_url")
        )
        external_url = self.settings.get(
            "external_mapserv_wfs_url",
            self.settings.get("external_mapserv_url")
        )
        return external_url if self.external else internal_url

    @view_config(route_name="mapserverproxy")
    def proxy(self):

        self.user = self.request.user
        self.external = bool(self.request.params.get("EXTERNAL", None))

        # params hold the parameters we"re going to send to MapServer
        params = dict(self.request.params)

        # reset possible value of role_id and user_id
        if "role_id" in params:  # pragma: no cover
            del params["role_id"]
        if "user_id" in params:  # pragma: no cover
            del params["user_id"]

        self.lower_params = self._get_lower_params(params)

        if self.user is not None and not self.settings["geoserver"]:
            # We have a user logged in. We need to set group_id and
            # possible layer_name in the params. We set layer_name
            # when either QUERY_PARAMS or LAYERS is set in the
            # WMS params, i.e. for GetMap and GetFeatureInfo
            # requests. For GetLegendGraphic requests we don't
            # send layer_name, but MapServer shouldn't use the DATA
            # string for GetLegendGraphic.

            params["role_id"] = self.user.parent_role.id if self.external else self.user.role.id

            # In some application we want to display the features owned by a user
            # than we need his id.
            if not self.external:
                params["user_id"] = self.user.id  # pragma: nocover

        # don't allows direct variable substitution
        for k in params.keys():
            if k[:2].capitalize() == "S_":
                log.warning("Direct substitution not allowed (%s=%s)." %
                            (k, params[k]))
                del params[k]

        # add functionalities params
        params.update(get_mapserver_substitution_params(self.request))

        # get method
        method = self.request.method

        # we want the browser to cache GetLegendGraphic and
        # DescribeFeatureType requests
        use_cache = False

        if method == "GET":
            # For GET requests, params are added only if the self.request
            # parameter is actually provided.
            if "request" not in self.lower_params:
                params = {}  # pragma: no cover
            else:
                use_cache = self.lower_params["request"] in (
                    u"getcapabilities",
                    u"getlegendgraphic",
                    u"describelayer",
                    u"describefeaturetype",
                )

                # no user_id and role_id or cached queries
                if use_cache and "user_id" in params:
                    del params["user_id"]
                if use_cache and "role_id" in params:
                    del params["role_id"]

            if "service" in self.lower_params and self.lower_params["service"] == u"wfs":
                _url = self._get_wfs_url()
            else:
                _url = self._get_wms_url()
        else:
            # POST means WFS
            _url = self._get_wfs_url()

        cache_control = PRIVATE_CACHE
        if method == "GET" and \
                "service" in self.lower_params and \
                self.lower_params["service"] == u"wms":
            if self.lower_params["request"] in (u"getmap", u"getfeatureinfo"):
                cache_control = NO_CACHE
            elif self.lower_params["request"] == u"getlegendgraphic":
                cache_control = PUBLIC_CACHE
        elif method == "GET" and \
                "service" in self.lower_params and \
                self.lower_params["service"] == u"wfs":
            if self.lower_params["request"] == u"getfeature":
                cache_control = NO_CACHE
        elif method != "GET":
            cache_control = NO_CACHE

        role = None if self.user is None else \
            self.user.parent_role if self.external else self.user.role

        headers = self._get_headers()
        # Add headers for Geoserver
        if self.settings["geoserver"] and self.user is not None:
            headers["sec-username"] = self.user.username
            headers["sec-roles"] = role.name

        response = self._proxy_callback(
            role.id if role is not None else None, cache_control,
            url=_url, params=params, cache=use_cache,
            headers=headers, body=self.request.body
        )
        return response

    def _proxy_callback(self, role_id, cache_control, *args, **kwargs):
        params = kwargs.get("params", {})
        callback = params.get("callback", None)
        if callback is not None:
            del params["callback"]
        resp, content = self._proxy(*args, **kwargs)

        if self.lower_params.get("request") == "getcapabilities":
            content = filter_capabilities(
                content, role_id, self.lower_params.get("service") == "wms",
                self._get_wms_url(),
                self.request.headers,
                self.settings.get("proxies", None)
            )

        content_type = None
        if callback is not None:
            content_type = "application/javascript"
            # escape single quotes in the JavaScript string
            content = unicode(content.decode("utf8"))
            content = content.replace(u"'", u"\\'")
            content = u"%s('%s');" % (callback, u" ".join(content.splitlines()))
        else:
            content_type = resp["content-type"]

        return self._build_response(
            resp, content, cache_control, "mapserver",
            content_type=content_type
        )
