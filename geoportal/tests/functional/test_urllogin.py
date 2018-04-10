# -*- coding: utf-8 -*-

# Copyright (c) 2017-2018, Camptocamp SA
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


from unittest import TestCase
import datetime
import transaction
import pyramid.security
from c2cgeoportal_geoportal import create_get_user_from_request
from c2cgeoportal_geoportal.scripts.urllogin import create_token
from tests.functional import (  # noqa
    teardown_common as teardown_module,
    setup_common as setup_module,
    create_dummy_request,
)


class TestUrllogin(TestCase):

    def setup_method(self, _):
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

        self.old_remember = pyramid.security.remember
        self.user = None

        def remember(request, user=None):
            self.user = user

        pyramid.security.remember = remember

    def teardown_method(self, _):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User

        DBSession.query(User).filter(User.username == "__test_user1").delete()
        DBSession.query(User).filter(User.username == "__test_user2").delete()
        DBSession.query(User).filter(User.username == "__test_user3").delete()
        DBSession.query(User).filter(User.username == "__test_user4").delete()
        transaction.commit()

        pyramid.security.remember = None
        pyramid.security.remember = self.old_remember

    def get_user(self, aeskey, user, password, valid):
        token = create_token(aeskey, user, password, valid)
        request = create_dummy_request({
            "urllogin": {
                "aes_key": aeskey
            }
        }, params={"auth": token})
        get_user_from_request = create_get_user_from_request(request.registry.settings)
        get_user_from_request(request)
        return self.user

    def test_ok(self):
        user = self.get_user("foobar1234567891", "__test_user1", "__test_user1", 1)
        self.assertIsNotNone(user)
        self.assertEqual(user, "__test_user1")

    def test_token_expired(self):
        self.assertIsNone(self.get_user("foobar1234567891", "__test_user1", "__test_user1", -1))

    def test_wrong_user(self):
        self.assertIsNone(self.get_user("foobar1234567891", "__test_user2", "__test_user1", 1))

    def test_wrong_pass(self):
        self.assertIsNone(self.get_user("foobar1234567891", "__test_user1", "__test_user2", 1))

    def test_wrong_key(self):
        token = create_token("foobar1234567890", "__test_user1", "__test_user1", 1)
        request = create_dummy_request({
            "urllogin": {
                "aes_key": "foobar1234567891"
            }
        }, params={"auth": token})
        get_user_from_request = create_get_user_from_request(request.registry.settings)
        get_user_from_request(request)
        self.assertIsNone(self.user)

    def test_user_deactivated(self):
        self.assertIsNone(self.get_user("foobar1234567891", "__test_user2", "__test_user2", 1))

    def test_user_expired(self):
        self.assertIsNone(self.get_user("foobar1234567891", "__test_user3", "__test_user3", 1))

    def test_user_currently_not_expired(self):
        user = self.get_user("foobar1234567891", "__test_user4", "__test_user4", 1)
        self.assertEqual(user, "__test_user4")
