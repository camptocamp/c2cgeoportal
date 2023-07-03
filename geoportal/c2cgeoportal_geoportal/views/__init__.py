# Copyright (c) 2011-2023, Camptocamp SA
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


import pyramid.config
import pyramid.request
from pyramid.httpexceptions import HTTPFound


def add_ending_slash(request: pyramid.request.Request) -> HTTPFound:
    """Add an ending slash view."""
    return HTTPFound(location=request.path + "/")


def add_redirect(config: pyramid.config.Configurator, name: str, from_: str, to: str) -> None:
    """Add a redirect view."""

    def redirect_view(request: pyramid.request.Request) -> HTTPFound:
        return HTTPFound(location=request.route_url(to))

    config.add_route(name, from_, request_method="GET")
    config.add_view(redirect_view, route_name=name)


def restrict_headers(headers: dict[str, str], whitelist: list[str], blacklist: list[str]) -> dict[str, str]:
    """
    Filter headers with a whitelist then a blacklist.

    Some default pyramid headers will be added back by pyramid.
    """
    if len(whitelist) > 0:
        headers = {key: value for key, value in headers.items() if key in whitelist}

    headers = {key: value for key, value in headers.items() if key not in blacklist}
    return headers
