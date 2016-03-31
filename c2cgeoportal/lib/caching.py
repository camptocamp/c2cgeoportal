# -*- coding: utf-8 -*-

# Copyright (c) 2012-2016, Camptocamp SA
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


import inspect
import logging

from dogpile.cache import compat
from dogpile.cache.region import make_region

log = logging.getLogger(__name__)
_regions = {}


def keygen_function(namespace, fn):
    """Return a function that generates a string
    key, based on a given function as well as
    arguments to the returned function itself.

    This is used by :meth:`.CacheRegion.cache_on_arguments`
    to generate a cache key from a decorated function.
    """

    if namespace is None:
        namespace = "%s:%s" % (fn.__module__, fn.__name__)
    else:  # pragma: nocover
        namespace = "%s:%s|%s" % (fn.__module__, fn.__name__, namespace)

    args = inspect.getargspec(fn)
    has_self = args[0] and args[0][0] in ("self", "cls")

    def generate_key(*args, **kw):
        if kw:  # pragma: nocover
            raise ValueError(
                "key creation function does not accept keyword arguments.")
        parts = [namespace]
        if has_self:
            self_ = args[0]
            if hasattr(self_, "request"):
                parts.append(self_.request.application_url)
            args = args[1:]
        parts.append(" ".join(map(compat.text_type, args)))
        return "|".join(parts)
    return generate_key


def init_region(conf, region=None):
    """
    Initialize the caching module.
    """
    cache_region = make_region(function_key_generator=keygen_function)
    kwargs = dict(
        (k, conf[k]) for k in
        ("arguments", "expiration_time") if k in conf)
    cache_region.configure(conf["backend"], **kwargs)
    _regions[region] = cache_region
    return cache_region


def get_region(region=None):
    """
    Return a cache region.
    """
    try:
        return _regions[region]
    except KeyError:  # pragma: nocover
        raise Exception(
            "No such caching region. A region must be"
            "initialized before it can be used")


def invalidate_region(region=None):
    return get_region(region).invalidate()


NO_CACHE = 0
PUBLIC_CACHE = 1
PRIVATE_CACHE = 2

CORS_METHODS = "HEAD, GET, POST, PUT, DELETE"


def set_cors_headers(service_headers_settings, request, service_name,
                     credentials, response):
    """
    Handle CORS requests, as specified in http://www.w3.org/TR/cors/
    """
    if "Origin" not in request.headers:
        return  # Not a CORS request if this header is missing
    origin = request.headers["Origin"]

    if not service_headers_settings or \
            "access_control_allow_origin" not in service_headers_settings:
        log.warning("CORS query not configured for service=%s", service_name)
        return

    preflight = request.method == "OPTIONS"
    if preflight and "Access-Control-Request-Method" not in request.headers:
        log.warning("CORS preflight query missing the " +
                    "Access-Control-Request-Method header")
        return

    allowed_origins = service_headers_settings["access_control_allow_origin"]
    if origin not in allowed_origins:
        if "*" in allowed_origins:
            origin = "*"
            credentials = False  # Force no credentials
        else:
            log.warning("CORS query not allowed for origin=%s, service=%s", origin,
                        service_name)
            return

    response.headers.update({
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Methods": CORS_METHODS,
        "Vary": "Origin",
    })

    if preflight:
        max_age = service_headers_settings.get("access_control_max_age", 3600)
        response.headers["Access-Control-Max-Age"] = str(max_age)

    if credentials:
        response.headers["Access-Control-Allow-Credentials"] = "true"

    requested_headers = \
        request.headers.get("Access-Control-Request-Headers", False)
    if requested_headers:
        # For the moment, we allow all requested headers
        response.headers["Access-Control-Allow-Headers"] = requested_headers

    # If we start using headers in responses, we'll have to add
    # Access-Control-Expose-Headers


def set_common_headers(
        request, service_name, cache,
        response=None, credentials=True, vary=False, content_type=None):
    if response is None:
        response = request.response

    if cache == NO_CACHE:
        response.cache_control.no_cache = True
    elif cache == PUBLIC_CACHE:
        response.cache_control.public = True
    elif cache == PRIVATE_CACHE:
        if request.user is not None:
            response.cache_control.private = True
        else:
            response.cache_control.public = True
    else:  # pragma: nocover
        raise "Invalid cache type"

    if hasattr(request, "registry"):
        headers_settings = request.registry.settings.get("headers", {})
        service_headers_settings = headers_settings.get(service_name)

        if cache != NO_CACHE:
            max_age = request.registry.settings["default_max_age"]

            if service_headers_settings and \
                    "cache_control_max_age" in service_headers_settings:
                max_age = service_headers_settings["cache_control_max_age"]

            if max_age != 0:
                response.cache_control.max_age = max_age
            else:
                response.cache_control.no_cache = True

        set_cors_headers(
            service_headers_settings, request, service_name,
            credentials, response
        )

    if vary:
        response.headers["Vary"] = "Accept-Language"

    if content_type is not None:
        response.content_type = content_type

    return response
