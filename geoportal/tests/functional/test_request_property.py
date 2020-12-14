# -*- coding: utf-8 -*-

# Copyright (c) 2011-2019, Camptocamp SA
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


import base64
from unittest import TestCase

from tests.functional import create_dummy_request
from tests.functional import setup_common as setup_module  # noqa
from tests.functional import teardown_common as teardown_module  # noqa


class TestRequestProperty(TestCase):
    def setup_method(self, _):
        import transaction

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import Role
        from c2cgeoportal_commons.models.static import User

        r = Role(name="__test_role")
        u = User(username="__test_user", password="__test_user", settings_role=r, roles=[r])

        DBSession.add_all([u, r])
        transaction.commit()

    def teardown_method(self, _):
        import transaction

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import Role
        from c2cgeoportal_commons.models.static import User

        transaction.commit()

        DBSession.delete(DBSession.query(User).filter_by(username="__test_user").one())
        DBSession.query(Role).filter_by(name="__test_role").delete()
        transaction.commit()

    def test_request_no_auth(self):
        request = create_dummy_request()
        self.assertEqual(request.user, None)

    def test_request_auth(self):
        request = create_dummy_request(authentication=False, user="__test_user")
        self.assertEqual(request.user.username, "__test_user")
        self.assertEqual([role.name for role in request.user.roles], ["__test_role"])

    def test_request_right_auth(self):
        request = create_dummy_request(
            {"basicauth": "true"},
            headers={
                "Authorization": "Basic "
                + base64.b64encode("__test_user:__test_user".encode("utf-8"))
                .decode("utf-8")
                .replace("\n", "")
            },
        )

        self.assertEqual(request.user.username, "__test_user")

    def test_request_wrong_auth(self):
        request = create_dummy_request(
            headers={
                "Authorization": "Basic "
                + base64.b64encode("__test_user:__wrong_pass".encode("utf-8"))
                .decode("utf-8")
                .replace("\n", "")
            }
        )

        self.assertEqual(request.user, None)

    def test_request_auth_overwritten_property(self):
        def setter(request):
            del request  # Unused

            class User:
                pass

            class Role:
                pass

            user = User()
            user.username = "__foo"
            role = Role()
            role.name = "__bar"
            user.settings_role = role
            user.roles = [role]
            return user

        request = create_dummy_request(authentication=False, user="__test_user")
        request.set_property(setter, name="user", reify=True)
        self.assertEqual(request.user.username, "__foo")
        self.assertEqual([role.name for role in request.user.roles], ["__bar"])
