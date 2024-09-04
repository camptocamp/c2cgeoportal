# Copyright (c) 2012-2024, Camptocamp SA
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
from enum import Enum
from typing import Any, cast

import pyramid.request
import pyramid.response

from c2cgeoportal_geoportal.lib import is_intranet

_LOG = logging.getLogger(__name__)


class Cache(Enum):
    """Enumeration for the possible cache values."""

    # For responses that do not depend on authentication
    PUBLIC = 0
    # For responses that do not depends on authentication
    # We use a small cache (e.g. 10s) instead of no cache to protect the service against too high traffic.
    PUBLIC_NO = 1
    # For responses that can depend on authentication
    PRIVATE = 2
    # See PUBLIC_NO and PRIVATE
    PRIVATE_NO = 3


CORS_METHODS = "HEAD, GET, POST, PUT, DELETE"


def _set_cors_headers(
    request: pyramid.request.Request,
    response: pyramid.response.Response,
    service_name: str,
    service_headers_settings: dict[str, Any],
    credentials: bool,
) -> None:
    """Handle CORS requests, as specified in https://www.w3.org/TR/cors/."""
    response.vary = (response.vary or ()) + ("Origin",)

    if "Origin" not in request.headers:
        return  # Not a CORS request if this header is missing
    origin = request.headers["Origin"]

    if request.method == "OPTIONS" and "Access-Control-Request-Method" not in request.headers:
        _LOG.warning("CORS preflight query missing the Access-Control-Request-Method header")
        return

    allowed_origins = cast(list[str], service_headers_settings.get("access_control_allow_origin", []))
    if origin not in allowed_origins:
        if "*" in allowed_origins:
            origin = "*"
            credentials = False  # Force no credentials
        else:
            _LOG.warning("CORS query not allowed for origin=%s, service=%s", origin, service_name)
            return

    response.headers.update(
        {"Access-Control-Allow-Origin": origin, "Access-Control-Allow-Methods": CORS_METHODS}
    )

    max_age = service_headers_settings.get("access_control_max_age", 3600)
    response.headers["Access-Control-Max-Age"] = str(max_age)

    if credentials:
        response.headers["Access-Control-Allow-Credentials"] = "true"

    if request.method != "OPTIONS":
        return

    response.cache_control.max_age = max_age

    if not service_headers_settings or "access_control_allow_origin" not in service_headers_settings:
        _LOG.warning("CORS query not configured for service=%s", service_name)
        return

    requested_headers = request.headers.get("Access-Control-Request-Headers", False)
    if requested_headers:
        # For the moment, we allow all requested headers
        response.headers["Access-Control-Allow-Headers"] = requested_headers

    # If we start using headers in responses, we'll have to add
    # Access-Control-Expose-Headers


def _set_common_headers(
    request: pyramid.request.Request,
    response: pyramid.response.Response,
    service_headers_settings: dict[str, dict[str, str]],
    cache: Cache,
    content_type: str | None,
) -> pyramid.response.Response:
    """Set the common headers."""

    response.headers.update(service_headers_settings.get("headers", {}))

    if cache in (Cache.PRIVATE, Cache.PRIVATE_NO):
        response.vary = (response.vary or ()) + ("Cookie",)

    maxage = (
        service_headers_settings.get("cache_control_max_age", 3600)
        if cache in (Cache.PUBLIC, Cache.PRIVATE)
        else service_headers_settings.get("cache_control_max_age_nocache", 10)
    )
    response.cache_control.max_age = maxage
    if maxage == 0:
        response.cache_control.no_cache = True
        response.cache_control.no_store = True
    elif cache in (Cache.PUBLIC, Cache.PUBLIC_NO):
        response.cache_control.public = True
    elif cache in (Cache.PRIVATE, Cache.PRIVATE_NO):
        if hasattr(request, "user") and request.user is not None or is_intranet(request):
            response.cache_control.private = True
        else:
            response.cache_control.public = True
    else:
        raise Exception("Invalid cache type")  # pylint: disable=broad-exception-raised

    if content_type is not None:
        response.content_type = content_type

    return response


def set_common_headers(
    request: pyramid.request.Request,
    service_name: str,
    cache: Cache,
    response: pyramid.response.Response = None,
    credentials: bool = True,
    content_type: str | None = None,
) -> pyramid.response.Response:
    """Set the common headers."""
    if response is None:
        response = request.response

    headers_settings = request.registry.settings.get("headers", {})
    service_headers_settings = headers_settings.get(service_name, {})

    _set_cors_headers(request, response, service_name, service_headers_settings, credentials)
    if request.method == "OPTIONS":
        return response
    return _set_common_headers(request, response, service_headers_settings, cache, content_type)
