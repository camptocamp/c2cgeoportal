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

# pylint: disable=missing-docstring,attribute-defined-outside-init,protected-access


from unittest import TestCase

from pyramid import testing

from tests.functional import create_dummy_request
from tests.functional import setup_common as setup_module  # noqa
from tests.functional import teardown_common as teardown_module  # noqa


class TestAltchaView(TestCase):
    def teardown_method(self, _) -> None:
        testing.tearDown()

    @staticmethod
    def _create_request(additional_settings=None):
        request = create_dummy_request(additional_settings=additional_settings or {})
        request.params = {}
        return request

    def test_challenge(self) -> None:
        from c2cgeoportal_geoportal.views.altcha import altcha_challenge

        request = self._create_request({"altcha": {"hmac_secret": "test-secret"}})
        result = altcha_challenge(request)
        assert result["parameters"]["algorithm"] == "PBKDF2/SHA-256"
        assert result["parameters"]["cost"] == 5000
        assert result["signature"] != ""

    def test_challenge_without_secret(self) -> None:
        from c2cgeoportal_geoportal.views.altcha import altcha_challenge

        request = self._create_request({"altcha": {}})
        result = altcha_challenge(request)
        assert result["parameters"]["algorithm"] == "PBKDF2/SHA-256"
        assert "signature" not in result

    def test_verify_missing_payload(self) -> None:
        from pyramid.httpexceptions import HTTPBadRequest

        from c2cgeoportal_geoportal.views.altcha import verify_altcha_payload

        request = self._create_request({"altcha": {"hmac_secret": "test-secret"}})
        with self.assertRaises(HTTPBadRequest):
            verify_altcha_payload(request)

    def test_verify_invalid_payload(self) -> None:
        from pyramid.httpexceptions import HTTPBadRequest

        from c2cgeoportal_geoportal.views.altcha import verify_altcha_payload

        request = self._create_request({"altcha": {"hmac_secret": "test-secret"}})
        request.params = {"altcha": "invalid-payload"}
        with self.assertRaises(HTTPBadRequest):
            verify_altcha_payload(request)

    def test_verify_valid_payload(self) -> None:
        from altcha import Payload, create_challenge, solve_challenge

        from c2cgeoportal_geoportal.views.altcha import verify_altcha_payload

        hmac_secret = "test-secret"
        challenge = create_challenge(algorithm="PBKDF2/SHA-256", cost=500, hmac_secret=hmac_secret)
        solution = solve_challenge(challenge)
        assert solution is not None
        payload = Payload(challenge, solution).to_base64()

        request = self._create_request({"altcha": {"hmac_secret": hmac_secret}})
        request.params = {"altcha": payload}
        verify_altcha_payload(request)
