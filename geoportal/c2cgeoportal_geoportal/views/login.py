# -*- coding: utf-8 -*-

# Copyright (c) 2011-2020, Camptocamp SA
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
from random import Random
import sys
from typing import Dict, Set, Tuple  # noqa # pylint: disable=unused-import
import xml.dom.minidom  # noqa # pylint: disable=unused-import

import pyotp
from pyramid.httpexceptions import HTTPBadRequest, HTTPForbidden, HTTPFound, HTTPUnauthorized
from pyramid.response import Response
from pyramid.security import forget, remember
from pyramid.view import view_config
from sqlalchemy.orm.exc import NoResultFound

from c2cgeoportal_commons import models
from c2cgeoportal_commons.lib.email_ import send_email_config
from c2cgeoportal_commons.models import static
from c2cgeoportal_geoportal import is_valid_referer
from c2cgeoportal_geoportal.lib import get_setting, is_intranet
from c2cgeoportal_geoportal.lib.caching import NO_CACHE, PUBLIC_CACHE, get_region, set_common_headers
from c2cgeoportal_geoportal.lib.functionality import get_functionality

LOG = logging.getLogger(__name__)
CACHE_REGION = get_region("std")


class Login:
    def __init__(self, request):
        self.request = request
        self.settings = request.registry.settings
        self.lang = request.locale_name

        authentication_settings = self.settings.get("authentication", {})
        self.two_factor_auth = authentication_settings.get("two_factor", False)
        self.two_factor_issuer_name = authentication_settings.get("two_factor_issuer_name")

    def _functionality(self):
        functionality = {}
        for func_ in get_setting(self.settings, ("functionalities", "available_in_templates"), []):
            functionality[func_] = get_functionality(func_, self.request, is_intranet(self.request))
        return functionality

    def _referer_log(self) -> None:
        if not hasattr(self.request, "is_valid_referer"):
            self.request.is_valid_referer = is_valid_referer(self.request)
        if not self.request.is_valid_referer:
            LOG.info("Invalid referer for %s: %s", self.request.path_qs, repr(self.request.referer))

    @view_config(context=HTTPForbidden, renderer="login.html")
    def loginform403(self):
        if self.request.authenticated_userid:
            return HTTPUnauthorized()  # pragma: no cover

        set_common_headers(self.request, "login", NO_CACHE)

        return {"lang": self.lang, "came_from": self.request.path, "two_fa": self.two_factor_auth}

    @view_config(route_name="loginform", renderer="login.html")
    def loginform(self):
        set_common_headers(self.request, "login", PUBLIC_CACHE)

        return {
            "lang": self.lang,
            "came_from": self.request.params.get("came_from") or "/",
            "two_fa": self.two_factor_auth,
        }

    @staticmethod
    def _validate_2fa_totp(user, otp: str) -> bool:
        if pyotp.TOTP(user.tech_data.get("2fa_totp_secret", "")).verify(otp):
            return True
        return False

    @view_config(route_name="login")
    def login(self):
        self._referer_log()

        login = self.request.POST.get("login")
        password = self.request.POST.get("password")
        if login is None or password is None:  # pragma nocover
            raise HTTPBadRequest("'login' and 'password' should be available in request params.")
        username = self.request.registry.validate_user(self.request, login, password)
        if username is not None:
            user = models.DBSession.query(static.User).filter(static.User.username == username).one()
            if self.two_factor_auth:
                if "2fa_totp_secret" not in user.tech_data:
                    user.is_password_changed = False
                if not user.is_password_changed:
                    user.tech_data["2fa_totp_secret"] = pyotp.random_base32()
                    return set_common_headers(
                        self.request,
                        "login",
                        NO_CACHE,
                        response=Response(
                            json.dumps(
                                {
                                    "username": user.username,
                                    "is_password_changed": False,
                                    "two_factor_enable": True,
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
                    LOG.info("The second factor is wrong for user '%s'.", user.username)
                    raise HTTPUnauthorized("See server logs for details")
            user.update_last_login()
            user.tech_data["consecutive_failed"] = "0"

            if not user.is_password_changed:
                return set_common_headers(
                    self.request,
                    "login",
                    NO_CACHE,
                    response=Response(
                        json.dumps(
                            {
                                "username": user.username,
                                "is_password_changed": False,
                                "two_factor_enable": True,
                            }
                        ),
                        headers=(("Content-Type", "text/json"),),
                    ),
                )

            headers = remember(self.request, username)
            LOG.info("User '%s' logged in.", username)
            came_from = self.request.params.get("came_from")
            if came_from:
                return HTTPFound(location=came_from, headers=headers)
            headers.append(("Content-Type", "text/json"))
            return set_common_headers(
                self.request,
                "login",
                NO_CACHE,
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

    @view_config(route_name="logout")
    def logout(self):
        headers = forget(self.request)

        if not self.request.user:
            LOG.info("Logout on non login user.")
            raise HTTPUnauthorized("See server logs for details")

        LOG.info("User '%s' (%s) logging out.", self.request.user.username, self.request.user.id)

        headers.append(("Content-Type", "text/json"))
        return set_common_headers(self.request, "login", NO_CACHE, response=Response("true", headers=headers))

    def _user(self, user=None):
        result = {
            "functionalities": self._functionality(),
            "is_intranet": is_intranet(self.request),
            "two_factor_enable": self.two_factor_auth,
        }
        user = self.request.user if user is None else user
        if user is not None:
            result.update(
                {
                    "username": user.username,
                    "email": user.email,
                    "roles": [{"name": r.name, "id": r.id} for r in user.roles],
                }
            )
        return result

    @view_config(route_name="loginuser", renderer="json")
    def loginuser(self):
        LOG.info("Client IP adresse: %s", self.request.client_addr)
        set_common_headers(self.request, "login", NO_CACHE)
        return self._user()

    @view_config(route_name="change_password", renderer="json")
    def change_password(self):
        set_common_headers(self.request, "login", NO_CACHE)

        login = self.request.POST.get("login")
        old_password = self.request.POST.get("oldPassword")
        new_password = self.request.POST.get("newPassword")
        new_password_confirm = self.request.POST.get("confirmNewPassword")
        if new_password is None or new_password_confirm is None or old_password is None:
            raise HTTPBadRequest(
                "'oldPassword', 'newPassword' and 'confirmNewPassword' should be available in "
                "request params."
            )

        if login is not None:
            try:
                user = self.request.get_user(login)
                if user is None:
                    LOG.info("The login '%s' does not exist.", login)
                    raise HTTPUnauthorized("See server logs for details")
            except NoResultFound:  # pragma: no cover
                LOG.info("The login '%s' does not exist.", login)
                raise HTTPUnauthorized("See server logs for details")

            if self.two_factor_auth:
                otp = self.request.POST.get("otp")
                if otp is None:
                    raise HTTPBadRequest("The second factor is missing.")
                if not self._validate_2fa_totp(user, otp):
                    LOG.info("The second factor is wrong for user '%s'.", login)
                    raise HTTPUnauthorized("See server logs for details")

        else:
            if self.request.user is not None:
                user = self.request.user
            else:
                raise HTTPBadRequest(
                    "You should be logged in or 'login' should be available in request params."
                )

        username = self.request.registry.validate_user(self.request, user.username, old_password)
        if username is None:
            LOG.info("The old password is wrong for user '%s'.", username)
            raise HTTPUnauthorized("See server logs for details")

        if new_password != new_password_confirm:
            raise HTTPBadRequest("The new password and the new password confirmation do not match")

        user.password = new_password
        user.is_password_changed = True
        models.DBSession.flush()
        LOG.info("Password changed for user '%s'", username)

        headers = remember(self.request, username)
        headers.append(("Content-Type", "text/json"))
        return set_common_headers(
            self.request, "login", NO_CACHE, response=Response(json.dumps(self._user(user)), headers=headers)
        )

    @staticmethod
    def generate_password():
        allchars = "123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        rand = Random()

        password = ""
        for _ in range(8):
            password += rand.choice(allchars)

        return password

    def _loginresetpassword(self):
        username = self.request.POST.get("login")
        if username is None:
            raise HTTPBadRequest("'login' should be available in request params.")
        username = self.request.POST["login"]
        try:
            user = models.DBSession.query(static.User).filter(static.User.username == username).one()
        except NoResultFound:  # pragma: no cover
            return None, None, None, "The login '{}' does not exist.".format(username)

        if user.email is None or user.email == "":  # pragma: no cover
            return None, None, None, "The user '{}' has no registered email address.".format(user.username)

        password = self.generate_password()
        user.set_temp_password(password)

        return user, username, password, None

    @view_config(route_name="loginresetpassword", renderer="json")
    def loginresetpassword(self):  # pragma: no cover
        set_common_headers(self.request, "login", NO_CACHE)

        user, username, password, error = self._loginresetpassword()
        if error is not None:
            LOG.info(error)
            raise HTTPUnauthorized("See server logs for details")
        if user.deactivated:
            LOG.info("The user '%s' is deactivated", username)
            raise HTTPUnauthorized("See server logs for details")

        send_email_config(
            self.request.registry.settings, "reset_password", user.email, user=username, password=password
        )

        return {"success": True}
