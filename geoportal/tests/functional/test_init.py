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

import types
from unittest.mock import PropertyMock, patch

import pytest

from c2cgeoportal_geoportal import create_get_user_from_request
from c2cgeoportal_geoportal.lib import oidc
from tests import create_dummy_request


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
