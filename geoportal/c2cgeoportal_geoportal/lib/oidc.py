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
from typing import TYPE_CHECKING, Any, NamedTuple, Optional, TypedDict, Union

import pyramid.request
import pyramid.response
import simple_openid_connect.client
import simple_openid_connect.data
from pyramid.httpexceptions import HTTPBadRequest, HTTPInternalServerError, HTTPUnauthorized
from pyramid.security import remember

from c2cgeoportal_geoportal.lib.caching import get_region

if TYPE_CHECKING:
    from c2cgeoportal_commons.models import main, static

_LOG = logging.getLogger(__name__)
_CACHE_REGION_OBJ = get_region("obj")


# User create on demand
class DynamicUser(NamedTuple):
    """
    User created dynamically.
    """

    id: int
    username: str
    display_name: str
    email: str
    settings_role: Optional["main.Role"]
    roles: list["main.Role"]


@_CACHE_REGION_OBJ.cache_on_arguments()
def get_oidc_client(request: pyramid.request.Request, host: str) -> simple_openid_connect.client.OpenidClient:
    """
    Get the OpenID Connect client from the request settings.
    """

    del host  # used for cache key

    authentication_settings = request.registry.settings.get("authentication", {})
    openid_connect = authentication_settings.get("openid_connect", {})
    if openid_connect.get("enabled", False) is not True:
        raise HTTPBadRequest("OpenID Connect not enabled")

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
    display_name: str | None
    email: str | None
    settings_role: str | None
    roles: list[str]


def get_remember_from_user_info(
    request: pyramid.request.Request, user_info: dict[str, Any], remember_object: OidcRememberObject
) -> None:
    """
    Fill the remember object from the user info.

    The remember object will be stored in a cookie to remember the user.

    :param user_info: The user info from the ID token or from the user info view according to the `query_user_info` configuration.
    :param remember_object: The object to fill, by default with the `username`, `email`, `settings_role` and `roles`,
        the corresponding field from `user_info` can be configured in `user_info_fields`.
    :param settings: The OpenID Connect configuration.
    """
    settings_fields = (
        request.registry.settings.get("authentication", {})
        .get("openid_connect", {})
        .get("user_info_fields", {})
    )

    for field_, default_field in (
        ("username", "sub"),
        ("display_name", "name"),
        ("email", "email"),
        ("settings_role", None),
        ("roles", None),
    ):
        user_info_field = settings_fields.get(field_, default_field)
        if user_info_field is not None:
            if user_info_field not in user_info:
                _LOG.error(
                    "Field '%s' not found in user info, available: %s.",
                    user_info_field,
                    ", ".join(user_info.keys()),
                )
                raise HTTPInternalServerError(f"Field '{user_info_field}' not found in user info.")
            remember_object[field_] = user_info[user_info_field]  # type: ignore[literal-required]


def get_user_from_remember(
    request: pyramid.request.Request, remember_object: OidcRememberObject, update_create_user: bool = False
) -> Union["static.User", DynamicUser] | None:
    """
    Create a user from the remember object filled from `get_remember_from_user_info`.

    :param remember_object: The object to fill, by default with the `username`, `email`, `settings_role` and `roles`.
    :param settings: The OpenID Connect configuration.
    :param update_create_user: If the user should be updated or created if it does not exist.
    """

    # Those imports are here to avoid initializing the models module before the database schema are
    # correctly initialized.
    from c2cgeoportal_commons import models  # pylint: disable=import-outside-toplevel
    from c2cgeoportal_commons.models import main, static  # pylint: disable=import-outside-toplevel

    assert models.DBSession is not None

    user: static.User | DynamicUser | None
    username = remember_object["username"]
    assert username is not None
    email = remember_object["email"]
    assert email is not None
    display_name = remember_object["display_name"] or email

    openid_connect_configuration = request.registry.settings.get("authentication", {}).get(
        "openid_connect", {}
    )
    provide_roles = openid_connect_configuration.get("provide_roles", False)
    if provide_roles is False:
        user_query = models.DBSession.query(static.User)
        match_field = openid_connect_configuration.get("match_field", "username")
        if match_field == "username":
            user_query = user_query.filter_by(username=username)
        elif match_field == "email":
            user_query = user_query.filter_by(email=email)
        else:
            raise HTTPInternalServerError(
                f"Unknown match_field: '{match_field}', allowed values are 'username' and 'email'"
            )
        user = user_query.one_or_none()
        if update_create_user is True:
            if user is not None:
                for field in openid_connect_configuration.get("update_fields", []):
                    if field == "username":
                        user.username = username
                    elif field == "display_name":
                        user.display_name = display_name
                    elif field == "email":
                        user.email = email
                    else:
                        raise HTTPInternalServerError(
                            f"Unknown update_field: '{field}', allowed values are 'username', 'display_name' and 'email'"
                        )
            elif openid_connect_configuration.get("create_user", False) is True:
                user = static.User(username=username, email=email, display_name=display_name)
                models.DBSession.add(user)
    else:
        user = DynamicUser(
            id=-1,
            username=username,
            display_name=display_name,
            email=email,
            settings_role=(
                models.DBSession.query(main.Role).filter_by(name=remember_object["settings_role"]).first()
                if remember_object.get("settings_role") is not None
                else None
            ),
            roles=[
                models.DBSession.query(main.Role).filter_by(name=role).one()
                for role in remember_object.get("roles", [])
            ],
        )
    return user


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
        host: str,
    ) -> OidcRememberObject:
        """
        Remember the user in the cookie.
        """

        del host  # Used for cache key

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
            "display_name": None,
            "email": None,
            "settings_role": None,
            "roles": [],
        }
        client = get_oidc_client(self.request, self.request.host)

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

        self.request.get_remember_from_user_info(user_info.dict(), remember_object)
        self.request.response.headers.extend(remember(self.request, json.dumps(remember_object)))

        return remember_object


def includeme(config: pyramid.config.Configurator) -> None:
    """
    Pyramid includeme function.
    """
    config.add_request_method(get_remember_from_user_info, name="get_remember_from_user_info")
    config.add_request_method(get_user_from_remember, name="get_user_from_remember")
