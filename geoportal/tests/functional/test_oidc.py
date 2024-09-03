import base64
import re
import urllib.parse
from http.client import responses
from unittest import TestCase

import jwt
import responses
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from pyramid import testing
from tests.functional import cleanup_db, create_dummy_request
from tests.functional import setup_common as setup_module  # noqa, pylint: disable=unused-import
from tests.functional import setup_db
from tests.functional import teardown_common as teardown_module  # noqa, pylint: disable=unused-import

_OIDC_CONFIGURATION = {
    "issuer": "https://sso.example.com",
    "authorization_endpoint": "https://sso.example.com/authorize",
    "token_endpoint": "https://sso.example.com/token",
    "jwks_uri": "https://sso.example.com/jwks",
    "subject_types_supported": ["public"],
    "id_token_signing_alg_values_supported": ["RS256"],
    "code_challenge_methods_supported": ["S256"],
}
_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=512)
_OIDC_KEYS = {
    "keys": [
        {
            "use": "sig",
            "kty": "RSA",
            "alg": "RS256",
            "n": base64.urlsafe_b64encode(
                _PRIVATE_KEY.public_key().public_numbers().n.to_bytes(64, byteorder="big")
            ).decode(),
            "e": "AQAB",
            # _PRIVATE_KEY.public_key().public_bytes(encoding=serialization.Encoding.DER, format=serialization.PublicFormat.SubjectPublicKeyInfo),
            # PKCS8EncodedKeySpec
        }
    ]
}


class TestLogin(TestCase):
    def setUp(self):
        setup_db()
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        cleanup_db()

    @responses.activate
    def test_login(self):
        from c2cgeoportal_geoportal.views.login import Login

        request = create_dummy_request(
            {
                "authentication": {
                    "openid_connect": {
                        "enabled": True,
                        "url": "https://sso.example.com",
                        "client_id": "client_id_1",
                    }
                }
            },
            params={"came_from": "/came_from"},
        )
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

        set_cookies = {k: v for k, v in [v.split("=", 1) for v in response.headers.getall("Set-Cookie")]}
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
    def test_callback(self):
        from c2cgeoportal_geoportal.views.login import Login

        request = create_dummy_request(
            {
                "authentication": {
                    "openid_connect": {
                        "enabled": True,
                        "url": "https://sso.example.com",
                        "client_id": "client_id_123",
                    }
                }
            },
            params={"code": "code_123"},
            cookies={
                "came_from": "/came_from",
                "code_verifier": "code_verifier",
                "code_challenge": "code_challenge",
            },
        )
        responses.get("https://sso.example.com/.well-known/openid-configuration", json=_OIDC_CONFIGURATION)
        responses.get("https://sso.example.com/jwks", json=_OIDC_KEYS)
        responses.post(
            "https://sso.example.com/token",
            json={
                "access_token": "access",
                "expires_in": 3600,
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

        set_cookies = {k: v for k, v in [v.split("=", 1) for v in response.headers.getall("Set-Cookie")]}
        assert set_cookies["came_from"].startswith("; Max-Age=0; Path=/; expires="), set_cookies["came_from"]
        assert set_cookies["code_verifier"].startswith("; Max-Age=0; Path=/; expires="), set_cookies[
            "code_verifier"
        ]
        assert set_cookies["code_challenge"].startswith("; Max-Age=0; Path=/; expires="), set_cookies[
            "code_challenge"
        ]
