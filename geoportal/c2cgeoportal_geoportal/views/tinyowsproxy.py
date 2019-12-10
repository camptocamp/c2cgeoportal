# -*- coding: utf-8 -*-

# Copyright (c) 2015-2019, Camptocamp SA
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

from defusedxml import ElementTree
from pyramid.httpexceptions import HTTPBadRequest, HTTPForbidden, HTTPUnauthorized
from pyramid.view import view_config

from c2cgeoportal_commons import models
from c2cgeoportal_commons.models import main
from c2cgeoportal_geoportal.lib.caching import NO_CACHE, PRIVATE_CACHE
from c2cgeoportal_geoportal.lib.filter_capabilities import (
    filter_wfst_capabilities,
    normalize_tag,
    normalize_typename,
)
from c2cgeoportal_geoportal.lib.layers import get_writable_layers
from c2cgeoportal_geoportal.views.ogcproxy import OGCProxy

LOG = logging.getLogger(__name__)


class TinyOWSProxy(OGCProxy):
    def __init__(self, request):
        OGCProxy.__init__(self, request, has_default_ogc_server=True)
        self.settings = request.registry.settings.get("tinyowsproxy", {})

        assert "tinyows_url" in self.settings, "tinyowsproxy.tinyows_url must be set"
        self.ogc_server = (
            models.DBSession.query(main.OGCServer)
            .filter(main.OGCServer.name == self.settings["ogc_server"])
            .one()
        )

        self.user = self.request.user

        # params hold the parameters we are going to send to TinyOWS
        self.lower_params = self._get_lower_params(dict(self.request.params))

    def _get_wfs_url(self):
        return self.settings.get("tinyows_url")

    @view_config(route_name="tinyowsproxy")
    def proxy(self):
        if self.user is None:
            raise HTTPUnauthorized(
                "Authentication required", headers=[("WWW-Authenticate", 'Basic realm="TinyOWS"')]
            )

        operation = self.lower_params.get("request")
        typenames = (
            set([normalize_typename(self.lower_params.get("typename"))])
            if "typename" in self.lower_params
            else set()
        )

        method = self.request.method
        if method == "POST":
            try:
                (operation, typenames_post) = self._parse_body(self.request.body)
            except Exception as exception:
                LOG.error("Error while parsing POST request body")
                LOG.exception(exception)
                raise HTTPBadRequest("Error parsing the request (see logs for more details)")

            typenames = typenames.union(typenames_post)

        if operation is None or operation == "":
            operation = "getcapabilities"

        if operation == "describefeaturetype":
            # for DescribeFeatureType we require that exactly one type-name
            # is given, otherwise we would have to filter the result
            if len(typenames) != 1:
                raise HTTPBadRequest(
                    "Exactly one type-name must be given for " "DescribeFeatureType requests"
                )

        if not self._is_allowed(typenames):
            raise HTTPForbidden("No access rights for at least one of the given type-names")

        # we want clients to cache GetCapabilities and DescribeFeatureType req.
        use_cache = method == "GET" and operation in ("getcapabilities", "describefeaturetype")
        cache_control = PRIVATE_CACHE if use_cache else NO_CACHE

        response = self._proxy_callback(
            operation,
            cache_control,
            url=self._get_wfs_url(),
            params=dict(self.request.params),
            cache=use_cache,
            headers=self._get_headers(),
            body=self.request.body,
        )
        return response

    def _is_allowed(self, typenames):
        """
        Checks if the current user has the rights to access the given
        type-names.
        """

        writable_layers = set()
        for gmflayer in list(get_writable_layers(self.request, [self.ogc_server.id]).values()):
            for ogclayer in gmflayer.layer.split(","):
                writable_layers.add(ogclayer.lower())
        return typenames.issubset(writable_layers)

    def _get_headers(self):
        headers = OGCProxy._get_headers(self)
        if "tinyows_host" in self.settings:
            headers["Host"] = self.settings.get("tinyows_host")
        return headers

    def _proxy_callback(self, operation, cache_control, *args, **kwargs):
        response = self._proxy(*args, **kwargs)
        content = response.content.decode()

        if operation == "getcapabilities":
            content = filter_wfst_capabilities(
                content, super(TinyOWSProxy, self)._get_wfs_url(), self.request
            )

        content = self._filter_urls(
            content, self.settings.get("online_resource"), self.settings.get("proxy_online_resource")
        )

        return self._build_response(response, content, cache_control, "tinyows")

    @staticmethod
    def _filter_urls(content, online_resource, proxy_online_resource):
        if online_resource is not None and proxy_online_resource is not None:
            return content.replace(online_resource, proxy_online_resource)
        return content

    @staticmethod
    def _parse_body(body):
        """
        Read the WFS-T request body and extract the referenced type-names
        and request method.
        """
        xml = ElementTree.fromstring(body)
        wfs_request = normalize_tag(xml.tag)

        # get the type names
        typenames = set()
        for child in xml:
            tag = normalize_tag(child.tag)
            if tag == "typename":
                typenames.add(child.text)
            elif tag in ("query", "lock", "update", "delete"):
                typenames.add(child.get("typeName"))
            elif tag == "insert":
                for insert_child in child:
                    typenames.add(normalize_tag(insert_child.tag))

        # remove the namespace from the typenames
        typenames = {normalize_typename(t) for t in typenames}

        return (wfs_request, typenames)
