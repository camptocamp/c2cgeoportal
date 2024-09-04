# Copyright (c) 2024, Camptocamp SA
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
import json
import logging
from typing import NamedTuple, TypedDict

import pyramid.request
import pyramid.response
import simple_openid_connect.client
import simple_openid_connect.data
from pyramid.httpexceptions import HTTPBadRequest, HTTPInternalServerError, HTTPUnauthorized
from pyramid.security import remember

from c2cgeoportal_commons.models import main
from c2cgeoportal_geoportal.lib.caching import get_region

_LOG = logging.getLogger(__name__)
_CACHE_REGION_OBJ = get_region("obj")


# User create on demand
class DynamicUser(NamedTuple):
    """
    User created dynamically.
    """

    username: str
    email: str
    settings_role: main.Role | None
    roles: list[main.Role]


@_CACHE_REGION_OBJ.cache_on_arguments()
def get_oidc_client(request: pyramid.request.Request) -> simple_openid_connect.client.OpenidClient:
    """
    Get the OpenID Connect client from the request settings.
    """

    authentication_settings = request.registry.settings.get("authentication", {})
    openid_connect = authentication_settings.get("openid_connect", {})
    if openid_connect.get("enabled", False) is not True:
        raise HTTPBadRequest("OpenID Connect not enabled")

    _LOG.info(openid_connect)
    return simple_openid_connect.client.OpenidClient.from_issuer_url(
        url=openid_connect["url"],
        authentication_redirect_uri=request.route_url("oidc_callback"),
        client_id=openid_connect["client_id"],
        client_secret=openid_connect.get("client-secret"),
        scope=" ".join(openid_connect.get("scopes", ["openid", "profile", "email"])),
    )


class OidcRememberObject(TypedDict):
    """
    The JSON object that is stored in a cookie to remember the user.
    """

    access_token: str
    access_token_expires: str
    refresh_token: str | None
    refresh_token_expires: str | None
    username: str | None
    email: str | None
    settings_role: str | None
    roles: list[str]


class OidcRemember:
    """
    Build the abject that we want to remember in the cookie.
    """

    def __init__(self, request: pyramid.request.Request):
        self.request = request
        self.authentication_settings = request.registry.settings.get("authentication", {})

    @_CACHE_REGION_OBJ.cache_on_arguments()
    def remember(
        self,
        token_response: (
            simple_openid_connect.data.TokenSuccessResponse | simple_openid_connect.data.TokenErrorResponse
        ),
    ) -> OidcRememberObject:
        """
        Remember the user in the cookie.
        """
        if isinstance(token_response, simple_openid_connect.data.TokenErrorResponse):
            _LOG.warning(
                "OpenID connect connection error: %s [%s]",
                token_response.error_description,
                token_response.error_uri,
            )
            raise HTTPUnauthorized("See server logs for details")

        if not isinstance(token_response, simple_openid_connect.data.TokenSuccessResponse):
            _LOG.warning("OpenID connect connection error: %s", token_response)
            raise HTTPUnauthorized("See server logs for details")

        openid_connect = self.authentication_settings.get("openid_connect", {})
        remember_object: OidcRememberObject = {
            "access_token": token_response.access_token,
            "access_token_expires": (
                datetime.datetime.now() + datetime.timedelta(seconds=token_response.expires_in)
            ).isoformat(),
            "refresh_token": token_response.refresh_token,
            "refresh_token_expires": (
                None
                if token_response.refresh_expires_in is None
                else (
                    datetime.datetime.now() + datetime.timedelta(seconds=token_response.refresh_expires_in)
                ).isoformat()
            ),
            "username": None,
            "email": None,
            "settings_role": None,
            "roles": [],
        }
        settings_fields = openid_connect.get("user_info_fields", {})
        client = get_oidc_client(self.request)

        if openid_connect.get("query_user_info", False) is True:
            user_info = client.fetch_userinfo(token_response.access_token)
        else:
            un_validated_user_info = simple_openid_connect.data.IdToken.parse_jwt(
                token_response.id_token, client.provider_keys
            )
            _LOG.info(
                "Receive audiences: %s",
                (
                    un_validated_user_info.aud
                    if isinstance(un_validated_user_info.aud, str)
                    else ", ".join(un_validated_user_info.aud)
                ),
            )
            user_info = client.decode_id_token(
                token_response.id_token,
                extra_trusted_audiences=openid_connect.get(
                    "trusted_audiences", [openid_connect.get("client_id")]
                ),
            )

        for field_, default_field in (
            ("username", "name"),
            ("email", "email"),
            ("settings_role", None),
            ("roles", None),
        ):
            user_info_field = settings_fields.get(field_, default_field)
            if user_info_field is not None:
                user_info_dict = user_info.dict()
                if user_info_field not in user_info_dict:
                    _LOG.error(
                        "Field '%s' not found in user info, available: %s.",
                        user_info_field,
                        ", ".join(user_info_dict.keys()),
                    )
                    raise HTTPInternalServerError(f"Field '{user_info_field}' not found in user info.")
                remember_object[field_] = user_info_dict[user_info_field]  # type: ignore[literal-required]

        self.request.response.headers.extend(remember(self.request, json.dumps(remember_object)))

        return remember_object
