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


import logging
import re

import pyramid.request
import pyramid.response
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from c2cgeoportal_commons.lib.url import Url
from c2cgeoportal_geoportal.views.proxy import Proxy

logger = logging.getLogger(__name__)


class Dev(Proxy):
    """All the development views."""

    THEME_RE = re.compile(r"/theme/.*$")

    def __init__(self, request: pyramid.request.Request):
        super().__init__(request)
        self.dev_url = self.request.registry.settings["devserver_url"]

    @view_config(route_name="dev")  # type: ignore[misc]
    def dev(self) -> pyramid.response.Response:
        path = self.THEME_RE.sub("", self.request.path_info)
        if self.request.path.endswith("/dynamic.js"):
            return HTTPFound(location=self.request.route_url("dynamic", _query=self.request.params))
        return self._proxy_response("dev", Url(f"{self.dev_url.rstrip('/')}/{path.lstrip('/')}"))
