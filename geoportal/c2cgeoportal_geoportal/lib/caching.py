# -*- coding: utf-8 -*-

# Copyright (c) 2012-2021, Camptocamp SA
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
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, cast

import pyramid.request
import pyramid.response
import sqlalchemy.ext.declarative.api
from dogpile.cache.api import NO_VALUE, SerializedReturnType
from dogpile.cache.backends.redis import RedisBackend, RedisSentinelBackend
from dogpile.cache.region import CacheRegion, make_region
from dogpile.cache.util import sha1_mangle_key
from pyramid.request import Request
from sqlalchemy.orm.util import identity_key

from c2cgeoportal_commons.models import Base

LOG = logging.getLogger(__name__)
_REGION: Dict[str, Any] = {}
MEMORY_CACHE_DICT: Dict[str, Any] = {}


def map_dbobject(
    item: sqlalchemy.ext.declarative.api.ConcreteBase,
) -> sqlalchemy.ext.declarative.api.ConcreteBase:

    return identity_key(item) if isinstance(item, Base) else item


def keygen_function(namespace: Any, function: Callable[..., Any]) -> Callable[..., str]:
    """
    Return a function that generates a string
    key, based on a given function as well as
    arguments to the returned function itself.

    This is used by :meth:`.CacheRegion.cache_on_arguments`
    to generate a cache key from a decorated function.
    """

    if namespace is None:
        namespace = (function.__module__, function.__name__)
    else:
        namespace = (function.__module__, function.__name__, namespace)

    args = inspect.getfullargspec(function)
    ignore_first_argument = args[0] and args[0][0] in ("self", "cls")

    def generate_key(*args: Any, **kw: Any) -> str:
        if kw:
            raise ValueError("key creation function does not accept keyword arguments.")
        parts: List[str] = []
        parts.extend(namespace)
        if ignore_first_argument:
            args = args[1:]
        new_args: List[str] = [arg for arg in args if not isinstance(arg, Request)]
        parts.extend(map(str, map(map_dbobject, new_args)))
        return "|".join(parts)

    return generate_key


def init_region(conf: Dict[str, Any], region: str) -> CacheRegion:
    """
    Initialize the caching module.
    """
    cache_region = get_region(region)
    _configure_region(conf, cache_region)
    return cache_region


def _configure_region(conf: Dict[str, Any], cache_region: CacheRegion) -> None:
    global MEMORY_CACHE_DICT
    kwargs: Dict[str, Any] = {"replace_existing_backend": True}
    backend = conf["backend"]
    kwargs.update({k: conf[k] for k in conf if k != "backend"})
    kwargs.setdefault("arguments", {})
    kwargs["arguments"]["cache_dict"] = MEMORY_CACHE_DICT
    cache_region.configure(backend, **kwargs)


def get_region(region: str) -> CacheRegion:
    """
    Return a cache region.
    """
    global _REGION
    if region not in _REGION:
        _REGION[region] = make_region(function_key_generator=keygen_function)
    return _REGION[region]


def invalidate_region(region: str = None) -> None:
    if region is None:
        for cache_region in _REGION.values():
            cache_region.invalidate()
    else:
        get_region(region).invalidate()


class HybridRedisBackend(RedisBackend):
    """
    A memory and redis backend
    """

    def __init__(self, arguments: Dict[str, Any]):
        self._cache: Dict[str, SerializedReturnType] = arguments.pop("cache_dict", {})
        self._use_memory_cache = not arguments.pop("disable_memory_cache", False)

        super().__init__(arguments)

    def get(self, key: str) -> SerializedReturnType:
        value = self._cache.get(key, NO_VALUE)
        if value == NO_VALUE:
            value = super().get(sha1_mangle_key(key.encode()))
        if value != NO_VALUE and self._use_memory_cache:
            self._cache[key] = value
        return value

    def get_multi(self, keys: List[str]) -> List[SerializedReturnType]:
        return [self.get(key) for key in keys]

    def set(self, key: str, value: SerializedReturnType) -> None:
        if self._use_memory_cache:
            self._cache[key] = value
        super().set(sha1_mangle_key(key.encode()), value)

    def set_multi(self, mapping: Dict[str, SerializedReturnType]) -> None:
        for key, value in mapping.items():
            self.set(key, value)

    def delete(self, key: str) -> None:
        self._cache.pop(key, None)
        super().delete(key)


class HybridRedisSentinelBackend(RedisSentinelBackend):
    """
    A memory and redis sentinel backend
    """

    def __init__(self, arguments: Dict[str, Any]):
        self._cache: Dict[str, SerializedReturnType] = arguments.pop("cache_dict", {})
        self._use_memory_cache = not arguments.pop("disable_memory_cache", False)

        super().__init__(arguments)

    def get(self, key: str) -> SerializedReturnType:
        value = self._cache.get(key, NO_VALUE)
        if value == NO_VALUE:
            value = super().get(sha1_mangle_key(key.encode()))
        if value != NO_VALUE and self._use_memory_cache:
            self._cache[key] = value
        return value

    def get_multi(self, keys: List[str]) -> List[SerializedReturnType]:
        return [self.get(key) for key in keys]

    def set(self, key: str, value: SerializedReturnType) -> None:
        if self._use_memory_cache:
            self._cache[key] = value
        super().set(sha1_mangle_key(key.encode()), value)

    def set_multi(self, mapping: Dict[str, SerializedReturnType]) -> None:
        for key, value in mapping.items():
            self.set(key, value)

    def delete(self, key: str) -> None:
        self._cache.pop(key, None)
        super().delete(key)


class Cache(Enum):
    NO = 0
    PUBLIC = 1
    PRIVATE = 2


CORS_METHODS = "HEAD, GET, POST, PUT, DELETE"


def _set_cors_headers(
    request: pyramid.request.Request,
    response: pyramid.response.Response,
    service_name: str,
    service_headers_settings: Dict[str, Any],
    credentials: bool,
) -> None:
    """
    Handle CORS requests, as specified in https://www.w3.org/TR/cors/
    """
    response.vary = (response.vary or ()) + ("Origin",)

    if "Origin" not in request.headers:
        return  # Not a CORS request if this header is missing
    origin = request.headers["Origin"]

    if request.method == "OPTIONS" and "Access-Control-Request-Method" not in request.headers:
        LOG.warning("CORS preflight query missing the Access-Control-Request-Method header")
        return

    allowed_origins = cast(List[str], service_headers_settings.get("access_control_allow_origin", []))
    if origin not in allowed_origins:
        if "*" in allowed_origins:
            origin = "*"
            credentials = False  # Force no credentials
        else:
            LOG.warning("CORS query not allowed for origin=%s, service=%s", origin, service_name)
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
        LOG.warning("CORS query not configured for service=%s", service_name)
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
    service_headers_settings: Dict[str, Dict[str, str]],
    cache: Cache,
    content_type: Optional[str],
) -> pyramid.response.Response:
    """
    Set the common headers
    """

    response.headers.update(service_headers_settings.get("headers", {}))

    if cache == Cache.NO:
        response.cache_control.no_cache = True
        response.cache_control.max_age = 0
    elif cache == Cache.PUBLIC:
        response.cache_control.public = True
    elif cache == Cache.PRIVATE:
        if request.user is not None:
            response.cache_control.private = True
        else:
            response.cache_control.public = True
    else:
        raise Exception("Invalid cache type")

    if cache != Cache.NO:
        max_age = service_headers_settings.get("cache_control_max_age", 3600)

        response.cache_control.max_age = max_age
        if max_age == 0:
            response.cache_control.no_cache = True

    if content_type is not None:
        response.content_type = content_type

    return response


def set_common_headers(
    request: pyramid.request.Request,
    service_name: str,
    cache: Cache,
    response: pyramid.response.Response = None,
    credentials: bool = True,
    content_type: str = None,
) -> pyramid.response.Response:
    """
    Set the common headers
    """
    if response is None:
        response = request.response

    headers_settings = request.registry.settings.get("headers", {})
    service_headers_settings = headers_settings.get(service_name, {})

    _set_cors_headers(request, response, service_name, service_headers_settings, credentials)
    if request.method == "OPTIONS":
        return response
    return _set_common_headers(request, response, service_headers_settings, cache, content_type)
