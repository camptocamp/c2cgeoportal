# -*- coding: utf-8 -*-

# Copyright (c) 2012-2019, Camptocamp SA
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

from dogpile.cache.util import compat
from dogpile.cache.region import make_region
from pyramid.request import Request

log = logging.getLogger(__name__)
_regions = {}


def map_dbobject(item):
    # here to avoid import loop
    from c2cgeoportal_commons.models import Base

    return item.id if isinstance(item, Base) and hasattr(item, "id") else item


def keygen_function(namespace, function):
    """
    Return a function that generates a string
    key, based on a given function as well as
    arguments to the returned function itself.

    This is used by :meth:`.CacheRegion.cache_on_arguments`
    to generate a cache key from a decorated function.
    """

    if namespace is None:
        namespace = "{0!s}:{1!s}".format(function.__module__, function.__name__)
    else:  # pragma: no cover
        namespace = "{0!s}:{1!s}|{2!s}".format(function.__module__, function.__name__, namespace)

    args = inspect.getfullargspec(function)
    has_self = args[0] and args[0][0] in ("self", "cls")

    def generate_key(*args, **kw):
        if kw:  # pragma: no cover
            raise ValueError(
                "key creation function does not accept keyword arguments.")
        parts = [namespace]
        if has_self:
            args = args[1:]
        args = [arg for arg in args if not isinstance(arg, Request)]
        parts.extend(map(compat.text_type, map(map_dbobject, args)))
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
    except KeyError:  # pragma: no cover
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
    Handle CORS requests, as specified in https://www.w3.org/TR/cors/
    """
    if "Vary" not in response.headers:
        response.headers["Vary"] = set()
    response.headers["Vary"].add("Origin")

    if "Origin" not in request.headers:
        return  # Not a CORS request if this header is missing
    origin = request.headers["Origin"]

    if not service_headers_settings or \
            "access_control_allow_origin" not in service_headers_settings:
        log.warning("CORS query not configured for service=%s", service_name)
        return

    preflight = request.method == "OPTIONS"
    if preflight and "Access-Control-Request-Method" not in request.headers:
        log.warning("CORS preflight query missing the Access-Control-Request-Method header")
        return

    allowed_origins = service_headers_settings["access_control_allow_origin"]
    if origin not in allowed_origins:
        if "*" in allowed_origins:
            origin = "*"
            credentials = False  # Force no credentials
        else:
            log.warning(
                "CORS query not allowed for origin=%s, service=%s",
                origin, service_name
            )
            return

    response.headers.update({
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Methods": CORS_METHODS,
    })

    if preflight:
        max_age = service_headers_settings.get("access_control_max_age", 3600)
        response.headers["Access-Control-Max-Age"] = str(max_age)
        response.cache_control.max_age = max_age

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
    """
    Set the common headers
    vary: Vary on Accept-Language
    """
    if response is None:
        response = request.response

    if request.method != "OPTIONS":
        if cache == NO_CACHE:
            response.cache_control.no_cache = True
            response.cache_control.max_age = 0
        elif cache == PUBLIC_CACHE:
            response.cache_control.public = True
        elif cache == PRIVATE_CACHE:
            if request.user is not None:
                response.cache_control.private = True
            else:
                response.cache_control.public = True
        else:  # pragma: no cover
            raise "Invalid cache type"

    response.headers["Vary"] = set(["Accept-Encoding"])
    if hasattr(request, "registry"):
        headers_settings = request.registry.settings.get("headers", {})
        service_headers_settings = headers_settings.get(service_name, {})

        if cache != NO_CACHE and request.method != "OPTIONS":
            max_age = service_headers_settings.get("cache_control_max_age", 3600)

            response.cache_control.max_age = max_age
            if max_age == 0:
                response.cache_control.no_cache = True

        set_cors_headers(
            service_headers_settings, request, service_name,
            credentials, response
        )

    if vary and request.method != "OPTIONS":
        response.headers["Vary"].add("Accept-Language")

    response.headers["Vary"] = ", ".join(response.headers["Vary"])

    if content_type is not None and request.method != "OPTIONS":
        response.content_type = content_type

    return response
