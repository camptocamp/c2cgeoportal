# Copyright (c) 2012-2023, Camptocamp SA
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
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

import pyramid.interfaces
import sqlalchemy.ext.declarative
import zope.interface
from dogpile.cache.api import NO_VALUE, CacheBackend
from dogpile.cache.backends.memory import MemoryBackend
from dogpile.cache.backends.redis import RedisBackend, RedisSentinelBackend
from dogpile.cache.region import CacheRegion, make_region
from dogpile.cache.util import sha1_mangle_key
from sqlalchemy.orm.util import identity_key

from c2cgeoportal_commons.models import Base

if TYPE_CHECKING:
    from dogpile.cache.api import SerializedReturnType
else:
    SerializedReturnType = Any

LOG = logging.getLogger(__name__)
_REGION: Dict[str, Any] = {}
MEMORY_CACHE_DICT: Dict[str, Any] = {}


def map_dbobject(
    item: sqlalchemy.ext.declarative.ConcreteBase,
) -> sqlalchemy.ext.declarative.ConcreteBase:
    """Get an cache identity key for the cache."""
    return identity_key(item) if isinstance(item, Base) else item


def keygen_function(namespace: Any, function: Callable[..., Any]) -> Callable[..., str]:
    """
    Return a function that generates a string key.

    Based on a given function as well as arguments to the returned function itself.

    This is used by :meth:`.CacheRegion.cache_on_arguments` to generate a cache key from a decorated function.
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
        new_args: List[str] = [
            arg for arg in args if pyramid.interfaces.IRequest not in zope.interface.implementedBy(type(arg))
        ]
        parts.extend(map(str, map(map_dbobject, new_args)))
        return "|".join(parts)

    return generate_key


def init_region(conf: Dict[str, Any], region: str) -> CacheRegion:
    """Initialize the caching module."""
    cache_region = get_region(region)
    _configure_region(conf, cache_region)
    return cache_region


def _configure_region(conf: Dict[str, Any], cache_region: CacheRegion) -> None:
    kwargs: Dict[str, Any] = {"replace_existing_backend": True}
    backend = conf["backend"]
    kwargs.update({k: conf[k] for k in conf if k != "backend"})
    kwargs.setdefault("arguments", {}).setdefault("cache_dict", MEMORY_CACHE_DICT)
    cache_region.configure(backend, **kwargs)


def get_region(region: str) -> CacheRegion:
    """Return a cache region."""
    if region not in _REGION:
        _REGION[region] = make_region(function_key_generator=keygen_function)
    return _REGION[region]


def invalidate_region(region: Optional[str] = None) -> None:
    """Invalidate a cache region."""
    if region is None:
        for cache_region in _REGION.values():
            cache_region.invalidate()
    else:
        get_region(region).invalidate()


class HybridRedisBackend(CacheBackend):  # type: ignore
    """A Dogpile cache backend with a memory cache backend in front of a Redis backend for performance."""

    def __init__(self, arguments: Dict[str, Any]):
        self._use_memory_cache = not arguments.pop("disable_memory_cache", False)
        self._memory = MemoryBackend({"cache_dict": arguments.pop("cache_dict", {})})
        self._redis = RedisBackend(arguments)

    def get(self, key: str) -> SerializedReturnType:
        value = self._memory.get(key)
        if value == NO_VALUE:
            val = self._redis.get_serialized(sha1_mangle_key(key.encode()))
            if val in (None, NO_VALUE):
                return NO_VALUE
            value = self._redis.deserializer(val)
            if value != NO_VALUE and self._use_memory_cache:
                self._memory.set(key, value)
        return value

    def get_multi(self, keys: List[str]) -> List[SerializedReturnType]:
        return [self.get(key) for key in keys]

    def set(self, key: str, value: SerializedReturnType) -> None:
        if self._use_memory_cache:
            self._memory.set(key, value)
        self._redis.set_serialized(sha1_mangle_key(key.encode()), self._redis.serializer(value))

    def set_multi(self, mapping: Dict[str, SerializedReturnType]) -> None:
        for key, value in mapping.items():
            self.set(key, value)

    def delete(self, key: str) -> None:
        self._memory.delete(key)
        self._redis.delete(key)

    def delete_multi(self, keys: List[str]) -> None:
        self._memory.delete_multi(keys)
        self._redis.delete_multi(keys)


class HybridRedisSentinelBackend(HybridRedisBackend):
    """Same as HybridRedisBackend but using the Redis Sentinel."""

    def __init__(self, arguments: Dict[str, Any]):
        super().__init__(arguments)
        self._redis = RedisSentinelBackend(arguments)
