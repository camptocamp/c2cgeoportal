# Copyright (c) 2014-2025, Camptocamp SA
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


import binascii
import json
import logging
import os
import re
import time
from collections.abc import Callable
from typing import Any, cast

import pyramid.request
from Crypto.Cipher import AES  # nosec
from pyramid.authentication import (
    AuthTktAuthenticationPolicy,
    BasicAuthAuthenticationPolicy,
    CallbackAuthenticationPolicy,
)
from pyramid.interfaces import IAuthenticationPolicy
from pyramid.security import remember
from pyramid_multiauth import MultiAuthenticationPolicy
from zope.interface import implementer

import c2cgeoportal_commons.models
from c2cgeoportal_geoportal.lib import oauth2
from c2cgeoportal_geoportal.resources import defaultgroupsfinder

_LOG = logging.getLogger(__name__)

_HEX_RE = re.compile(r"^[0-9a-fA-F]+$")


@implementer(IAuthenticationPolicy)
class UrlAuthenticationPolicy(CallbackAuthenticationPolicy):  # type: ignore
    """An authentication policy based on information given in the URL."""

    def __init__(
        self, aes_key: str, callback: Callable[[str, Any], list[str]] | None = None, debug: bool = False
    ):
        self.aeskey = aes_key
        self.callback = callback
        self.debug = debug

    def unauthenticated_userid(self, request: pyramid.request.Request) -> str | None:
        if not request.method == "GET" or "auth" not in request.params:
            return None
        auth_enc = request.params.get("auth")
        if auth_enc is None:
            return None
        try:
            if self.aeskey is None:
                _LOG.warning("Found auth parameter in URL query string but urllogin is not configured")
                return None

            if not _HEX_RE.match(auth_enc):
                _LOG.warning("Found auth parameter in URL query string but it is not an hex string")
                return None

            if len(auth_enc) % 2 != 0:
                _LOG.warning(
                    "Found auth parameter in URL query string but it is not an even number of characters"
                )
                return None

            now = int(time.time())
            data = binascii.unhexlify(auth_enc.encode("ascii"))
            nonce = data[0:16]
            tag = data[16:32]
            ciphertext = data[32:]
            cipher = AES.new(self.aeskey.encode("ascii"), AES.MODE_EAX, nonce)
            auth = json.loads(cipher.decrypt_and_verify(ciphertext, tag).decode("utf-8"))

            if "t" in auth and "u" in auth and "p" in auth:
                timestamp = int(auth["t"])

                if now < timestamp and request.registry.validate_user(request, auth["u"], auth["p"]):
                    headers = remember(request, auth["u"])
                    request.response.headerlist.extend(headers)
                    return cast(str, auth["u"])

        except Exception:  # pylint: disable=broad-exception-caught
            _LOG.exception("URL login error on auth '%s'.", auth_enc)

        return None

    def remember(self, request: pyramid.request.Request, userid: str, **kw: Any) -> list[dict[str, str]]:
        """Do no-op."""
        del request, userid, kw
        return []

    def forget(self, request: pyramid.request.Request) -> list[dict[str, str]]:
        """Do no-op."""
        del request
        return []


@implementer(IAuthenticationPolicy)
class OAuth2AuthenticationPolicy(CallbackAuthenticationPolicy):  # type: ignore
    """The oauth2 authentication policy."""

    @staticmethod
    def unauthenticated_userid(request: pyramid.request.Request) -> str | None:
        route_url = ""
        try:
            route_url = request.current_route_url(_query={**request.GET})
        except ValueError:
            route_url = request.route_url("base", _query={**request.GET})

        _LOG.debug(
            "Call OAuth verify_request with:\nurl: %s\nmethod: %s\nbody:\n%s",
            route_url,
            request.method,
            request.body,
        )
        valid, oauth2_request = oauth2.get_oauth_client(request.registry.settings).verify_request(
            route_url,
            request.method,
            request.body,
            request.headers,
            [],
        )
        _LOG.debug("OAuth verify_request: %s", valid)
        if valid:
            request.user_ = oauth2_request.user
            if request.user_ is not None and c2cgeoportal_commons.models.DBSession is not None:
                c2cgeoportal_commons.models.DBSession.add(request.user_)

            return cast(str, request.user.username)
        return None

    def remember(self, request: pyramid.request.Request, userid: str, **kw: Any) -> list[dict[str, str]]:
        """Do no-op."""
        del request, userid, kw
        return []

    def forget(self, request: pyramid.request.Request) -> list[dict[str, str]]:
        """Do no-op."""
        del request
        return []


@implementer(IAuthenticationPolicy)
class DevAuthenticationPolicy(CallbackAuthenticationPolicy):  # type: ignore
    """An authentication policy for the dev base on an environment variable."""

    @staticmethod
    def unauthenticated_userid(request: pyramid.request.Request) -> str | None:
        """Get the user name from the environment variable."""
        del request
        return os.environ["DEV_LOGINNAME"]


def create_authentication(settings: dict[str, Any]) -> MultiAuthenticationPolicy:
    """Create all the authentication policies."""
    timeout = settings.get("authtkt_timeout")
    timeout = None if timeout is None or timeout.lower() == "none" else int(timeout)
    reissue_time = settings.get("authtkt_reissue_time")
    reissue_time = None if reissue_time is None or reissue_time.lower() == "none" else int(reissue_time)
    max_age = settings.get("authtkt_max_age")
    max_age = None if max_age is None or max_age.lower() == "none" else int(max_age)
    http_only = settings.get("authtkt_http_only", "True")
    http_only = http_only.lower() in ("true", "yes", "1")
    secure = settings.get("authtkt_secure", "True")
    secure = secure.lower() in ("true", "yes", "1")
    samesite = settings.get("authtkt_samesite", "Lax")
    secret = settings["authtkt_secret"]
    basicauth = settings.get("basicauth", "False").lower() in ("true", "yes", "1")
    if len(secret) < 64:
        raise Exception(  # pylint: disable=broad-exception-raised
            '"authtkt_secret should be at least 64 characters.'
            "See https://docs.pylonsproject.org/projects/pyramid/en/latest/api/session.html"
        )

    policies = []

    policies.append(
        UrlAuthenticationPolicy(
            settings.get("urllogin", {}).get("aes_key"),
            defaultgroupsfinder,
        )
    )

    policies.append(
        AuthTktAuthenticationPolicy(
            secret,
            callback=defaultgroupsfinder,
            cookie_name=settings["authtkt_cookie_name"],
            samesite=None if samesite == "" else samesite,
            timeout=timeout,
            max_age=max_age,
            reissue_time=reissue_time,
            hashalg="sha512",
            http_only=http_only,
            secure=secure,
        )
    )

    authentication_config = settings.get("authentication", {})
    openid_connect_config = authentication_config.get("openid_connect", {})
    oauth2_config = authentication_config.get("oauth2", {})
    if oauth2_config.get("enabled", not openid_connect_config.get("enabled", False)):
        policies.append(OAuth2AuthenticationPolicy())

    if basicauth:
        if authentication_config.get("two_factor", False):
            _LOG.warning(
                "Basic auth and two factor auth should not be enable together, "
                "you should use OAuth2 instead of Basic auth"
            )
        if openid_connect_config.get("enabled", False):
            _LOG.warning("Basic auth and OpenID Connect should not be enable together")

        basic_authentication_policy = BasicAuthAuthenticationPolicy(c2cgeoportal_check)
        policies.append(basic_authentication_policy)

    # Consider empty string as not configured
    if "DEV_LOGINNAME" in os.environ and os.environ["DEV_LOGINNAME"]:
        policies.append(DevAuthenticationPolicy())

    return MultiAuthenticationPolicy(policies)


def c2cgeoportal_check(username: str, password: str, request: pyramid.request.Request) -> list[str] | None:
    """Check the user authentication."""
    if request.registry.validate_user(request, username, password):
        return defaultgroupsfinder(username, request)
    return None
