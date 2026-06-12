# Copyright (c) 2026, Camptocamp SA
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


import json
import logging
from typing import Any, cast

import pyramid.request
from pyramid.httpexceptions import (
    HTTPBadRequest,
    HTTPInternalServerError,
    HTTPRequestEntityTooLarge,
    HTTPUnauthorized,
)
from pyramid.view import view_config

from c2cgeoportal_commons import models
from c2cgeoportal_commons.models import static
from c2cgeoportal_geoportal.lib.common_headers import Cache, set_common_headers

_LOG = logging.getLogger(__name__)


class UserSettings:
    """User settings endpoint."""

    _SERVICE_NAME = "user_settings"
    _DEFAULT_MAX_PAYLOAD_SIZE = 65536
    _MAX_PAYLOAD_SIZE_CONFIG_NAME = "max_payload_size"

    def __init__(self, request: pyramid.request.Request) -> None:
        self.request = request
        self.config = self.request.registry.settings.get("user_settings", {})
        if not isinstance(self.config, dict):
            _LOG.error(
                "The 'user_settings' configuration should be a map, got %s", type(self.config).__name__
            )
            raise HTTPInternalServerError("Invalid 'user_settings' configuration.")

    def _get_user(self) -> static.User:
        user = cast("static.User | None", self.request.user)
        if user is None:
            raise HTTPUnauthorized("See server logs for details")
        return user

    @staticmethod
    def _parse_max_payload_size(raw_value: Any) -> int:
        if raw_value is None:
            return UserSettings._DEFAULT_MAX_PAYLOAD_SIZE
        try:
            value = int(raw_value)
        except (TypeError, ValueError) as exc:
            _LOG.exception("Invalid user_settings.max_payload_size value: %r", raw_value)
            raise HTTPInternalServerError("Invalid 'user_settings.max_payload_size' configuration.") from exc
        if value < 1:
            _LOG.error("user_settings.max_payload_size should be greater than 0, got %s", value)
            raise HTTPInternalServerError("Invalid 'user_settings.max_payload_size' configuration.")
        return value

    def _read_body_with_limit(self) -> bytes:
        max_payload_size = self._parse_max_payload_size(self.config.get(self._MAX_PAYLOAD_SIZE_CONFIG_NAME))
        if self.request.content_length is not None and self.request.content_length > max_payload_size:
            raise HTTPRequestEntityTooLarge("The payload is too large.")

        body = cast("bytes", self.request.body_file.read(max_payload_size + 1))
        if len(body) > max_payload_size:
            raise HTTPRequestEntityTooLarge("The payload is too large.")
        return body

    @view_config(route_name="user_settings_get", renderer="json")  # type: ignore[untyped-decorator]
    def get(self) -> dict[str, Any]:
        user = self._get_user()
        set_common_headers(self.request, self._SERVICE_NAME, Cache.PRIVATE_NO)
        return user.settings or {}

    @view_config(route_name="user_settings_update", renderer="json")  # type: ignore[untyped-decorator]
    def update(self) -> dict[str, Any]:
        assert models.DBSession is not None

        user = self._get_user()
        body = self._read_body_with_limit()
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise HTTPBadRequest("Body should be valid JSON.") from exc
        if not isinstance(payload, dict):
            raise HTTPBadRequest("Body should be a JSON object.")

        user.settings = payload
        models.DBSession.flush()

        set_common_headers(self.request, self._SERVICE_NAME, Cache.PRIVATE_NO)
        return user.settings
