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
from unittest import TestCase
from unittest.mock import MagicMock, patch

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa


def _generate_rsa_key_pair():
    """Generate an RSA key pair for testing."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    return private_key, public_key


def _create_test_token(
    private_key,
    audience="geomapfish-l10n",
    issuer="https://token.actions.githubusercontent.com",
    repository="org/repo",
    expired=False,
):
    """Create a test JWT token."""
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    payload = {
        "iss": issuer,
        "aud": audience,
        "exp": now - datetime.timedelta(hours=1) if expired else now + datetime.timedelta(hours=1),
        "iat": now,
        "sub": f"repo:{repository}:ref:refs/heads/main",
        "repository": repository,
        "repository_owner": repository.split("/")[0],
        "workflow": "update_l10n",
        "job_workflow_ref": f"{repository}/.github/workflows/update_l10n.yaml@refs/heads/main",
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


class TestVerifyGithubOidcToken(TestCase):
    """Tests for _verify_github_oidc_token."""

    def setUp(self):
        self.private_key, self.public_key = _generate_rsa_key_pair()

    def _mock_jwks_client(self, signing_key):
        """Create a mock JWKS client that returns the given signing key."""
        mock_client = MagicMock()
        mock_signing_key = MagicMock()
        mock_signing_key.key = self.public_key
        mock_client.get_signing_key_from_jwt.return_value = mock_signing_key
        return mock_client

    @patch("c2cgeoportal_geoportal.views.i18n._get_jwks_client")
    def test_valid_token(self, mock_get_client):
        """A valid token should be accepted."""
        from c2cgeoportal_geoportal.views.i18n import _verify_github_oidc_token

        token = _create_test_token(self.private_key)
        mock_get_client.return_value = self._mock_jwks_client(self.public_key)

        payload = _verify_github_oidc_token(token, None)
        self.assertEqual(payload["repository"], "org/repo")

    @patch("c2cgeoportal_geoportal.views.i18n._get_jwks_client")
    def test_valid_token_with_repository_check(self, mock_get_client):
        """A valid token with correct repository should be accepted."""
        from c2cgeoportal_geoportal.views.i18n import _verify_github_oidc_token

        token = _create_test_token(self.private_key, repository="org/repo")
        mock_get_client.return_value = self._mock_jwks_client(self.public_key)

        payload = _verify_github_oidc_token(token, "org/repo")
        self.assertEqual(payload["repository"], "org/repo")

    @patch("c2cgeoportal_geoportal.views.i18n._get_jwks_client")
    def test_wrong_repository(self, mock_get_client):
        """A token with wrong repository should be rejected."""
        from c2cgeoportal_geoportal.views.i18n import _verify_github_oidc_token
        from pyramid.httpexceptions import HTTPForbidden

        token = _create_test_token(self.private_key, repository="org/repo")
        mock_get_client.return_value = self._mock_jwks_client(self.public_key)

        with self.assertRaises(HTTPForbidden) as ctx:
            _verify_github_oidc_token(token, "other/repo")
        self.assertIn("Unauthorized repository", str(ctx.exception.detail))

    @patch("c2cgeoportal_geoportal.views.i18n._get_jwks_client")
    def test_expired_token(self, mock_get_client):
        """An expired token should be rejected."""
        from c2cgeoportal_geoportal.views.i18n import _verify_github_oidc_token
        from pyramid.httpexceptions import HTTPForbidden

        token = _create_test_token(self.private_key, expired=True)
        mock_get_client.return_value = self._mock_jwks_client(self.public_key)

        with self.assertRaises(HTTPForbidden) as ctx:
            _verify_github_oidc_token(token, None)
        self.assertEqual("Token expired", str(ctx.exception.detail))

    @patch("c2cgeoportal_geoportal.views.i18n._get_jwks_client")
    def test_wrong_audience(self, mock_get_client):
        """A token with wrong audience should be rejected."""
        from c2cgeoportal_geoportal.views.i18n import _verify_github_oidc_token
        from pyramid.httpexceptions import HTTPForbidden

        token = _create_test_token(self.private_key, audience="wrong-audience")
        mock_get_client.return_value = self._mock_jwks_client(self.public_key)

        with self.assertRaises(HTTPForbidden) as ctx:
            _verify_github_oidc_token(token, None)
        self.assertEqual("Invalid token audience", str(ctx.exception.detail))

    @patch("c2cgeoportal_geoportal.views.i18n._get_jwks_client")
    def test_wrong_issuer(self, mock_get_client):
        """A token with wrong issuer should be rejected."""
        from c2cgeoportal_geoportal.views.i18n import _verify_github_oidc_token
        from pyramid.httpexceptions import HTTPForbidden

        token = _create_test_token(
            self.private_key, issuer="https://evil.example.com"
        )
        mock_get_client.return_value = self._mock_jwks_client(self.public_key)

        with self.assertRaises(HTTPForbidden) as ctx:
            _verify_github_oidc_token(token, None)
        self.assertEqual("Invalid token issuer", str(ctx.exception.detail))


class TestAuthenticateLocalepot(TestCase):
    """Tests for _authenticate_localepot."""

    def test_bearer_token_with_valid_oidc(self):
        """A valid Bearer token should be accepted."""
        from c2cgeoportal_geoportal.views.i18n import _authenticate_localepot

        request = MagicMock()
        request.headers = {"Authorization": "Bearer fake-token"}
        request.registry.settings = {}

        with patch("c2cgeoportal_geoportal.views.i18n._verify_github_oidc_token") as mock_verify:
            mock_verify.return_value = {"repository": "org/repo"}
            _authenticate_localepot(request)
            mock_verify.assert_called_once_with("fake-token", None)

    def test_bearer_token_with_repository_setting(self):
        """The allowed_repository setting should be passed to verification."""
        from c2cgeoportal_geoportal.views.i18n import _authenticate_localepot

        request = MagicMock()
        request.headers = {"Authorization": "Bearer fake-token"}
        request.registry.settings = {"github_oidc_allowed_repository": "my/repo"}

        with patch("c2cgeoportal_geoportal.views.i18n._verify_github_oidc_token") as mock_verify:
            mock_verify.return_value = {"repository": "my/repo"}
            _authenticate_localepot(request)
            mock_verify.assert_called_once_with("fake-token", "my/repo")

    def test_no_bearer_token_falls_back_to_auth_view(self):
        """Without a Bearer token, auth_view should be called."""
        from c2cgeoportal_geoportal.views.i18n import _authenticate_localepot

        request = MagicMock()
        request.headers = {}
        request.registry.settings = {}

        with patch("c2cgeoportal_geoportal.views.i18n.auth_view") as mock_auth_view:
            _authenticate_localepot(request)
            mock_auth_view.assert_called_once_with(request)

    def test_non_bearer_auth_header_falls_back_to_auth_view(self):
        """A non-Bearer Authorization header should fall back to auth_view."""
        from c2cgeoportal_geoportal.views.i18n import _authenticate_localepot

        request = MagicMock()
        request.headers = {"Authorization": "Basic dXNlcjpwYXNz"}
        request.registry.settings = {}

        with patch("c2cgeoportal_geoportal.views.i18n.auth_view") as mock_auth_view:
            _authenticate_localepot(request)
            mock_auth_view.assert_called_once_with(request)
