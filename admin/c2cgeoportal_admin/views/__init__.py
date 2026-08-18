# Copyright (c) 2025-2026, Camptocamp SA
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

from typing import Any

import pyramid.httpexceptions
import pyramid.request
from pyramid.view import view_config


class IsAdminPredicate:
    """A custom predicate that checks if the request is for the admin interface."""

    def __init__(self, val: str, info: Any) -> None:
        del info

        self.val = val

    def text(self) -> str:
        return f"is_admin = {self.val}"

    phash = text

    def __call__(self, context: Any, request: pyramid.request.Request) -> bool:
        del context
        path = request.path
        assert isinstance(path, str)
        return path.startswith("/admin/") or path == "/admin"


@view_config(context=pyramid.httpexceptions.HTTPNotFound, is_admin=True, renderer="../templates/404.jinja2")  # type: ignore[untyped-decorator]
def _not_found_view(request=pyramid.request.Request) -> dict[str, str]:  # type: ignore[no-untyped-def] # noqa: ANN001
    del request

    return {}
