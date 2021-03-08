# -*- coding: utf-8 -*-

# Copyright (c) 2013-2019, Camptocamp SA
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


import json
import logging
from unittest import TestCase

import pytest
import transaction
from geoalchemy2 import WKTElement
from pyramid import testing
from tests.functional import cleanup_db, create_dummy_request, fill_tech_user_functionality, mapserv_url
from tests.functional import setup_common as setup_module  # noqa, pylint: disable=unused-import
from tests.functional import setup_db
from tests.functional import teardown_common as teardown_module  # noqa, pylint: disable=unused-import

LOG = logging.getLogger(__name__)


class TestLoginView(TestCase):
    def setup_method(self, _):
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None  # pylint: disable=invalid-name
        self._tables = []

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import Role
        from c2cgeoportal_commons.models.static import User

        setup_db()

        role1 = Role(name="__test_role1")
        user1 = User(username="__test_user1", password="__test_user1", settings_role=role1, roles=[role1])
        user1.email = "__test_user1@example.com"

        role2 = Role(name="__test_role2", extent=WKTElement("POLYGON((1 2, 1 4, 3 4, 3 2, 1 2))", srid=21781))
        user2 = User(username="__test_user2", password="__test_user2", settings_role=role2, roles=[role2])

        DBSession.add_all([user1, user2])
        DBSession.flush()

        self.role1_id = role1.id

        transaction.commit()

    def teardown_method(self, _):
        testing.tearDown()

        cleanup_db()

    @staticmethod
    def _create_request_obj(username=None, params=None, **kwargs):
        if params is None:
            params = {}
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User

        request = create_dummy_request(**kwargs)
        request.route_url = lambda url, **kwargs: mapserv_url
        request.interface_name = "desktop"
        request.params = params

        if username is not None:
            request.user = DBSession.query(User).filter_by(username=username).one()

        return request

    #
    # login/logout tests
    #

    def test_login(self):
        from pyramid.httpexceptions import HTTPUnauthorized

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User
        from c2cgeoportal_geoportal.views.login import Login

        user = DBSession.query(User).filter_by(username="__test_user1").one()
        user.is_password_changed = True

        request = self._create_request_obj(
            params={"came_from": "/came_from"}, POST={"login": "__test_user1", "password": "__test_user1"}
        )
        response = Login(request).login()
        assert response.status_int == 302
        assert response.headers["Location"] == "/came_from"

        request = self._create_request_obj(POST={"login": "__test_user1", "password": "__test_user1"})
        response = Login(request).login()
        assert response.status_int == 200
        assert json.loads(response.body.decode("utf-8")) == {
            "username": "__test_user1",
            "email": "__test_user1@example.com",
            "is_intranet": False,
            "two_factor_enable": False,
            "roles": [{"name": "__test_role1", "id": self.role1_id}],
            "functionalities": {},
        }

        request = self._create_request_obj(POST={"login": "__test_user1", "password": "bad password"})
        login = Login(request)
        self.assertRaises(HTTPUnauthorized, login.login)

    def test_logout_no_auth(self):
        from pyramid.httpexceptions import HTTPUnauthorized

        from c2cgeoportal_geoportal.views.login import Login

        request = self._create_request_obj(path="/", params={"came_from": "/came_from"})
        login = Login(request)
        with pytest.raises(HTTPUnauthorized):
            login.logout()

    def test_logout(self):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User
        from c2cgeoportal_geoportal.views.login import Login

        request = self._create_request_obj(path="/")
        request.user = DBSession.query(User).filter_by(username="__test_user1").one()
        response = Login(request).logout()
        assert response.status_int == 200
        assert response.body.decode("utf-8") == "true"

        request = self._create_request_obj(path="/")
        request.route_url = lambda url: "/dummy/route/url"
        request.user = DBSession.query(User).filter_by(username="__test_user1").one()
        response = Login(request).logout()
        assert response.status_int == 200
        assert response.body.decode("utf-8") == "true"

    def test_reset_password(self):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User
        from c2cgeoportal_geoportal.views.login import Login

        request = self._create_request_obj(POST={"login": "__test_user1"})
        user, username, password, _ = Login(request)._loginresetpassword()

        assert user.temp_password is not None
        assert username == "__test_user1"

        request = self._create_request_obj(POST={"login": username, "password": password})
        response = Login(request).login()
        assert response.status_int == 200
        assert json.loads(response.body.decode("utf-8")) == {
            "username": "__test_user1",
            "is_password_changed": False,
            "two_factor_enable": False,
        }

        request = self._create_request_obj(
            POST={
                "login": username,
                "oldPassword": password,
                "newPassword": "1234",
                "confirmNewPassword": "1234",
            }
        )
        response = Login(request).change_password()

        assert json.loads(response.body.decode("utf-8")) == {
            "username": "__test_user1",
            "email": "__test_user1@example.com",
            "is_intranet": False,
            "two_factor_enable": False,
            "roles": [{"name": "__test_role1", "id": self.role1_id}],
            "functionalities": {},
        }

        user = DBSession.query(User).filter(User.username == "__test_user1").first()
        self.assertIsNone(user.temp_password)
        self.assertIsNotNone(user.password)
        self.assertNotEqual(len(user.password), 0)

    def test_change_password_no_params(self):
        from pyramid.httpexceptions import HTTPBadRequest

        from c2cgeoportal_geoportal.views.login import Login

        request = self._create_request_obj(username="__test_user1", params={"lang": "en"}, POST={})
        login = Login(request)
        self.assertRaises(HTTPBadRequest, login.change_password)

    def test_change_password_wrong_old(self):
        from pyramid.httpexceptions import HTTPUnauthorized

        from c2cgeoportal_geoportal.views.login import Login

        request = self._create_request_obj(
            username="__test_user1",
            params={"lang": "en"},
            POST={"oldPassword": "wrong", "newPassword": "1234", "confirmNewPassword": "1234"},
        )
        login = Login(request)
        with pytest.raises(HTTPUnauthorized):
            login.change_password()

    def test_change_password_different(self):
        from pyramid.httpexceptions import HTTPBadRequest

        from c2cgeoportal_geoportal.views.login import Login

        request = self._create_request_obj(
            username="__test_user1",
            params={"lang": "en"},
            POST={"oldPassword": "__test_user1", "newPassword": "1234", "confirmNewPassword": "12345"},
        )
        login = Login(request)
        with pytest.raises(HTTPBadRequest):
            login.change_password()

    def test_change_password_good_is_password_changed(self):
        import crypt

        from c2cgeoportal_geoportal.views.login import Login

        request = self._create_request_obj(
            params={"lang": "en"},
            POST={
                "login": "__test_user1",
                "oldPassword": "__test_user1",
                "newPassword": "1234",
                "confirmNewPassword": "1234",
            },
        )

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User

        user = DBSession.query(User).filter_by(username="__test_user1").one()
        assert user.is_password_changed is False
        assert user._password == crypt.crypt("__test_user1", user._password)
        login = Login(request)
        self.assertNotEqual(login.change_password(), None)
        user = DBSession.query(User).filter_by(username="__test_user1").one()
        assert user.is_password_changed is True
        assert user._password == crypt.crypt("1234", user._password)

    def test_login_0(self):
        from tests import DummyRequest

        from c2cgeoportal_geoportal.views.login import Login

        request = DummyRequest()
        request.is_valid_referer = True
        request.user = None
        login = Login(request)

        request.path = "/for_test"
        response = login.loginform403()
        assert response["came_from"] == "/for_test"

        request.params = {"came_from": "/for_a_second_test"}
        login = Login(request)
        response = login.loginform()
        assert response["came_from"] == "/for_a_second_test"

        login = Login(request)
        request.params = {}
        response = login.loginform()
        assert response["came_from"] == "/"

        request.registry.settings = {
            "functionalities": {"available_in_templates": ["func"]},
            "admin_interface": {"available_functionalities": [{"name": "func"}]},
        }
        fill_tech_user_functionality("anonymous", (("func", "anon"), ("toto", "anon_value2")))
        fill_tech_user_functionality("registered", (("func", "reg"),))
        login = Login(request)
        self.assertEqual(login.loginuser()["functionalities"], {"func": ["anon"]})

        class R:
            id = 123

            def __init__(self, name, functionalities):
                self.name = name
                self.functionalities = functionalities

        class U:
            username = "__test_user"
            is_password_changed = True
            email = "info@example.com"
            settings_role = None

            def __init__(self, role="__test_role", functionalities=None):
                if functionalities is None:
                    functionalities = []
                self.roles = [R(role, functionalities)]

        request.user = U()
        login = Login(request)
        expected = {
            "username": "__test_user",
            "email": "info@example.com",
            "is_intranet": False,
            "two_factor_enable": False,
            "roles": [{"name": "__test_role", "id": 123}],
            "functionalities": {"func": ["reg"]},
        }
        self.assertEqual(login.loginuser(), expected)

        class F:
            name = "func"
            value = "value"

        request.user = U("__test_role2", [F()])
        login = Login(request)
        expected = {
            "username": "__test_user",
            "email": "info@example.com",
            "is_intranet": False,
            "two_factor_enable": False,
            "roles": [{"name": "__test_role2", "id": 123}],
            "functionalities": {"func": ["value"]},
        }
        self.assertEqual(login.loginuser(), expected)

    def test_intranet(self):
        from tests import DummyRequest

        from c2cgeoportal_geoportal.views.login import Login

        request = DummyRequest()
        request.registry.settings = {"intranet": {"networks": ["192.168.1.0/255.255.255.0"]}}
        request.user = None

        login = Login(request)
        self.assertEqual(
            login.loginuser(), {"is_intranet": False, "functionalities": {}, "two_factor_enable": False}
        )

        request.client_addr = "192.168.1.20"
        login = Login(request)
        self.assertEqual(
            login.loginuser(), {"is_intranet": True, "functionalities": {}, "two_factor_enable": False}
        )

        class G:
            id = 123

            def __init__(self, name, functionalities):
                self.name = name
                self.functionalities = functionalities

        class U:
            username = "__test_user"
            is_password_changed = True
            email = "info@example.com"

            def __init__(self, role="__test_role", functionalities=None):
                if functionalities is None:
                    functionalities = []
                self.roles = [G(role, functionalities)]

        request.user = U()

        login = Login(request)
        request.client_addr = "192.168.2.20"
        self.assertEqual(
            login.loginuser(),
            {
                "email": "info@example.com",
                "functionalities": {},
                "is_intranet": False,
                "roles": [{"id": 123, "name": "__test_role"}],
                "two_factor_enable": False,
                "username": "__test_user",
            },
        )

        login = Login(request)
        request.client_addr = "192.168.1.20"
        self.assertEqual(
            login.loginuser(),
            {
                "email": "info@example.com",
                "functionalities": {},
                "is_intranet": True,
                "roles": [{"id": 123, "name": "__test_role"}],
                "two_factor_enable": False,
                "username": "__test_user",
            },
        )
