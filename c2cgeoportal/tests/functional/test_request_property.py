# -*- coding: utf-8 -*-

# Copyright (c) 2011-2016, Camptocamp SA
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


import base64
from nose.plugins.attrib import attr
from pyramid import testing
from unittest import TestCase

from c2cgeoportal.tests.functional import (  # noqa
    tear_down_common as tearDownModule,
    set_up_common as setUpModule,
    add_user_property
)


@attr(functional=True)
class TestRequestProperty(TestCase):

    def setUp(self):  # noqa
        self.config = testing.setUp()

        import transaction
        from c2cgeoportal.models import DBSession, User, Role

        r = Role(name=u"__test_role")
        u = User(
            username=u"__test_user", password=u"__test_user", role=r
        )

        DBSession.add_all([u, r])
        transaction.commit()

    def tearDown(self):  # noqa
        testing.tearDown()

        import transaction
        from c2cgeoportal.models import DBSession, User, Role

        transaction.commit()

        DBSession.query(User).filter_by(username=u"__test_user").delete()
        DBSession.query(Role).filter_by(name=u"__test_role").delete()
        transaction.commit()

    def test_request_no_auth(self):
        request = self._create_request()
        self.assertEqual(request.user, None)

    def test_request_auth(self):
        self.config.testing_securitypolicy(u"__test_user")
        request = self._create_request()
        self.assertEqual(request.user.username, u"__test_user")
        self.assertEqual(request.user.role.name, u"__test_role")

    def test_request_right_auth(self):
        from pyramid.testing import DummyRequest
        from c2cgeoportal import default_user_validator
        from c2cgeoportal.lib.authentication import create_authentication

        request = DummyRequest(headers={
            "Authorization": "Basic " + base64.b64encode("__test_user:__test_user").replace("\n", "")
        })
        request.path_info_peek = lambda: "main"
        request.registry.validate_user = default_user_validator
        request._get_authentication_policy = lambda: create_authentication({
            "authtkt_cookie_name": "__test",
            "authtkt_secret": "123",
        })
        add_user_property(request)

        self.assertEqual(request.user.username, u"__test_user")

    def test_request_wrong_auth(self):
        from pyramid.testing import DummyRequest
        from c2cgeoportal import default_user_validator
        from c2cgeoportal.lib.authentication import create_authentication

        request = DummyRequest(headers={
            "Authorization": "Basic " + base64.b64encode("__test_user:__wrong_pass").replace("\n", "")
        })
        request.path_info_peek = lambda: "main"
        request.registry.validate_user = default_user_validator
        request._get_authentication_policy = lambda: create_authentication({
            "authtkt_cookie_name": "__test",
            "authtkt_secret": "123",
        })
        add_user_property(request)

        self.assertEqual(request.user, None)

    def test_request_auth_overwritten_property(self):
        def setter(request):
            class User(object):
                pass

            class Role(object):
                pass

            u = User()
            u.username = u"__foo"
            u.role = Role()
            u.role.name = u"__bar"
            return u

        self.config.testing_securitypolicy(u"__test_user")
        request = self._create_request()
        request.set_property(setter, name="user", reify=True)
        self.assertEqual(request.user.username, u"__foo")
        self.assertEqual(request.user.role.name, u"__bar")

    def _create_request(self):
        from pyramid.request import Request
        request = Request({})
        add_user_property(request)
        return request
