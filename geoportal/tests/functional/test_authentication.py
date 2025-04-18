# Copyright (c) 2017-2025, Camptocamp SA
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

import datetime
from unittest import TestCase
from unittest.mock import patch

import transaction
from c2cgeoportal_geoportal.lib.authentication import UrlAuthenticationPolicy
from c2cgeoportal_geoportal.resources import defaultgroupsfinder
from c2cgeoportal_geoportal.scripts.urllogin import create_token

from tests.functional import create_dummy_request
from tests.functional import setup_common as setup_module  # noqa
from tests.functional import teardown_common as teardown_module  # noqa


class TestUrlAuthenticationPolicy(TestCase):
    def setup_method(self, _) -> None:
        self.maxDiff = None

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User

        user = User(username="__test_user1", password="__test_user1")
        DBSession.add(user)

        user2 = User(username="__test_user2", password="__test_user2", deactivated=True)
        DBSession.add(user2)

        now = datetime.datetime.utcnow()
        user3 = User(username="__test_user3", password="__test_user3", expire_on=now)
        DBSession.add(user3)

        tomorrow = now + datetime.timedelta(days=1)
        user4 = User(username="__test_user4", password="__test_user4", expire_on=tomorrow)
        DBSession.add(user4)

        DBSession.flush()

    def teardown_method(self, _) -> None:
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User

        DBSession.query(User).filter(User.username == "__test_user1").delete()
        DBSession.query(User).filter(User.username == "__test_user2").delete()
        DBSession.query(User).filter(User.username == "__test_user3").delete()
        DBSession.query(User).filter(User.username == "__test_user4").delete()
        transaction.commit()

    @patch("c2cgeoportal_geoportal.lib.authentication.remember")
    def get_user(self, aeskey, user, password, valid, remember_mock):
        token = create_token(aeskey, user, password, valid)
        request = create_dummy_request(params={"auth": token})
        policy = UrlAuthenticationPolicy(aeskey, defaultgroupsfinder)
        userid = policy.unauthenticated_userid(request)
        if userid is not None:
            remember_mock.assert_called_once_with(request, userid)
        else:
            remember_mock.assert_not_called()
        return userid

    def test_ok(self) -> None:
        user = self.get_user("foobar1234567891", "__test_user1", "__test_user1", 1)
        assert user is not None
        assert user == "__test_user1"

    def test_token_expired(self) -> None:
        assert self.get_user("foobar1234567891", "__test_user1", "__test_user1", -1) is None

    def test_wrong_user(self) -> None:
        assert self.get_user("foobar1234567891", "__test_user2", "__test_user1", 1) is None

    def test_wrong_pass(self) -> None:
        assert self.get_user("foobar1234567891", "__test_user1", "__test_user2", 1) is None

    def test_wrong_key(self) -> None:
        token = create_token("foobar1234567890", "__test_user1", "__test_user1", 1)
        request = create_dummy_request(params={"auth": token})
        policy = UrlAuthenticationPolicy("foobar1234567891", defaultgroupsfinder)
        userid = policy.unauthenticated_userid(request)
        assert userid is None

    @patch("c2cgeoportal_geoportal.lib.authentication._LOG.error", side_effect=Exception())
    def test_wrong_method(self, log_mock) -> None:  # pylint: disable=unused-argument
        """POST requests with input named "auth" must not raise exceptions due to urllogin."""

        def _get_user(method):
            request = create_dummy_request(params={"auth": "this is a wrong field value"}, method=method)
            policy = UrlAuthenticationPolicy(None, defaultgroupsfinder)
            assert policy.unauthenticated_userid(request) is None

        _get_user("GET")
        _get_user("POST")

    def test_user_deactivated(self) -> None:
        assert self.get_user("foobar1234567891", "__test_user2", "__test_user2", 1) is None

    def test_user_expired(self) -> None:
        assert self.get_user("foobar1234567891", "__test_user3", "__test_user3", 1) is None

    def test_user_currently_not_expired(self) -> None:
        user = self.get_user("foobar1234567891", "__test_user4", "__test_user4", 1)
        assert user == "__test_user4"
