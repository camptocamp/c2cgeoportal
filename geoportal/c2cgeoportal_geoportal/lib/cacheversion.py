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


import uuid
from collections.abc import Callable
from typing import Any
from urllib.parse import urljoin

import pyramid.registry
import pyramid.request
import pyramid.response

from c2cgeoportal_geoportal.lib.caching import get_region

CACHE_REGION = get_region("std")


@CACHE_REGION.cache_on_arguments()
def get_cache_version() -> str:
    """Return a cache version that is regenerate after each cache invalidation."""
    return uuid.uuid4().hex


def version_cache_buster(
    request: pyramid.request.Request, subpath: str, kw: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    """Join the cash buster version with the sub path."""
    del request  # unused
    return urljoin(get_cache_version() + "/", subpath), kw


class CachebusterTween:
    """Get back the cachebuster URL."""

    def __init__(
        self,
        handler: Callable[[pyramid.request.Request], pyramid.response.Response],
        registry: pyramid.registry.Registry,
    ):
        self.handler = handler
        self.cache_path = registry.settings["cache_path"]

    def __call__(self, request: pyramid.request.Request) -> pyramid.response.Response:
        path = request.path_info.split("/")
        if len(path) > 1 and path[1] in self.cache_path:
            # remove the cache buster
            path.pop(2)
            request.path_info = "/".join(path)

        return self.handler(request)
