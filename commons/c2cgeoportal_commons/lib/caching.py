# Copyright (c) 2022, Camptocamp SA
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
from typing import Any, Callable, Dict, List

import sqlalchemy.ext.declarative
from dogpile.cache.region import CacheRegion, make_region
from pyramid.request import Request
from sqlalchemy.orm.util import identity_key

from c2cgeoportal_commons.models import Base

_LOG = logging.getLogger(__name__)
REGION: Dict[str, Any] = {}


def _keygen_function(namespace: Any, function: Callable[..., Any]) -> Callable[..., str]:
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
        new_args: List[str] = [arg for arg in args if not isinstance(arg, Request)]
        parts.extend(map(str, map(_map_dbobject, new_args)))
        return "|".join(parts)

    return generate_key


def _map_dbobject(
    item: sqlalchemy.ext.declarative.ConcreteBase,
) -> sqlalchemy.ext.declarative.ConcreteBase:
    """Get an cache identity key for the cache."""
    return identity_key(item) if isinstance(item, Base) else item


def get_region(region: str) -> CacheRegion:
    """Return a cache region."""
    if region not in REGION:
        REGION[region] = make_region(function_key_generator=_keygen_function)
    return REGION[region]
