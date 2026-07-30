# Copyright (c) 2013-2026, Camptocamp SA
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

# pylint: disable=missing-docstring,attribute-defined-outside-init,protected-access,no-value-for-parameter

import base64
import time
import types
from unittest.mock import Mock, PropertyMock, patch
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from tests import create_dummy_request

from c2cgeoportal_geoportal import create_get_user_from_request
from c2cgeoportal_geoportal.lib import oidc


class TestGetUser:
    @pytest.mark.usefixtures("dbsession", "transact")
    def test_get_user_oidc_enabled_non_json_identity(self, dbsession) -> None:
        from c2cgeoportal_commons.models.static import User

        settings = {
            "authentication": {"openid_connect": {"enabled": True}},
            "authorized_referers": ["example.com"],
        }

        request = create_dummy_request(settings)
        request.referrer = "https://example.com"
        request.host = "example.com"

        request.get_user_from_remember = types.MethodType(oidc.get_user_from_remember, request)

        with patch.object(type(request), "unauthenticated_userid", new_callable=PropertyMock) as mock_userid:
            mock_userid.return_value = "12345"

            test_user = User(username="12345", password="12345")
            dbsession.add(test_user)
            dbsession.flush()

            get_user = create_get_user_from_request(settings)
            user = get_user(request)

            assert user is not None
            assert user.username == "12345"
            assert user.deactivated is False

    @pytest.mark.usefixtures("dbsession", "transact")
    def test_get_user_oidc_bearer_token_query_user_info_false(self, dbsession) -> None:
        from c2cgeoportal_commons.models.static import User

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        now = int(time.time())
        token_payload = {
            "iss": "https://sso.example.com",
            "sub": "jwt_test_user",
            "aud": "test_client_id",
            "exp": now + 3600,
            "iat": now,
            "jti": str(uuid4()),
            "client_id": "test_client_id",
            "email": "jwt_test_user@example.com",
            "name": "JWT Test User",
        }
        token = jwt.encode(token_payload, private_key, algorithm="RS256")

        public_numbers = private_key.public_key().public_numbers()
        n = (
            base64.urlsafe_b64encode(
                public_numbers.n.to_bytes(256, byteorder="big"),
            )
            .decode()
            .rstrip("=")
        )
        from cryptojwt.jwk.jwk import key_from_jwk_dict

        jwk_obj = key_from_jwk_dict(
            {
                "use": "sig",
                "kty": "RSA",
                "e": "AQAB",
                "n": n,
            }
        )

        settings = {
            "authentication": {
                "openid_connect": {
                    "enabled": True,
                    "url": "https://sso.example.com",
                    "client_id": "test_client_id",
                },
            },
            "authorized_referers": ["example.com"],
        }

        request = create_dummy_request(settings)
        request.referrer = "https://example.com"
        request.host = "example.com"
        request.headers["Authorization"] = f"Bearer {token}"

        request.get_remember_from_user_info = types.MethodType(oidc.get_remember_from_user_info, request)
        request.get_user_from_remember = types.MethodType(oidc.get_user_from_remember, request)

        test_user = User(username="jwt_test_user", password="jwt_test_user")
        dbsession.add(test_user)
        dbsession.flush()

        with patch("c2cgeoportal_geoportal.lib.oidc.get_oidc_client") as mock_get_client:
            mock_client = Mock()
            mock_client.provider_keys = [jwk_obj]
            mock_client.provider_config = Mock()
            mock_client.provider_config.issuer = "https://sso.example.com"
            mock_client.client_auth = Mock()
            mock_client.client_auth.client_id = "test_client_id"
            mock_get_client.return_value = mock_client

            get_user = create_get_user_from_request(settings)
            user = get_user(request)

            assert user is not None
            assert user.username == "jwt_test_user"
            assert user.deactivated is False

    @pytest.mark.usefixtures("dbsession", "transact")
    def test_get_user_oidc_bearer_token_query_user_info_true(self, dbsession) -> None:
        from c2cgeoportal_commons.models.static import User

        settings = {
            "authentication": {
                "openid_connect": {
                    "enabled": True,
                    "query_user_info": True,
                    "url": "https://sso.example.com",
                    "client_id": "test_client_id",
                },
            },
            "authorized_referers": ["example.com"],
        }

        request = create_dummy_request(settings)
        request.referrer = "https://example.com"
        request.host = "example.com"
        request.headers["Authorization"] = "Bearer dummy_token"

        request.get_remember_from_user_info = types.MethodType(oidc.get_remember_from_user_info, request)
        request.get_user_from_remember = types.MethodType(oidc.get_user_from_remember, request)

        test_user = User(username="fetch_test_user", password="fetch_test_user")
        dbsession.add(test_user)
        dbsession.flush()

        with patch("c2cgeoportal_geoportal.lib.oidc.get_oidc_client") as mock_get_client:
            mock_client = Mock()

            def fetch_userinfo(_token):
                class UserInfo:
                    def dict(self):
                        return {
                            "sub": "fetch_test_user",
                            "email": "fetch_test_user@example.com",
                            "name": "Fetch Test User",
                        }

                return UserInfo()

            mock_client.fetch_userinfo = fetch_userinfo
            mock_get_client.return_value = mock_client

            get_user = create_get_user_from_request(settings)
            user = get_user(request)

            assert user is not None
            assert user.username == "fetch_test_user"
            assert user.deactivated is False
