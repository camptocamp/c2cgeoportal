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


import datetime
import logging
from typing import Any, cast

import pyramid.request
from altcha import create_challenge, verify_solution
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.view import view_config

from c2cgeoportal_geoportal.lib.common_headers import Cache, set_common_headers

_LOGGER = logging.getLogger(__name__)


def _get_altcha_settings(request: pyramid.request.Request) -> dict[str, Any]:
    return cast("dict[str, Any]", request.registry.settings.get("altcha", {}))


@view_config(route_name="altcha_challenge", renderer="json")  # type: ignore[untyped-decorator]
def altcha_challenge(request: pyramid.request.Request) -> dict[str, Any]:
    """Return a new ALTCHA proof-of-work challenge."""
    settings = _get_altcha_settings(request)
    challenge = create_challenge(
        algorithm=settings.get("algorithm", "PBKDF2/SHA-256"),
        cost=settings.get("cost", 5000),
        expires_at=datetime.datetime.now(datetime.UTC)
        + datetime.timedelta(seconds=settings.get("expires_in", 300)),
        hmac_secret=settings.get("hmac_secret"),
    )
    set_common_headers(request, "altcha", Cache.PRIVATE_NO)
    return challenge.to_dict()


def verify_altcha_payload(request: pyramid.request.Request) -> None:
    """Verify the ALTCHA payload sent by the widget."""
    settings = _get_altcha_settings(request)
    payload = request.params.get("altcha")
    if not payload:
        raise HTTPBadRequest(detail="parameter missing: altcha")
    result = verify_solution(payload, settings.get("hmac_secret") or "")
    if not result.verified:
        _LOGGER.warning(
            "ALTCHA verification failed: expired=%s, invalid_signature=%s",
            result.expired,
            result.invalid_signature,
        )
        raise HTTPBadRequest(detail="Invalid ALTCHA")
