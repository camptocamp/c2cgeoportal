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

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest
from c2cgeoportal_geoportal.views.proxy import Proxy
from c2cgeoportal_geoportal.lib.caching import NO_CACHE

import ast

log = logging.getLogger(__name__)


class ResourceProxy(Proxy):

    def __init__(self, request):  # pragma: no cover
        Proxy.__init__(self, request)
        self.request = request
        self.settings = request.registry.settings.get("resourceproxy", {})

    @view_config(route_name="resourceproxy")
    def proxy(self):  # pragma: no cover
        target = self.request.params.get("target", "")
        targets = self.settings.get("targets", [])
        if target in targets:  # pragma: no cover
            url = targets[target]
            values = ast.literal_eval(self.request.params.get("values"))
            url = url % values

            resp, content = self._proxy(url=url)

            cache_control = NO_CACHE
            content_type = resp["content-type"]

            response = self._build_response(
                resp, content, cache_control, "externalresource",
                content_type=content_type
            )
            for header in response.headers.keys():
                if header not in self.settings["allowed_headers"]:
                    response.headers.pop(header)
            return response
        else:  # pragma: no cover
            log.warning("target url not found: {0!s}".format(target))
            return HTTPBadRequest("url not allowed")
