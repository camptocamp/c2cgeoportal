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

import pyotp
import pyramid.httpexceptions
import pytest
import transaction
from pyramid import testing
from tests.functional import cleanup_db, create_dummy_request
from tests.functional import setup_common as setup_module  # noqa, pylint: disable=unused-import
from tests.functional import setup_db
from tests.functional import teardown_common as teardown_module  # noqa, pylint: disable=unused-import

LOG = logging.getLogger(__name__)


class Test2faView(TestCase):
    def setup_method(self, _):
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None  # pylint: disable=invalid-name
        self._tables = []

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User

        setup_db()

        user = User(username="__test_user", password="__test_user")
        user.email = "__test_user@example.com"
        DBSession.add(user)
        testing.setUp().testing_securitypolicy(remember_result=[("Cookie", "Test")])
        transaction.commit()

    def teardown_method(self, _):
        testing.tearDown()
        cleanup_db()

    @staticmethod
    def _create_request_obj(username=None, **kwargs):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User

        request = create_dummy_request(**kwargs)
        request.registry.settings.update(
            {"authentication": {"two_factor": True, "two_factor_issuer_name": "CI"}}
        )

        if username is not None:
            request.user = DBSession.query(User).filter_by(username=username).one()

        return request

    def test_new_user(self):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User
        from c2cgeoportal_geoportal.views.login import Login

        request = self._create_request_obj(POST={"login": "__test_user", "password": "__test_user"})
        response = Login(request).login()
        response_json = json.loads(response.body.decode("utf-8"))
        assert "Cookie" not in dict(response.headers)
        totp = pyotp.TOTP(response_json["two_factor_totp_secret"])
        del response_json["two_factor_totp_secret"]
        del response_json["otp_uri"]
        assert response_json == {
            "username": "__test_user",
            "is_password_changed": False,
            "two_factor_enable": True,
        }
        user = DBSession.query(User).filter_by(username="__test_user").one()
        assert user.is_password_changed is False

        request = self._create_request_obj(
            POST={
                "login": "__test_user",
                "oldPassword": "__test_user",
                "newPassword": "1234",
                "confirmNewPassword": "1234",
                "otp": totp.now(),
            }
        )
        response = Login(request).change_password()
        assert "Cookie" in dict(response.headers)
        assert set(user.tech_data.keys()) == {"2fa_totp_secret"}
        assert user.is_password_changed is True
        assert json.loads(response.body.decode("utf-8")) == {
            "email": "__test_user@example.com",
            "functionalities": {},
            "is_intranet": False,
            "roles": [],
            "two_factor_enable": True,
            "username": "__test_user",
        }

        request = self._create_request_obj(
            POST={"login": "__test_user", "password": "1234", "otp": totp.now()}
        )
        response = Login(request).login()
        assert "Cookie" in dict(response.headers)
        assert json.loads(response.body.decode("utf-8")) == {
            "username": "__test_user",
            "email": "__test_user@example.com",
            "is_intranet": False,
            "two_factor_enable": True,
            "roles": [],
            "functionalities": {},
        }

    def test_user_reset_password(self):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User
        from c2cgeoportal_geoportal.views.login import Login

        user = DBSession.query(User).filter_by(username="__test_user").one()
        _2fa_totp_secret = pyotp.random_base32()
        totp = pyotp.TOTP(_2fa_totp_secret)
        user.tech_data["2fa_totp_secret"] = _2fa_totp_secret
        user.is_password_changed = True

        request = self._create_request_obj(POST={"login": "__test_user", "otp": totp.now()})
        _, _, password, error = Login(request)._loginresetpassword()

        request = self._create_request_obj(
            POST={"login": "__test_user", "password": password, "otp": totp.now()}
        )
        response = Login(request).login()
        response_json = json.loads(response.body.decode("utf-8"))
        assert "Cookie" not in dict(response.headers)
        totp = pyotp.TOTP(response_json["two_factor_totp_secret"])
        del response_json["two_factor_totp_secret"]
        del response_json["otp_uri"]
        assert response_json == {
            "username": "__test_user",
            "is_password_changed": False,
            "two_factor_enable": True,
        }

        request = self._create_request_obj(
            POST={
                "login": "__test_user",
                "oldPassword": password,
                "newPassword": "1234",
                "confirmNewPassword": "1234",
                "otp": totp.now(),
            }
        )
        response = Login(request).change_password()
        assert "Cookie" in dict(response.headers)
        assert set(user.tech_data.keys()) == {"2fa_totp_secret"}
        assert user.is_password_changed is True
        assert json.loads(response.body.decode("utf-8")) == {
            "email": "__test_user@example.com",
            "functionalities": {},
            "is_intranet": False,
            "roles": [],
            "two_factor_enable": True,
            "username": "__test_user",
        }

        request = self._create_request_obj(
            POST={"login": "__test_user", "password": "1234", "otp": totp.now()}
        )
        response = Login(request).login()
        assert "Cookie" in dict(response.headers)
        assert json.loads(response.body.decode("utf-8")) == {
            "username": "__test_user",
            "email": "__test_user@example.com",
            "is_intranet": False,
            "two_factor_enable": True,
            "roles": [],
            "functionalities": {},
        }

    def test_change_password(self):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User
        from c2cgeoportal_geoportal.views.login import Login

        user = DBSession.query(User).filter_by(username="__test_user").one()
        _2fa_totp_secret = pyotp.random_base32()
        totp = pyotp.TOTP(_2fa_totp_secret)
        user.tech_data["2fa_totp_secret"] = _2fa_totp_secret
        user.is_password_changed = True

        request = self._create_request_obj(
            username="__test_user",
            POST={
                "oldPassword": "__test_user",
                "newPassword": "1234",
                "confirmNewPassword": "1234",
                "otp": totp.now(),
            },
        )
        response = Login(request).change_password()
        assert "Cookie" in dict(response.headers)
        assert set(user.tech_data.keys()) == {"2fa_totp_secret"}
        assert user.is_password_changed is True
        assert json.loads(response.body.decode("utf-8")) == {
            "email": "__test_user@example.com",
            "functionalities": {},
            "is_intranet": False,
            "roles": [],
            "two_factor_enable": True,
            "username": "__test_user",
        }

        request = self._create_request_obj(
            POST={"login": "__test_user", "password": "1234", "otp": totp.now()}
        )
        response = Login(request).login()
        assert "Cookie" in dict(response.headers)
        assert json.loads(response.body.decode("utf-8")) == {
            "username": "__test_user",
            "email": "__test_user@example.com",
            "is_intranet": False,
            "two_factor_enable": True,
            "roles": [],
            "functionalities": {},
        }

    def test_admin_reset(self):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User

        user = DBSession.query(User).filter_by(username="__test_user").one()
        original_2fa_totp_secret = pyotp.random_base32()
        user.tech_data["2fa_totp_secret"] = original_2fa_totp_secret

        self.test_new_user()

        assert original_2fa_totp_secret != user.tech_data["2fa_totp_secret"]

    def test_wrong_firstlogin(self):
        from c2cgeoportal_geoportal.views.login import Login

        request = self._create_request_obj(POST={"login": "__test_user"})
        with pytest.raises(pyramid.httpexceptions.HTTPBadRequest):
            Login(request).login()

        request = self._create_request_obj(POST={"password": "__test_user"})
        with pytest.raises(pyramid.httpexceptions.HTTPBadRequest):
            Login(request).login()

        request = self._create_request_obj(POST={"login": "__test_user", "password": "toto"})
        with pytest.raises(pyramid.httpexceptions.HTTPUnauthorized):
            Login(request).login()

    def test_wrong_login(self):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User
        from c2cgeoportal_geoportal.views.login import Login

        user = DBSession.query(User).filter_by(username="__test_user").one()
        _2fa_totp_secret = pyotp.random_base32()
        totp = pyotp.TOTP(_2fa_totp_secret)
        user.tech_data["2fa_totp_secret"] = _2fa_totp_secret
        user.is_password_changed = True

        request = self._create_request_obj(POST={"password": "__test_user", "otp": totp.now()})
        with pytest.raises(pyramid.httpexceptions.HTTPBadRequest):
            Login(request).login()

        request = self._create_request_obj(POST={"login": "__test_user", "password": "__test_user"})
        with pytest.raises(pyramid.httpexceptions.HTTPBadRequest):
            Login(request).login()

        request = self._create_request_obj(
            POST={"login": "__test_user", "password": "toto", "otp": totp.now()}
        )
        with pytest.raises(pyramid.httpexceptions.HTTPUnauthorized):
            Login(request).login()

        request = self._create_request_obj(
            POST={"login": "__test_user", "password": "__test_user", "otp": "toto"}
        )
        with pytest.raises(pyramid.httpexceptions.HTTPUnauthorized):
            Login(request).login()

        request = self._create_request_obj(POST={"login": "__test_user", "otp": totp.now()})
        with pytest.raises(pyramid.httpexceptions.HTTPBadRequest):
            Login(request).login()

    def test_wrong_change_password(self):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User
        from c2cgeoportal_geoportal.views.login import Login

        user = DBSession.query(User).filter_by(username="__test_user").one()
        _2fa_totp_secret = pyotp.random_base32()
        totp = pyotp.TOTP(_2fa_totp_secret)
        user.tech_data["2fa_totp_secret"] = _2fa_totp_secret

        request = self._create_request_obj(
            POST={
                "oldPassword": "__test_user",
                "newPassword": "1234",
                "confirmNewPassword": "1234",
                "otp": totp.now(),
            }
        )
        with pytest.raises(pyramid.httpexceptions.HTTPBadRequest):
            Login(request).change_password()

        request = self._create_request_obj(
            POST={
                "login": "__test_user",
                "newPassword": "1234",
                "confirmNewPassword": "1234",
                "otp": totp.now(),
            }
        )
        with pytest.raises(pyramid.httpexceptions.HTTPBadRequest):
            Login(request).change_password()

        request = self._create_request_obj(
            POST={
                "login": "__test_user",
                "oldPassword": "__test_user",
                "confirmNewPassword": "1234",
                "otp": totp.now(),
            }
        )
        with pytest.raises(pyramid.httpexceptions.HTTPBadRequest):
            Login(request).change_password()

        request = self._create_request_obj(
            POST={
                "login": "__test_user",
                "oldPassword": "__test_user",
                "newPassword": "1234",
                "otp": totp.now(),
            }
        )
        with pytest.raises(pyramid.httpexceptions.HTTPBadRequest):
            Login(request).change_password()

        request = self._create_request_obj(
            POST={
                "login": "__test_user",
                "oldPassword": "__test_user",
                "newPassword": "1234",
                "confirmNewPassword": "1234",
            }
        )
        with pytest.raises(pyramid.httpexceptions.HTTPBadRequest):
            Login(request).change_password()

        request = self._create_request_obj(
            POST={
                "login": "__test_user_unexistiong",
                "oldPassword": "__test_user",
                "newPassword": "1234",
                "confirmNewPassword": "1234",
                "otp": totp.now(),
            }
        )
        with pytest.raises(pyramid.httpexceptions.HTTPUnauthorized):
            Login(request).change_password()

        request = self._create_request_obj(
            POST={
                "login": "__test_user",
                "oldPassword": "__test_user_wrong",
                "newPassword": "1234",
                "confirmNewPassword": "1234",
                "otp": totp.now(),
            }
        )
        with pytest.raises(pyramid.httpexceptions.HTTPUnauthorized):
            Login(request).change_password()

        request = self._create_request_obj(
            POST={
                "login": "__test_user",
                "oldPassword": "__test_user",
                "newPassword": "111",
                "confirmNewPassword": "222",
                "otp": totp.now(),
            }
        )
        with pytest.raises(pyramid.httpexceptions.HTTPBadRequest):
            Login(request).change_password()

        request = self._create_request_obj(
            POST={
                "login": "__test_user",
                "oldPassword": "__test_user",
                "newPassword": "1234",
                "confirmNewPassword": "1234",
                "otp": "wrong",
            }
        )
        with pytest.raises(pyramid.httpexceptions.HTTPUnauthorized):
            Login(request).change_password()

    def test_wrong_login_change_password(self):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User
        from c2cgeoportal_geoportal.views.login import Login

        user = DBSession.query(User).filter_by(username="__test_user").one()
        user.tech_data["2fa_totp_secret"] = pyotp.random_base32()
        user.is_password_changed = True

        request = self._create_request_obj(
            username="__test_user", POST={"newPassword": "1234", "confirmNewPassword": "1234"}
        )
        with pytest.raises(pyramid.httpexceptions.HTTPBadRequest):
            Login(request).change_password()

        request = self._create_request_obj(
            username="__test_user", POST={"oldPassword": "__test_user", "confirmNewPassword": "1234"}
        )
        with pytest.raises(pyramid.httpexceptions.HTTPBadRequest):
            Login(request).change_password()

        request = self._create_request_obj(
            username="__test_user", POST={"oldPassword": "__test_user", "newPassword": "1234"}
        )
        with pytest.raises(pyramid.httpexceptions.HTTPBadRequest):
            Login(request).change_password()

        request = self._create_request_obj(
            username="__test_user",
            POST={"oldPassword": "__test_user", "newPassword": "111", "confirmNewPassword": "222"},
        )
        with pytest.raises(pyramid.httpexceptions.HTTPBadRequest):
            Login(request).change_password()

    def test_wrong_loginresetpassword(self):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User
        from c2cgeoportal_geoportal.views.login import Login

        user = DBSession.query(User).filter_by(username="__test_user").one()
        _2fa_totp_secret = pyotp.random_base32()
        totp = pyotp.TOTP(_2fa_totp_secret)
        user.tech_data["2fa_totp_secret"] = _2fa_totp_secret
        user.is_password_changed = True

        request = self._create_request_obj(POST={"otp": totp.now()})
        with pytest.raises(pyramid.httpexceptions.HTTPBadRequest):
            Login(request).loginresetpassword()

        request = self._create_request_obj(POST={"login": "__test_user_unexisting"})
        with pytest.raises(pyramid.httpexceptions.HTTPUnauthorized):
            Login(request).loginresetpassword()
