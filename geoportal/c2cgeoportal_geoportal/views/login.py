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


import json
import logging
import secrets
import string
import sys
import urllib.parse
from typing import Any

import pkce
import pyotp
import pyramid.request
import pyramid.response
from pyramid.httpexceptions import (
    HTTPBadRequest,
    HTTPForbidden,
    HTTPFound,
    HTTPUnauthorized,
    exception_response,
)
from pyramid.response import Response
from pyramid.security import forget, remember
from pyramid.view import forbidden_view_config, view_config
from sqlalchemy.orm.exc import NoResultFound  # type: ignore[attr-defined]

import c2cgeoportal_commons.lib.url
from c2cgeoportal_commons import models
from c2cgeoportal_commons.lib.email_ import send_email_config
from c2cgeoportal_commons.models import static
from c2cgeoportal_geoportal import is_allowed_url, is_valid_referrer
from c2cgeoportal_geoportal.lib import get_setting, is_intranet, oauth2, oidc
from c2cgeoportal_geoportal.lib.common_headers import Cache, set_common_headers
from c2cgeoportal_geoportal.lib.functionality import get_functionality

_LOG = logging.getLogger(__name__)


class Login:
    """
    All the login, logout, oauth2, user information views.

    Also manage the 2fa.
    """

    def __init__(self, request: pyramid.request.Request):
        self.request = request
        self.settings = request.registry.settings
        self.lang = request.locale_name

        self.authentication_settings = self.settings.get("authentication", {})

        self.two_factor_auth = self.authentication_settings.get("two_factor", False)
        self.two_factor_issuer_name = self.authentication_settings.get("two_factor_issuer_name")

    def _functionality(self) -> dict[str, list[str | int | float | bool | list[Any] | dict[str, Any]]]:
        functionality = {}
        for func_ in get_setting(self.settings, ("functionalities", "available_in_templates"), []):
            functionality[func_] = get_functionality(func_, self.request, is_intranet(self.request))
        return functionality

    def _referrer_log(self) -> None:
        if not hasattr(self.request, "is_valid_referer"):
            self.request.is_valid_referer = is_valid_referrer(self.request)
        if not self.request.is_valid_referer:
            _LOG.info("Invalid referrer for %s: %s", self.request.path_qs, repr(self.request.referrer))

    @forbidden_view_config(renderer="login.html")  # type: ignore[misc]
    def loginform403(self) -> dict[str, Any] | pyramid.response.Response:
        if self.request.authenticated_userid is not None:
            return HTTPForbidden()

        if self.authentication_settings.get("openid_connect", {}).get("enabled", False):
            return HTTPFound(
                location=self.request.route_url(
                    "oidc_login",
                    _query={"came_from": f"{self.request.path}?{urllib.parse.urlencode(self.request.GET)}"},
                )
            )

        set_common_headers(self.request, "login", Cache.PRIVATE_NO)

        return {
            "lang": self.lang,
            "login_params": {"came_from": f"{self.request.path}?{urllib.parse.urlencode(self.request.GET)}"},
            "two_fa": self.two_factor_auth,
        }

    @view_config(route_name="loginform", renderer="login.html")  # type: ignore[misc]
    def loginform(self) -> dict[str, Any]:
        if self.authentication_settings.get("openid_connect", {}).get("enabled", False):
            raise HTTPBadRequest("View disabled by OpenID Connect")

        set_common_headers(self.request, "login", Cache.PUBLIC)

        return {
            "lang": self.lang,
            "login_params": {"came_from": self.request.params.get("came_from") or "/"},
            "two_fa": self.two_factor_auth,
        }

    @staticmethod
    def _validate_2fa_totp(user: static.User, otp: str) -> bool:
        if pyotp.TOTP(user.tech_data.get("2fa_totp_secret", "")).verify(otp):
            return True
        return False

    @view_config(route_name="login")  # type: ignore[misc]
    def login(self) -> pyramid.response.Response:
        assert models.DBSession is not None
        if self.authentication_settings.get("openid_connect", {}).get("enabled", False):
            raise HTTPBadRequest("View disabled by OpenID Connect")

        self._referrer_log()

        login = self.request.POST.get("login")
        password = self.request.POST.get("password")
        if login is None or password is None:
            raise HTTPBadRequest("'login' and 'password' should be available in request params.")
        username = self.request.registry.validate_user(self.request, login, password)
        user: static.User | None
        if username is not None:
            user = models.DBSession.query(static.User).filter(static.User.username == username).one()
            if self.two_factor_auth:
                if "2fa_totp_secret" not in user.tech_data:
                    user.is_password_changed = False
                if not user.is_password_changed:
                    user.tech_data["2fa_totp_secret"] = pyotp.random_base32()
                    if self.request.GET.get("type") == "oauth2":
                        raise HTTPFound(location=self.request.route_url("notlogin"))
                    return set_common_headers(
                        self.request,
                        "login",
                        Cache.PRIVATE_NO,
                        response=Response(
                            json.dumps(
                                {
                                    "username": user.username,
                                    "is_password_changed": False,
                                    "two_factor_enable": self.two_factor_auth,
                                    "two_factor_totp_secret": user.tech_data["2fa_totp_secret"],
                                    "otp_uri": pyotp.TOTP(user.tech_data["2fa_totp_secret"]).provisioning_uri(
                                        user.email, issuer_name=self.two_factor_issuer_name
                                    ),
                                }
                            ),
                            headers=(("Content-Type", "text/json"),),
                        ),
                    )
                otp = self.request.POST.get("otp")
                if otp is None:
                    raise HTTPBadRequest("The second factor is missing.")
                if not self._validate_2fa_totp(user, otp):
                    _LOG.info("The second factor is wrong for user '%s'.", user.username)
                    raise HTTPUnauthorized("See server logs for details")
            user.update_last_login()
            user.tech_data["consecutive_failed"] = "0"

            if not user.is_password_changed:
                if self.request.GET.get("type") == "oauth2":
                    raise HTTPFound(location=self.request.route_url("notlogin"))
                return set_common_headers(
                    self.request,
                    "login",
                    Cache.PRIVATE_NO,
                    response=Response(
                        json.dumps(
                            {
                                "username": user.username,
                                "is_password_changed": False,
                                "two_factor_enable": self.two_factor_auth,
                            }
                        ),
                        headers=(("Content-Type", "text/json"),),
                    ),
                )

            _LOG.info("User '%s' logged in.", username)
            if self.request.GET.get("type") == "oauth2":
                self._oauth2_login(user)

            headers = remember(self.request, username)

            came_from = self.request.params.get("came_from")
            if came_from:
                if not came_from.startswith("/"):
                    allowed_hosts = self.request.registry.settings.get("authorized_referers", [])
                    came_from_hostname, ok = is_allowed_url(self.request, came_from, allowed_hosts)
                    if not ok:
                        message = (
                            f"Invalid hostname '{came_from_hostname}' in 'came_from' parameter, "
                            f"is not the current host '{self.request.host}' "
                            f"or part of allowed hosts: {', '.join(allowed_hosts)}"
                        )
                        _LOG.debug(message)
                        return HTTPBadRequest(message)
                return HTTPFound(location=came_from, headers=headers)

            headers.append(("Content-Type", "text/json"))
            return set_common_headers(
                self.request,
                "login",
                Cache.PRIVATE_NO,
                response=Response(json.dumps(self._user(self.request.get_user(username))), headers=headers),
            )
        user = models.DBSession.query(static.User).filter(static.User.username == login).one_or_none()
        if user and not user.deactivated:
            if "consecutive_failed" not in user.tech_data:
                user.tech_data["consecutive_failed"] = "0"
            user.tech_data["consecutive_failed"] = str(int(user.tech_data["consecutive_failed"]) + 1)
            if int(user.tech_data["consecutive_failed"]) >= self.request.registry.settings.get(
                "authentication", {}
            ).get("max_consecutive_failures", sys.maxsize):
                user.deactivated = True
                user.tech_data["consecutive_failed"] = "0"

        if hasattr(self.request, "tm"):
            self.request.tm.commit()
        raise HTTPUnauthorized("See server logs for details")

    def _oauth2_login(self, user: static.User) -> pyramid.response.Response:
        self.request.user_ = user
        _LOG.debug(
            "Call OAuth create_authorization_response with:\nurl: %s\nmethod: %s\nbody:\n%s",
            self.request.current_route_url(_query=self.request.GET),
            self.request.method,
            self.request.body,
        )
        headers, body, status = oauth2.get_oauth_client(
            self.request.registry.settings
        ).create_authorization_response(
            self.request.current_route_url(_query=self.request.GET),
            self.request.method,
            self.request.body,
            self.request.headers,
        )
        if hasattr(self.request, "tm"):
            self.request.tm.commit()
        _LOG.debug("OAuth create_authorization_response return\nstatus: %s\nbody:\n%s", status, body)

        location = headers.get("Location")
        location_hostname = urllib.parse.urlparse(location).hostname
        allowed_hosts = self.request.registry.settings.get("authentication", {}).get("allowed_hosts", [])
        location_hostname, ok = is_allowed_url(self.request, location, allowed_hosts)
        if not ok:
            message = (
                f"Invalid location hostname '{location_hostname}', "
                f"is not the current host '{self.request.host}' "
                f"or part of allowed_hosts: {', '.join(allowed_hosts)}"
            )
            _LOG.debug(message)
            return HTTPBadRequest(message)

        if status == 302:
            raise HTTPFound(location=location)
        if status != 200:
            if body:
                raise exception_response(status, details=body)
            raise exception_response(status)
        return set_common_headers(
            self.request,
            "login",
            Cache.PRIVATE_NO,
            response=Response(body, headers=headers.items()),
        )

    @view_config(route_name="logout")  # type: ignore[misc]
    def logout(self) -> pyramid.response.Response:
        if self.authentication_settings.get("openid_connect", {}).get("enabled", False):
            client = oidc.get_oidc_client(self.request, self.request.host)
            if hasattr(client, "revoke_token"):
                user_info = json.loads(self.request.authenticated_userid)
                client.revoke_token(user_info["access_token"])
                if user_info.get("refresh_token") is not None:
                    client.revoke_token(user_info["refresh_token"])

        headers = forget(self.request)

        if not self.request.user:
            _LOG.info("Logout on non login user.")
            raise HTTPUnauthorized("See server logs for details")

        _LOG.info("User '%s' (%s) logging out.", self.request.user.username, self.request.user.id)

        headers.append(("Content-Type", "text/json"))
        return set_common_headers(
            self.request, "login", Cache.PRIVATE_NO, response=Response("true", headers=headers)
        )

    def _user(self, user: static.User | None = None) -> dict[str, Any]:
        result = {
            "functionalities": self._functionality(),
            "is_intranet": is_intranet(self.request),
            "login_type": (
                "oidc"
                if self.authentication_settings.get("openid_connect", {}).get("enabled", False)
                else "local"
            ),
        }
        if not self.authentication_settings.get("openid_connect", {}).get("enabled", False):
            result["two_factor_enable"] = self.two_factor_auth

        user = self.request.user if user is None else user
        if user is not None:
            result.update(
                {
                    "username": user.display_name,
                    "email": user.email,
                    "roles": [{"name": r.name, "id": r.id} for r in user.roles],
                }
            )
        return result

    @view_config(route_name="loginuser", renderer="json")  # type: ignore[misc]
    def loginuser(self) -> dict[str, Any]:
        _LOG.info("Client IP address: %s", self.request.client_addr)
        set_common_headers(self.request, "login", Cache.PRIVATE_NO)
        return self._user()

    @view_config(route_name="change_password", renderer="json")  # type: ignore[misc]
    def change_password(self) -> pyramid.response.Response:
        assert models.DBSession is not None

        if self.authentication_settings.get("openid_connect", {}).get("enabled", False):
            raise HTTPBadRequest("View disabled by OpenID Connect")

        set_common_headers(self.request, "login", Cache.PRIVATE_NO)

        login = self.request.POST.get("login")
        old_password = self.request.POST.get("oldPassword")
        new_password = self.request.POST.get("newPassword")
        new_password_confirm = self.request.POST.get("confirmNewPassword")
        otp = self.request.POST.get("otp")
        if new_password is None or new_password_confirm is None or old_password is None:
            raise HTTPBadRequest(
                "'oldPassword', 'newPassword' and 'confirmNewPassword' should be available in "
                "request params."
            )
        if self.two_factor_auth and otp is None:
            raise HTTPBadRequest("The second factor is missing.")
        if login is None and self.request.user is None:
            raise HTTPBadRequest("You should be logged in or 'login' should be available in request params.")
        if new_password != new_password_confirm:
            raise HTTPBadRequest("The new password and the new password confirmation do not match")

        if login is not None:
            user = models.DBSession.query(static.User).filter_by(username=login).one_or_none()
            if user is None:
                _LOG.info("The login '%s' does not exist.", login)
                raise HTTPUnauthorized("See server logs for details")

            if self.two_factor_auth:
                if not self._validate_2fa_totp(user, otp):
                    _LOG.info("The second factor is wrong for user '%s'.", login)
                    raise HTTPUnauthorized("See server logs for details")
        else:
            user = self.request.user

        assert user is not None
        if self.request.registry.validate_user(self.request, user.username, old_password) is None:
            _LOG.info("The old password is wrong for user '%s'.", user.username)
            raise HTTPUnauthorized("See server logs for details")

        user.password = new_password
        user.is_password_changed = True
        models.DBSession.flush()
        _LOG.info("Password changed for user '%s'", user.username)

        headers = remember(self.request, user.username)
        headers.append(("Content-Type", "text/json"))
        return set_common_headers(
            self.request,
            "login",
            Cache.PRIVATE_NO,
            response=Response(json.dumps(self._user(user)), headers=headers),
        )

    @staticmethod
    def generate_password() -> str:
        allchars = "".join(
            [
                string.ascii_letters * 2,
                string.digits * 2,
                string.punctuation,  # One time to have less punctuation char
            ]
        )
        return "".join(secrets.choice(allchars) for i in range(8))

    def _loginresetpassword(
        self,
    ) -> tuple[static.User | None, str | None, str | None, str | None]:
        assert models.DBSession is not None

        username = self.request.POST.get("login")
        if username is None:
            raise HTTPBadRequest("'login' should be available in request params.")
        try:
            user = models.DBSession.query(static.User).filter(static.User.username == username).one()
        except NoResultFound:
            return None, None, None, f"The login '{username}' does not exist."

        if user.email is None or user.email == "":
            return None, None, None, f"The user '{user.username}' has no registered email address."

        password = self.generate_password()
        user.set_temp_password(password)

        return user, username, password, None

    @view_config(route_name="loginresetpassword", renderer="json")  # type: ignore[misc]
    def loginresetpassword(self) -> dict[str, Any]:
        if self.authentication_settings.get("openid_connect", {}).get("enabled", False):
            raise HTTPBadRequest("View disabled by OpenID Connect")

        set_common_headers(self.request, "login", Cache.PRIVATE_NO)

        user, username, password, error = self._loginresetpassword()
        if error is not None:
            _LOG.info(error)
            return {"success": True}

        if user is None:
            _LOG.info("The user is not found without any error.")
            return {"success": True}

        if user.deactivated:
            _LOG.info("The user '%s' is deactivated", username)
            return {"success": True}

        send_email_config(
            self.request.registry.settings,
            "reset_password",
            user.email,
            user=username,
            password=password,
            application_url=self.request.route_url("base"),
            current_url=self.request.current_route_url(),
        )

        return {"success": True}

    @view_config(route_name="oauth2introspect")  # type: ignore[misc]
    def oauth2introspect(self) -> pyramid.response.Response:
        if self.authentication_settings.get("openid_connect", {}).get("enabled", False):
            raise HTTPBadRequest("View disabled by OpenID Connect")

        _LOG.debug(
            "Call OAuth create_introspect_response with:\nurl: %s\nmethod: %s\nbody:\n%s",
            self.request.current_route_url(_query=self.request.GET),
            self.request.method,
            self.request.body,
        )
        headers, body, status = oauth2.get_oauth_client(
            self.request.registry.settings
        ).create_introspect_response(
            self.request.current_route_url(_query=self.request.GET),
            self.request.method,
            self.request.body,
            self.request.headers,
        )
        _LOG.debug("OAuth create_introspect_response return status: %s", status)

        # All requests to /token will return a json response, no redirection.
        if status != 200:
            if body:
                raise exception_response(status, detail=body)
            raise exception_response(status)
        return set_common_headers(
            self.request,
            "login",
            Cache.PRIVATE_NO,
            response=Response(body, headers=headers.items()),
        )

    @view_config(route_name="oauth2token")  # type: ignore[misc]
    def oauth2token(self) -> pyramid.response.Response:
        if self.authentication_settings.get("openid_connect", {}).get("enabled", False):
            raise HTTPBadRequest("View disabled by OpenID Connect")

        _LOG.debug(
            "Call OAuth create_token_response with:\nurl: %s\nmethod: %s\nbody:\n%s",
            self.request.current_route_url(_query=self.request.GET),
            self.request.method,
            self.request.body,
        )
        headers, body, status = oauth2.get_oauth_client(self.request.registry.settings).create_token_response(
            self.request.current_route_url(_query=self.request.GET),
            self.request.method,
            self.request.body,
            self.request.headers,
            {},
        )
        _LOG.debug("OAuth create_token_response return status: %s", status)

        # All requests to /token will return a json response, no redirection.
        if status != 200:
            if body:
                raise exception_response(status, detail=body)
            raise exception_response(status)
        return set_common_headers(
            self.request,
            "login",
            Cache.PRIVATE_NO,
            response=Response(body, headers=headers.items()),
        )

    @view_config(route_name="oauth2revoke_token")  # type: ignore[misc]
    def oauth2revoke_token(self) -> pyramid.response.Response:
        if self.authentication_settings.get("openid_connect", {}).get("enabled", False):
            raise HTTPBadRequest("View disabled by OpenID Connect")

        _LOG.debug(
            "Call OAuth create_revocation_response with:\nurl: %s\nmethod: %s\nbody:\n%s",
            self.request.create_revocation_response(_query=self.request.GET),
            self.request.method,
            self.request.body,
        )
        headers, body, status = oauth2.get_oauth_client(
            self.request.registry.settings
        ).create_authorize_response(
            self.request.current_route_url(_query=self.request.GET),
            self.request.method,
            self.request.body,
            self.request.headers,
        )
        if status != 200:
            if body:
                raise exception_response(status, detail=body)
            raise exception_response(status)
        return set_common_headers(
            self.request,
            "login",
            Cache.PRIVATE_NO,
            response=Response(body, headers=headers.items()),
        )

    @view_config(route_name="oauth2loginform", renderer="login.html")  # type: ignore[misc]
    def oauth2loginform(self) -> dict[str, Any]:
        if self.authentication_settings.get("openid_connect", {}).get("enabled", False):
            raise HTTPBadRequest("View disabled by OpenID Connect")

        set_common_headers(self.request, "login", Cache.PUBLIC)

        if self.request.user:
            self._oauth2_login(self.request.user)

        login_param = {"type": "oauth2"}
        login_param.update(self.request.params)
        return {
            "lang": self.lang,
            "login_params": login_param,
            "two_fa": self.two_factor_auth,
        }

    @view_config(route_name="notlogin", renderer="notlogin.html")  # type: ignore[misc]
    def notlogin(self) -> dict[str, Any]:
        set_common_headers(self.request, "login", Cache.PUBLIC)

        return {"lang": self.lang}

    @view_config(route_name="oidc_login")  # type: ignore[misc]
    def oidc_login(self) -> pyramid.response.Response:
        client = oidc.get_oidc_client(self.request, self.request.host)
        if "came_from" in self.request.params:
            self.request.response.set_cookie(
                "came_from",
                self.request.params["came_from"],
                httponly=True,
                samesite="Lax",
                secure=True,
                domain=self.request.domain,
                max_age=600,
            )

        code_verifier, code_challenge = pkce.generate_pkce_pair()
        self.request.response.set_cookie(
            "code_verifier",
            code_verifier,
            httponly=True,
            samesite="Lax",
            secure=True,
            domain=self.request.domain,
            max_age=600,
        )
        self.request.response.set_cookie(
            "code_challenge",
            code_challenge,
            httponly=True,
            samesite="Lax",
            secure=True,
            domain=self.request.domain,
            max_age=600,
        )

        try:

            url = c2cgeoportal_commons.lib.url.Url(
                client.authorization_code_flow.start_authentication(
                    code_challenge=code_challenge,
                    code_challenge_method="S256",
                )
            )
            url.add_query(
                self.authentication_settings.get("openid_connect", {}).get("login_extra_params", {})
            )
            return HTTPFound(location=url.url(), headers=self.request.response.headers)
        finally:
            client.authorization_code_flow.code_challenge = ""

    @view_config(route_name="oidc_callback")  # type: ignore[misc]
    def oidc_callback(self) -> pyramid.response.Response:
        client = oidc.get_oidc_client(self.request, self.request.host)
        assert models.DBSession is not None

        token_response = client.authorization_code_flow.handle_authentication_result(
            "?" + urllib.parse.urlencode(self.request.params),
            code_verifier=self.request.cookies["code_verifier"],
            code_challenge=self.request.cookies["code_challenge"],
            code_challenge_method="S256",
        )
        self.request.response.delete_cookie("code_verifier")
        self.request.response.delete_cookie("code_challenge")

        remember_object = oidc.OidcRemember(self.request).remember(token_response, self.request.host)

        user: static.User | oidc.DynamicUser | None = self.request.get_user_from_remember(
            remember_object, update_create_user=True
        )
        if user is not None:
            self.request.user_ = user

        if "came_from" in self.request.cookies:
            came_from = self.request.cookies["came_from"]
            self.request.response.delete_cookie("came_from")

            return HTTPFound(location=came_from, headers=self.request.response.headers)

        if user is not None:
            return set_common_headers(
                self.request,
                "login",
                Cache.PRIVATE_NO,
                response=Response(
                    # TODO respect the user interface...
                    json.dumps(
                        {
                            "username": user.display_name,
                            "email": user.email,
                            "is_intranet": is_intranet(self.request),
                            "functionalities": self._functionality(),
                            "roles": [{"name": r.name, "id": r.id} for r in user.roles],
                        }
                    ),
                    headers=(("Content-Type", "text/json"),),
                ),
            )
        else:
            return HTTPUnauthorized("See server logs for details")
