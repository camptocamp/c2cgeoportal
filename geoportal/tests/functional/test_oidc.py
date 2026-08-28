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


import base64
import re
import types
import urllib.parse
from unittest import TestCase

import jwt
import pytest
import responses
from cryptography.hazmat.primitives.asymmetric import rsa
from pyramid import testing

from c2cgeoportal_geoportal.lib import oidc
from tests.functional import cleanup_db, create_dummy_request, setup_db
from tests.functional import setup_common as setup_module
from tests.functional import teardown_common as teardown_module


def use(item) -> None:
    pass


use(setup_module)
use(teardown_module)

_OIDC_CONFIGURATION = {
    "issuer": "https://sso.example.com",
    "authorization_endpoint": "https://sso.example.com/authorize",
    "token_endpoint": "https://sso.example.com/token",
    "jwks_uri": "https://sso.example.com/jwks",
    "subject_types_supported": ["public"],
    "id_token_signing_alg_values_supported": ["RS256"],
    "code_challenge_methods_supported": ["S256"],
}
_OIDC_CONFIGURATION_WITH_END_SESSION = {
    **_OIDC_CONFIGURATION,
    "end_session_endpoint": "https://sso.example.com/end-session",
}
_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_OIDC_KEYS = {
    "keys": [
        {
            "use": "sig",
            "kty": "RSA",
            "alg": "RS256",
            "n": base64.urlsafe_b64encode(
                _PRIVATE_KEY.public_key().public_numbers().n.to_bytes(256, byteorder="big"),
            ).decode(),
            "e": "AQAB",
        },
    ],
}


def includeme(request) -> None:
    request.get_remember_from_user_info = types.MethodType(oidc.get_remember_from_user_info, request)
    request.get_user_from_remember = types.MethodType(oidc.get_user_from_remember, request)


class TestLogin(TestCase):
    def setUp(self) -> None:
        setup_db()
        self.config = testing.setUp()

    def tearDown(self) -> None:
        testing.tearDown()
        cleanup_db()

    @responses.activate
    def test_login(self) -> None:
        from c2cgeoportal_geoportal.views.login import Login

        request = create_dummy_request(
            {
                "authentication": {
                    "openid_connect": {
                        "enabled": True,
                        "url": "https://sso.example.com",
                        "client_id": "client_id_1",
                    },
                },
            },
            params={"came_from": "/came_from"},
        )
        includeme(request)
        responses.get("https://sso.example.com/.well-known/openid-configuration", json=_OIDC_CONFIGURATION)
        responses.get("https://sso.example.com/jwks", json=_OIDC_KEYS)

        response = Login(request).oidc_login()
        assert response.status_int == 302
        location = urllib.parse.urlparse(response.headers["Location"])
        assert location.scheme == "https"
        assert location.netloc == "sso.example.com"
        assert location.path == "/authorize"
        query = urllib.parse.parse_qs(location.query)
        assert query["response_type"] == ["code"]
        assert query["client_id"] == ["client_id_1"]
        assert query["scope"] == ["openid profile email"]
        assert query["redirect_uri"] == ["http://example.com/oidc_callback/view"]
        assert "code_challenge" in query
        assert query["code_challenge_method"] == ["S256"]

        set_cookies = dict([v.split("=", 1) for v in response.headers.getall("Set-Cookie")])
        assert re.match(
            r"^.*; Domain=example\.com; Max\-Age=600; Path=/; expires=.*; secure; HttpOnly; SameSite=Lax$",
            set_cookies["code_verifier"],
        )
        assert re.match(
            r"^.*; Domain=example\.com; Max\-Age=600; Path=/; expires=.*; secure; HttpOnly; SameSite=Lax$",
            set_cookies["code_challenge"],
        )
        assert re.match(
            r"^/came_from; Domain=example\.com; Max\-Age=600; Path=/; expires=.*; secure; HttpOnly; SameSite=Lax$",
            set_cookies["came_from"],
        )

    @responses.activate
    def test_callback(self) -> None:
        from c2cgeoportal_geoportal.views.login import Login

        request = create_dummy_request(
            {
                "authentication": {
                    "openid_connect": {
                        "enabled": True,
                        "provide_roles": True,
                        "url": "https://sso.example.com",
                        "client_id": "client_id_123",
                    },
                },
            },
            params={"code": "code_123"},
            cookies={
                "came_from": "/came_from",
                "code_verifier": "code_verifier",
                "code_challenge": "code_challenge",
            },
        )
        includeme(request)
        responses.get("https://sso.example.com/.well-known/openid-configuration", json=_OIDC_CONFIGURATION)
        responses.get("https://sso.example.com/jwks", json=_OIDC_KEYS)
        id_token = jwt.encode(
            {
                "sub": "1234",
                "name": "Test User",
                "email": "user@example.com",
                "iss": "https://sso.example.com",
                "aud": "client_id_123",
                "exp": 2000000000,
                "iat": 1000000000,
            },
            _PRIVATE_KEY,
            algorithm="RS256",
        )
        responses.post(
            "https://sso.example.com/token",
            json={
                "access_token": "access",
                "expires_in": 3600,
                "token_type": "Bearer",
                "id_token": id_token,
            },
        )
        response = Login(request).oidc_callback()
        assert response.status_int == 302
        assert response.headers["Location"] == "/came_from"

        set_cookies = dict([v.split("=", 1) for v in response.headers.getall("Set-Cookie")])
        assert set_cookies["came_from"].startswith("; Max-Age=0; Path=/; expires="), set_cookies["came_from"]
        assert set_cookies["code_verifier"].startswith("; Max-Age=0; Path=/; expires="), set_cookies[
            "code_verifier"
        ]
        assert set_cookies["code_challenge"].startswith("; Max-Age=0; Path=/; expires="), set_cookies[
            "code_challenge"
        ]
        assert set_cookies["id_token"].startswith(f"{id_token};"), (
            "id_token cookie should contain the ID token"
        )
        assert "Max-Age=3600" in set_cookies["id_token"], (
            "id_token cookie should use the access token expiration when there is no refresh token"
        )

    @responses.activate
    def test_callback_refresh_token_set(self) -> None:
        from c2cgeoportal_geoportal.views.login import Login

        request = create_dummy_request(
            {
                "authentication": {
                    "openid_connect": {
                        "enabled": True,
                        "provide_roles": True,
                        "url": "https://sso.example.com",
                        "client_id": "client_id_123",
                    },
                },
            },
            params={"code": "code_123"},
            cookies={
                "came_from": "/came_from",
                "code_verifier": "code_verifier",
                "code_challenge": "code_challenge",
            },
        )
        includeme(request)
        responses.get("https://sso.example.com/.well-known/openid-configuration", json=_OIDC_CONFIGURATION)
        responses.get("https://sso.example.com/jwks", json=_OIDC_KEYS)
        responses.post(
            "https://sso.example.com/token",
            json={
                "access_token": "access",
                "expires_in": 3600,
                "refresh_token": "refresh_123",
                "token_type": "Bearer",
                "id_token": jwt.encode(
                    {
                        "sub": "1234",
                        "name": "Test User",
                        "email": "user@example.com",
                        "iss": "https://sso.example.com",
                        "aud": "client_id_123",
                        "exp": 2000000000,
                        "iat": 1000000000,
                    },
                    _PRIVATE_KEY,
                    algorithm="RS256",
                ),
            },
        )
        response = Login(request).oidc_callback()
        assert response.status_int == 302
        assert response.headers["Location"] == "/came_from"

        set_cookies = dict([v.split("=", 1) for v in response.headers.getall("Set-Cookie")])
        assert "refresh_token" in set_cookies, "refresh_token cookie should be set"
        assert set_cookies["refresh_token"].startswith("refresh_123;"), (
            "refresh_token cookie should contain the refresh token value"
        )

    @responses.activate
    def test_callback_refresh_token_default_max_age(self) -> None:
        from c2cgeoportal_geoportal.views.login import Login

        request = create_dummy_request(
            {
                "authentication": {
                    "openid_connect": {
                        "enabled": True,
                        "provide_roles": True,
                        "url": "https://sso.example.com",
                        "client_id": "client_id_123",
                        "refresh_max_age": 86400,
                    },
                },
            },
            params={"code": "code_123"},
            cookies={
                "came_from": "/came_from",
                "code_verifier": "code_verifier",
                "code_challenge": "code_challenge",
            },
        )
        includeme(request)
        responses.get("https://sso.example.com/.well-known/openid-configuration", json=_OIDC_CONFIGURATION)
        responses.get("https://sso.example.com/jwks", json=_OIDC_KEYS)
        responses.post(
            "https://sso.example.com/token",
            json={
                "access_token": "access",
                "expires_in": 3600,
                "refresh_token": "refresh_123",
                "token_type": "Bearer",
                "id_token": jwt.encode(
                    {
                        "sub": "1234",
                        "name": "Test User",
                        "email": "user@example.com",
                        "iss": "https://sso.example.com",
                        "aud": "client_id_123",
                        "exp": 2000000000,
                        "iat": 1000000000,
                    },
                    _PRIVATE_KEY,
                    algorithm="RS256",
                ),
            },
        )
        response = Login(request).oidc_callback()
        assert response.status_int == 302

        set_cookies = dict([v.split("=", 1) for v in response.headers.getall("Set-Cookie")])
        assert "Max-Age=86400" in set_cookies["refresh_token"], (
            "refresh_token cookie should use the configured refresh_max_age "
            "when the provider does not provide refresh_expires_in"
        )
        assert "Max-Age=86400" in set_cookies["id_token"], (
            "id_token cookie should have the same maximum age as the refresh token"
        )

    @responses.activate
    def test_callback_refresh_token_provider_expires_in(self) -> None:
        from c2cgeoportal_geoportal.views.login import Login

        request = create_dummy_request(
            {
                "authentication": {
                    "openid_connect": {
                        "enabled": True,
                        "provide_roles": True,
                        "url": "https://sso.example.com",
                        "client_id": "client_id_123",
                        "refresh_max_age": 86400,
                    },
                },
            },
            params={"code": "code_123"},
            cookies={
                "came_from": "/came_from",
                "code_verifier": "code_verifier",
                "code_challenge": "code_challenge",
            },
        )
        includeme(request)
        responses.get("https://sso.example.com/.well-known/openid-configuration", json=_OIDC_CONFIGURATION)
        responses.get("https://sso.example.com/jwks", json=_OIDC_KEYS)
        responses.post(
            "https://sso.example.com/token",
            json={
                "access_token": "access",
                "expires_in": 3600,
                "refresh_token": "refresh_123",
                "refresh_expires_in": 1234,
                "token_type": "Bearer",
                "id_token": jwt.encode(
                    {
                        "sub": "1234",
                        "name": "Test User",
                        "email": "user@example.com",
                        "iss": "https://sso.example.com",
                        "aud": "client_id_123",
                        "exp": 2000000000,
                        "iat": 1000000000,
                    },
                    _PRIVATE_KEY,
                    algorithm="RS256",
                ),
            },
        )
        response = Login(request).oidc_callback()
        assert response.status_int == 302

        set_cookies = dict([v.split("=", 1) for v in response.headers.getall("Set-Cookie")])
        assert "Max-Age=1234" in set_cookies["refresh_token"], (
            "refresh_token cookie should keep the refresh_expires_in value provided by the provider"
        )

    @responses.activate
    def test_callback_refresh_token_unset_max_age(self) -> None:
        from c2cgeoportal_geoportal.views.login import Login

        request = create_dummy_request(
            {
                "authentication": {
                    "openid_connect": {
                        "enabled": True,
                        "provide_roles": True,
                        "url": "https://sso.example.com",
                        "client_id": "client_id_123",
                    },
                },
            },
            params={"code": "code_123"},
            cookies={
                "came_from": "/came_from",
                "code_verifier": "code_verifier",
                "code_challenge": "code_challenge",
            },
        )
        includeme(request)
        responses.get("https://sso.example.com/.well-known/openid-configuration", json=_OIDC_CONFIGURATION)
        responses.get("https://sso.example.com/jwks", json=_OIDC_KEYS)
        responses.post(
            "https://sso.example.com/token",
            json={
                "access_token": "access",
                "expires_in": 3600,
                "refresh_token": "refresh_123",
                "token_type": "Bearer",
                "id_token": jwt.encode(
                    {
                        "sub": "1234",
                        "name": "Test User",
                        "email": "user@example.com",
                        "iss": "https://sso.example.com",
                        "aud": "client_id_123",
                        "exp": 2000000000,
                        "iat": 1000000000,
                    },
                    _PRIVATE_KEY,
                    algorithm="RS256",
                ),
            },
        )
        response = Login(request).oidc_callback()
        assert response.status_int == 302

        set_cookies = dict([v.split("=", 1) for v in response.headers.getall("Set-Cookie")])
        assert "Max-Age=604800" in set_cookies["refresh_token"], (
            "refresh_token cookie should use the default refresh_max_age when it's not configured"
        )


class TestLogout(TestCase):
    def setUp(self) -> None:
        setup_db()
        self.config = testing.setUp()

    def tearDown(self) -> None:
        testing.tearDown()
        cleanup_db()

    @staticmethod
    def _user():
        return oidc.DynamicUser(
            id=1,
            username="test_user",
            display_name="Test User",
            email="user@example.com",
            settings_role=None,
            roles=[],
        )

    @responses.activate
    def test_logout_redirect(self) -> None:
        from c2cgeoportal_geoportal.views.login import Login

        request = create_dummy_request(
            {
                "authentication": {
                    "openid_connect": {
                        "enabled": True,
                        "url": "https://sso.example.com",
                        "client_id": "client_id_1",
                        "logout_url": "https://sso.example.com/logout?post_logout_redirect_uri={came_from}",
                    },
                },
            },
            params={"came_from": "/came_from"},
            cookies={
                "access_token": "access_123",
                "refresh_token": "refresh_123",
                "id_token": "id_token_123",
            },
        )
        includeme(request)
        responses.get("https://sso.example.com/.well-known/openid-configuration", json=_OIDC_CONFIGURATION)
        request.user = self._user()

        response = Login(request).logout()
        assert response.status_int == 302
        assert (
            response.headers["Location"]
            == "https://sso.example.com/logout?post_logout_redirect_uri=http%3A%2F%2Fexample.com%2Fcame_from"
        )

        set_cookies = dict([v.split("=", 1) for v in response.headers.getall("Set-Cookie")])
        assert "Max-Age=0" in set_cookies["access_token"], "access_token cookie should be deleted on logout"
        assert "Max-Age=0" in set_cookies["refresh_token"], "refresh_token cookie should be deleted on logout"
        assert "Max-Age=0" in set_cookies["id_token"], "id_token cookie should be deleted on logout"

    @responses.activate
    def test_logout_redirect_absolute_came_from(self) -> None:
        from c2cgeoportal_geoportal.views.login import Login

        request = create_dummy_request(
            {
                "authentication": {
                    "openid_connect": {
                        "enabled": True,
                        "url": "https://sso.example.com",
                        "client_id": "client_id_1",
                        "logout_url": "https://sso.example.com/logout?post_logout_redirect_uri={came_from}",
                    },
                },
            },
            params={"came_from": "https://example.com/other"},
            cookies={"access_token": "access_123", "refresh_token": "refresh_123"},
        )
        includeme(request)
        responses.get("https://sso.example.com/.well-known/openid-configuration", json=_OIDC_CONFIGURATION)
        request.user = self._user()

        response = Login(request).logout()
        assert response.status_int == 302
        assert (
            response.headers["Location"]
            == "https://sso.example.com/logout?post_logout_redirect_uri=https%3A%2F%2Fexample.com%2Fother"
        )

    @responses.activate
    def test_logout_redirect_end_session_endpoint_placeholder(self) -> None:
        from c2cgeoportal_geoportal.views.login import Login

        request = create_dummy_request(
            {
                "authentication": {
                    "openid_connect": {
                        "enabled": True,
                        "url": "https://sso.example.com",
                        "client_id": "client_id_1",
                        "logout_url": "{end_session_endpoint}?post_logout_redirect_uri={came_from}",
                    },
                },
            },
            params={"came_from": "/came_from"},
            cookies={
                "access_token": "access_123",
                "refresh_token": "refresh_123",
                "id_token": "id_token_123",
            },
        )
        includeme(request)
        responses.get(
            "https://sso.example.com/.well-known/openid-configuration",
            json=_OIDC_CONFIGURATION_WITH_END_SESSION,
        )
        request.user = self._user()

        response = Login(request).logout()
        assert response.status_int == 302
        assert (
            response.headers["Location"]
            == "https://sso.example.com/end-session?post_logout_redirect_uri=http%3A%2F%2Fexample.com%2Fcame_from"
        )

    @responses.activate
    def test_logout_redirect_id_token_hint_placeholder(self) -> None:
        from c2cgeoportal_geoportal.views.login import Login

        request = create_dummy_request(
            {
                "authentication": {
                    "openid_connect": {
                        "enabled": True,
                        "url": "https://sso.example.com",
                        "client_id": "client_id_1",
                        "logout_url": (
                            "https://sso.example.com/logout"
                            "?post_logout_redirect_uri={came_from}&id_token_hint={id_token_hint}"
                        ),
                    },
                },
            },
            params={"came_from": "/came_from"},
            cookies={
                "access_token": "access_123",
                "refresh_token": "refresh_123",
                "id_token": "id_token.123",
            },
        )
        includeme(request)
        responses.get(
            "https://sso.example.com/.well-known/openid-configuration",
            json=_OIDC_CONFIGURATION_WITH_END_SESSION,
        )
        request.user = self._user()
        response = Login(request).logout()
        assert response.status_int == 302
        assert (
            response.headers["Location"] == "https://sso.example.com/logout"
            "?post_logout_redirect_uri=http%3A%2F%2Fexample.com%2Fcame_from&id_token_hint=id_token.123"
        )

    @responses.activate
    def test_logout_redirect_client_id_placeholder(self) -> None:
        from c2cgeoportal_geoportal.views.login import Login

        request = create_dummy_request(
            {
                "authentication": {
                    "openid_connect": {
                        "enabled": True,
                        "url": "https://sso.example.com",
                        "client_id": "client_id_1",
                        "logout_url": "https://sso.example.com/logout?client_id={client_id}",
                    },
                },
            },
            cookies={"access_token": "access_123", "refresh_token": "refresh_123"},
        )
        includeme(request)
        responses.get("https://sso.example.com/.well-known/openid-configuration", json=_OIDC_CONFIGURATION)
        request.user = self._user()

        response = Login(request).logout()
        assert response.status_int == 302
        assert response.headers["Location"] == "https://sso.example.com/logout?client_id=client_id_1"

    @responses.activate
    def test_logout_redirect_ui_locales_placeholder(self) -> None:
        from c2cgeoportal_geoportal.views.login import Login

        request = create_dummy_request(
            {
                "authentication": {
                    "openid_connect": {
                        "enabled": True,
                        "url": "https://sso.example.com",
                        "client_id": "client_id_1",
                        "logout_url": "https://sso.example.com/logout?ui_locales={ui_locales}",
                    },
                },
            },
            cookies={"access_token": "access_123", "refresh_token": "refresh_123"},
        )
        includeme(request)
        responses.get("https://sso.example.com/.well-known/openid-configuration", json=_OIDC_CONFIGURATION)
        request.user = self._user()

        response = Login(request).logout()
        assert response.status_int == 302
        assert response.headers["Location"] == "https://sso.example.com/logout?ui_locales=fr"

    @responses.activate
    def test_logout_redirect_unknown_placeholder(self) -> None:
        from pyramid.httpexceptions import HTTPInternalServerError

        from c2cgeoportal_geoportal.views.login import Login

        request = create_dummy_request(
            {
                "authentication": {
                    "openid_connect": {
                        "enabled": True,
                        "url": "https://sso.example.com",
                        "client_id": "client_id_1",
                        "logout_url": "https://sso.example.com/logout?foo={unknown_placeholder}",
                    },
                },
            },
            cookies={"access_token": "access_123", "refresh_token": "refresh_123"},
        )
        includeme(request)
        responses.get(
            "https://sso.example.com/.well-known/openid-configuration",
            json=_OIDC_CONFIGURATION_WITH_END_SESSION,
        )
        request.user = self._user()

        with pytest.raises(HTTPInternalServerError):
            Login(request).logout()

    @responses.activate
    def test_logout_redirect_unavailable_end_session_endpoint(self) -> None:
        from pyramid.httpexceptions import HTTPInternalServerError

        from c2cgeoportal_geoportal.views.login import Login

        request = create_dummy_request(
            {
                "authentication": {
                    "openid_connect": {
                        "enabled": True,
                        "url": "https://sso.example.com",
                        "client_id": "client_id_1",
                        "logout_url": "{end_session_endpoint}?post_logout_redirect_uri={came_from}",
                    },
                },
            },
            params={"came_from": "/came_from"},
            cookies={"access_token": "access_123", "refresh_token": "refresh_123"},
        )
        includeme(request)
        responses.get("https://sso.example.com/.well-known/openid-configuration", json=_OIDC_CONFIGURATION)
        request.user = self._user()

        with pytest.raises(HTTPInternalServerError):
            Login(request).logout()

    @responses.activate
    def test_logout_redirect_missing_id_token_hint(self) -> None:
        from pyramid.httpexceptions import HTTPInternalServerError

        from c2cgeoportal_geoportal.views.login import Login

        request = create_dummy_request(
            {
                "authentication": {
                    "openid_connect": {
                        "enabled": True,
                        "url": "https://sso.example.com",
                        "client_id": "client_id_1",
                        "logout_url": "https://sso.example.com/logout?id_token_hint={id_token_hint}",
                    },
                },
            },
            cookies={"access_token": "access_123", "refresh_token": "refresh_123"},
        )
        includeme(request)
        responses.get("https://sso.example.com/.well-known/openid-configuration", json=_OIDC_CONFIGURATION)
        request.user = self._user()

        with pytest.raises(HTTPInternalServerError):
            Login(request).logout()

    @responses.activate
    def test_logout_redirect_default_came_from(self) -> None:
        from c2cgeoportal_geoportal.views.login import Login

        request = create_dummy_request(
            {
                "authentication": {
                    "openid_connect": {
                        "enabled": True,
                        "url": "https://sso.example.com",
                        "client_id": "client_id_1",
                        "logout_url": "https://sso.example.com/logout?post_logout_redirect_uri={came_from}",
                    },
                },
            },
            cookies={"access_token": "access_123", "refresh_token": "refresh_123"},
        )
        includeme(request)
        responses.get("https://sso.example.com/.well-known/openid-configuration", json=_OIDC_CONFIGURATION)
        request.user = self._user()

        response = Login(request).logout()
        assert response.status_int == 302
        assert (
            response.headers["Location"] == "https://sso.example.com/logout?post_logout_redirect_uri="
            "http%3A%2F%2Fexample.com%2Fbase%2Fview%3F"
        )

    @responses.activate
    def test_logout_redirect_invalid_came_from(self) -> None:
        from pyramid.httpexceptions import HTTPBadRequest

        from c2cgeoportal_geoportal.views.login import Login

        request = create_dummy_request(
            {
                "authentication": {
                    "openid_connect": {
                        "enabled": True,
                        "url": "https://sso.example.com",
                        "client_id": "client_id_1",
                        "logout_url": "https://sso.example.com/logout?post_logout_redirect_uri={came_from}",
                    },
                },
            },
            params={"came_from": "https://evil.example.com/"},
            cookies={"access_token": "access_123", "refresh_token": "refresh_123"},
        )
        includeme(request)
        responses.get("https://sso.example.com/.well-known/openid-configuration", json=_OIDC_CONFIGURATION)
        request.user = self._user()

        with pytest.raises(HTTPBadRequest):
            Login(request).logout()

    @responses.activate
    def test_logout_came_from_without_logout_url(self) -> None:
        from c2cgeoportal_geoportal.views.login import Login

        request = create_dummy_request(
            {
                "authentication": {
                    "openid_connect": {
                        "enabled": True,
                        "url": "https://sso.example.com",
                        "client_id": "client_id_1",
                    },
                },
            },
            params={"came_from": "/came_from"},
            cookies={
                "access_token": "access_123",
                "refresh_token": "refresh_123",
                "id_token": "id_token_123",
            },
        )
        includeme(request)
        responses.get("https://sso.example.com/.well-known/openid-configuration", json=_OIDC_CONFIGURATION)
        request.user = self._user()

        response = Login(request).logout()
        assert response.status_int == 302
        assert response.headers["Location"] == "/came_from"

        set_cookies = dict([v.split("=", 1) for v in response.headers.getall("Set-Cookie")])
        assert "Max-Age=0" in set_cookies["access_token"], "access_token cookie should be deleted on logout"
        assert "Max-Age=0" in set_cookies["refresh_token"], "refresh_token cookie should be deleted on logout"
        assert "Max-Age=0" in set_cookies["id_token"], "id_token cookie should be deleted on logout"

    @responses.activate
    def test_logout_invalid_came_from_without_logout_url(self) -> None:
        from pyramid.httpexceptions import HTTPBadRequest

        from c2cgeoportal_geoportal.views.login import Login

        request = create_dummy_request(
            {
                "authentication": {
                    "openid_connect": {
                        "enabled": True,
                        "url": "https://sso.example.com",
                        "client_id": "client_id_1",
                    },
                },
            },
            params={"came_from": "https://evil.example.com/"},
            cookies={"access_token": "access_123", "refresh_token": "refresh_123"},
        )
        includeme(request)
        responses.get("https://sso.example.com/.well-known/openid-configuration", json=_OIDC_CONFIGURATION)
        request.user = self._user()

        with pytest.raises(HTTPBadRequest):
            Login(request).logout()

    @responses.activate
    def test_logout_no_logout_url(self) -> None:
        from c2cgeoportal_geoportal.views.login import Login

        request = create_dummy_request(
            {
                "authentication": {
                    "openid_connect": {
                        "enabled": True,
                        "url": "https://sso.example.com",
                        "client_id": "client_id_1",
                    },
                },
            },
            cookies={
                "access_token": "access_123",
                "refresh_token": "refresh_123",
                "id_token": "id_token_123",
            },
        )
        includeme(request)
        responses.get("https://sso.example.com/.well-known/openid-configuration", json=_OIDC_CONFIGURATION)
        request.user = self._user()

        response = Login(request).logout()
        assert response.status_int == 200, response.body
        assert response.body.decode("utf-8") == "true"

        set_cookies = dict([v.split("=", 1) for v in response.headers.getall("Set-Cookie")])
        assert "Max-Age=0" in set_cookies["access_token"], "access_token cookie should be deleted on logout"
        assert "Max-Age=0" in set_cookies["refresh_token"], "refresh_token cookie should be deleted on logout"
        assert "Max-Age=0" in set_cookies["id_token"], "id_token cookie should be deleted on logout"
