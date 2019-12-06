# -*- coding: utf-8 -*-

# Copyright (c) 2018-2019, Camptocamp SA
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
import time
from typing import Any, Dict

from c2cwsgiutils import broadcast
from c2cwsgiutils.auth import auth_view
from c2cwsgiutils.debug import get_size
from pyramid.view import view_config

from c2cgeoportal_geoportal.lib.caching import MEMORY_CACHE_DICT
from c2cgeoportal_geoportal.views import raster

LOG = logging.getLogger(__name__)


@view_config(route_name="memory", renderer="fast_json")
def memory(request):
    auth_view(request)
    return _memory()


def _nice_type_name(obj, dogpile_cache=False):
    # See: https://dogpilecache.sqlalchemy.org/en/latest/api.html#dogpile.cache.api.CachedValue
    if dogpile_cache:
        obj, _ = obj
    type_ = type(obj)
    return "{}.{}".format(type_.__module__, type_.__name__)


def _process_dict(dict_, dogpile_cache=False):
    # Timeout after one minute, must be set to a bit less that the timeout of the broadcast
    timeout = time.monotonic() + 20

    return {
        "elements": sorted(
            [
                {
                    "key": key,
                    "type": _nice_type_name(value, dogpile_cache),
                    "repr": repr(value),
                    "id": id(value),
                    "size_kb": get_size(value) / 1024 if time.monotonic() < timeout else -1,
                }
                for key, value in dict_.items()
            ],
            key=lambda i: -i["size_kb"],
        ),
        "id": id(dict_),
        "size_kb": get_size(dict_) / 1024 if time.monotonic() < timeout else -1,
        "timeout": time.monotonic() > timeout,
    }


@broadcast.decorator(expect_answers=True, timeout=110)
def _memory() -> Dict[str, Any]:
    return {
        "raster_data": _process_dict(raster.Raster.data),
        "memory_cache": _process_dict(MEMORY_CACHE_DICT, True),
    }
