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


import json
import logging
import urllib.parse

import pyramid.request
import pyramid.response
import requests
from pyramid.httpexceptions import HTTPBadGateway, HTTPFound
from pyramid.view import view_config

from c2cgeoportal_commons.lib.url import Url
from c2cgeoportal_geoportal.lib import is_intranet
from c2cgeoportal_geoportal.lib.caching import get_region
from c2cgeoportal_geoportal.lib.common_headers import Cache
from c2cgeoportal_geoportal.lib.functionality import get_functionality
from c2cgeoportal_geoportal.views.proxy import Proxy

_LOG = logging.getLogger(__name__)
_CACHE_REGION = get_region("std")


class PrintProxy(Proxy):
    """All the view concerned the print."""

    def __init__(self, request: pyramid.request.Request):
        Proxy.__init__(self, request)

    @view_config(route_name="printproxy_capabilities")  # type: ignore
    def capabilities(self) -> pyramid.response.Response:
        """Get print capabilities."""
        templates = get_functionality("print_template", self.request, is_intranet(self.request))

        # get query string
        params = dict(self.request.params)
        query_string = urllib.parse.urlencode(params)

        resp, content = self._capabilities(
            templates, query_string, self.request.method, self.request.referrer, self.request.host
        )

        response = self._build_response(resp, content, Cache.PRIVATE, "print")
        # Mapfish print will check the referrer header to return the capabilities.
        response.vary += ("Referrer", "Referer")
        return response

    @_CACHE_REGION.cache_on_arguments()
    def _capabilities(
        self, templates: list[str], query_string: dict[str, str], method: str, referrer: str, host: str
    ) -> tuple[requests.Response, str]:
        del query_string  # Just for caching
        del method  # Just for caching
        del referrer  # Just for caching
        del host  # Just for caching

        # Get URL
        _url = self.request.get_organization_print_url() + "/capabilities.json"

        response = self._proxy(Url(_url))
        response.raise_for_status()

        if self.request.method == "GET":
            try:
                capabilities = response.json()
            except json.decoder.JSONDecodeError:
                _LOG.exception("Unable to parse capabilities: %s", response.text)
                raise HTTPBadGateway(response.text)  # pylint: disable=raise-missing-from

            capabilities["layouts"] = list(
                layout for layout in capabilities["layouts"] if layout["name"] in templates
            )

            pretty = self.request.params.get("pretty", "false") == "true"
            content = json.dumps(
                capabilities, separators=None if pretty else (",", ":"), indent=4 if pretty else None
            )
        else:
            content = ""

        return response, content

    @view_config(route_name="printproxy_report_create")  # type: ignore
    def report_create(self) -> pyramid.response.Response:
        """Create PDF."""
        return self._proxy_response(
            "print",
            Url(
                f"{ self.request.get_organization_print_url()}/report.{self.request.matchdict.get('format')}"
            ),
        )

    @view_config(route_name="printproxy_status")  # type: ignore
    def status(self) -> pyramid.response.Response:
        """PDF status."""
        return self._proxy_response(
            "print",
            Url(
                f"{self.request.get_organization_print_url()}/status/{self.request.matchdict.get('ref')}.json"
            ),
        )

    @view_config(route_name="printproxy_cancel")  # type: ignore
    def cancel(self) -> pyramid.response.Response:
        """PDF cancel."""
        return self._proxy_response(
            "print",
            Url(f"{self.request.get_organization_print_url()}/cancel/{self.request.matchdict.get('ref')}"),
        )

    @view_config(route_name="printproxy_report_get")  # type: ignore
    def report_get(self) -> pyramid.response.Response:
        """Get the PDF."""
        url = Url(f"{self.request.get_organization_print_url()}/report/{self.request.matchdict.get('ref')}")
        if self.request.registry.settings.get("print_get_redirect", False):
            raise HTTPFound(location=url.url())
        return self._proxy_response("print", url)
