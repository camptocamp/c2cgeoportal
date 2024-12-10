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


import ast
import logging

import pyramid.request
import pyramid.response
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.view import view_config

from c2cgeoportal_geoportal.lib.common_headers import Cache
from c2cgeoportal_geoportal.views.proxy import Proxy

_LOG = logging.getLogger(__name__)


class ResourceProxy(Proxy):
    """All the views concerned the resources (it's a kind of proxy)."""

    def __init__(self, request: pyramid.request.Request):
        Proxy.__init__(self, request)
        self.request = request
        self.settings = request.registry.settings.get("resourceproxy", {})

    @view_config(route_name="resourceproxy")  # type: ignore[misc]
    def proxy(self) -> pyramid.response.Response:
        target = self.request.params.get("target", "")
        targets = self.settings.get("targets", [])
        if target in targets:
            url = targets[target]
            values = ast.literal_eval(self.request.params.get("values"))
            url = url % values

            response = self._proxy(url=url)

            cache_control = Cache.PRIVATE_NO
            content_type = response.headers["Content-Type"]

            response = self._build_response(
                response, response.content, cache_control, "externalresource", content_type=content_type
            )
            for header in response.headers.keys():
                if header not in self.settings["allowed_headers"]:
                    response.headers.pop(header)
            return response
        _LOG.warning("Target URL not found: %s", target)
        return HTTPBadRequest("URL not allowed")
