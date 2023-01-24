# Copyright (c) 2021-2023, Camptocamp SA
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

# pylint: disable=missing-docstring,attribute-defined-outside-init,protected-access,import-outside-toplevel


import json
import logging
import urllib.parse
from unittest import TestCase

import pyramid.httpexceptions
import pyramid.testing
import pytest
import transaction
from tests.functional import cleanup_db, create_dummy_request, init_registry
from tests.functional import setup_common as setup_module  # pylint: disable=unused-import
from tests.functional import teardown_common as teardown_module  # pylint: disable=unused-import

LOG = logging.getLogger(__name__)


class TestLoginView(TestCase):
    def setup_method(self, _) -> None:
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None  # pylint: disable=invalid-name
        self._tables = []

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import OAuth2Client, User

        user1 = User(username="__test_user1", password="__test_user1")
        user1.is_password_changed = True
        user1.email = "__test_user1@example.com"

        user2 = User(username="__test_user2", password="__test_user2")
        user2.email = "__test_user2@example.com"

        client = OAuth2Client()
        client.client_id = "qgis"
        client.secret = "1234"
        client.redirect_uri = "http://127.0.0.1:7070/"

        session = DBSession()

        session.add_all([user1, user2, client])
        session.flush()
        transaction.commit()

    def teardown_method(self, _) -> None:
        cleanup_db()

    def test_oauth2_protocol_login_form(self) -> None:
        from c2cgeoportal_geoportal.views.login import Login

        # Test login form
        request = create_dummy_request()
        request.params = {
            "client_id": "qgis",
            "redirect_uri": "http://127.0.0.1:7070/",
            "response_type": "token",
        }
        response = Login(request).oauth2loginform()
        assert response["login_params"] == {
            "client_id": "qgis",
            "redirect_uri": "http://127.0.0.1:7070/",
            "response_type": "token",
            "type": "oauth2",
        }

    def test_oauth2_protocol_test_login_get_token_is_login(self) -> None:
        from c2cgeoportal_geoportal.views.login import Login

        # Test login
        url = None
        request = create_dummy_request(authentication=True)
        request.POST = {"login": "__test_user1", "password": "__test_user1"}
        request.GET = {
            "client_id": "qgis",
            # "client_secret": "1234",
            "redirect_uri": "http://127.0.0.1:7070/",
            "response_type": "code",
            "type": "oauth2",
        }
        request.method = "POST"
        request.body = ""
        with pytest.raises(pyramid.httpexceptions.HTTPFound) as exc_info:
            Login(request).login()
        url = exc_info.value.headers["Location"]
        url_split = urllib.parse.urlsplit(url)
        query = dict(urllib.parse.parse_qsl(url_split.query))
        assert "code" in query
        code = query["code"]

        # Test get token
        request = create_dummy_request(authentication=True)
        request.POST = {
            "client_id": "qgis",
            "client_secret": "1234",
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": "http://127.0.0.1:7070/",
        }
        request.body = urllib.parse.urlencode(request.POST)
        request.method = "POST"
        response = Login(request).oauth2token()
        assert response.headers["Content-Type"] == "application/json"
        assert response.headers["Pragma"] == "no-cache"
        assert response.headers["Vary"] == "Origin, Cookie"
        assert response.headers["Cache-Control"] == "max-age=10, no-store, public"
        data = json.loads(response.body)
        assert set(data.keys()) == {"access_token", "expires_in", "token_type", "refresh_token"}
        assert data["expires_in"] == 3600
        assert data["token_type"] == "Bearer"
        access_token = data["access_token"]

        # Test is login
        request = create_dummy_request(authentication=True)
        request.headers["Authorization"] = "Bearer " + access_token
        response = Login(request).loginuser()
        assert set(response.keys()) == {
            "functionalities",
            "is_intranet",
            "two_factor_enable",
            "username",
            "email",
            "roles",
        }
        assert response["username"] == "__test_user1"

    #    def test_oauth2_protocol_test_login_wrong_code(self) -> None:
    #        from c2cgeoportal_geoportal.views.login import Login
    #
    #        # Test login
    #        url = None
    #        request = create_dummy_request(authentication=True)
    #        request.POST = {"login": "__test_user1", "password": "__test_user1"}
    #        request.GET = {
    #            "client_id": "qgis",
    #            "client_secret": "1111",
    #            "redirect_uri": "http://127.0.0.1:7070/",
    #            "response_type": "code",
    #            "type": "oauth2",
    #        }
    #        request.method = "POST"
    #        request.body = ""
    #        with pytest.raises(pyramid.httpexceptions.HTTPUnautorised) as exc_info:
    #            Login(request).login()

    def test_oauth2_protocol_test_login_get_token_wrong_client_secret(self) -> None:
        from c2cgeoportal_geoportal.views.login import Login

        # Test login
        url = None
        request = create_dummy_request(authentication=True)
        request.POST = {"login": "__test_user1", "password": "__test_user1"}
        request.GET = {
            "client_id": "qgis",
            # "client_secret": "1234",
            "redirect_uri": "http://127.0.0.1:7070/",
            "response_type": "code",
            "type": "oauth2",
        }
        request.method = "POST"
        request.body = ""
        with pytest.raises(pyramid.httpexceptions.HTTPFound) as exc_info:
            Login(request).login()
        url = exc_info.value.headers["Location"]
        url_split = urllib.parse.urlsplit(url)
        query = dict(urllib.parse.parse_qsl(url_split.query))
        assert "code" in query
        code = query["code"]

        # Test get token
        request = create_dummy_request(authentication=True)
        request.POST = {
            "client_id": "qgis",
            "client_secret": "1111",
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": "http://127.0.0.1:7070/",
        }
        request.body = urllib.parse.urlencode(request.POST)
        request.method = "POST"
        with pytest.raises(pyramid.httpexceptions.HTTPUnauthorized):
            Login(request).oauth2token()

    def test_oauth2_protocol_test_get_token_wrong_code(self) -> None:
        from c2cgeoportal_geoportal.views.login import Login

        # Test get token
        request = create_dummy_request(authentication=True)
        request.POST = {
            "client_id": "qgis",
            "client_secret": "1234",
            "code": "1111",
            "grant_type": "authorization_code",
            "redirect_uri": "http://127.0.0.1:7070/",
        }
        request.body = urllib.parse.urlencode(request.POST)
        request.method = "POST"
        with pytest.raises(pyramid.httpexceptions.HTTPBadRequest):
            Login(request).oauth2token()

    def test_oauth2_protocol_test_login_get_token_refresh_token_is_login(self) -> None:
        from c2cgeoportal_geoportal.views.login import Login

        # Test login
        url = None
        request = create_dummy_request(authentication=True)
        request.POST = {"login": "__test_user1", "password": "__test_user1"}
        request.GET = {
            "client_id": "qgis",
            # "client_secret": "1234",
            "redirect_uri": "http://127.0.0.1:7070/",
            "response_type": "code",
            "type": "oauth2",
        }
        request.method = "POST"
        request.body = ""
        with pytest.raises(pyramid.httpexceptions.HTTPFound) as exc_info:
            Login(request).login()
        url = exc_info.value.headers["Location"]
        url_split = urllib.parse.urlsplit(url)
        query = dict(urllib.parse.parse_qsl(url_split.query))
        assert "code" in query
        code = query["code"]

        # Test get token
        request = create_dummy_request(authentication=True)
        request.POST = {
            "client_id": "qgis",
            "client_secret": "1234",
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": "http://127.0.0.1:7070/",
        }
        request.body = urllib.parse.urlencode(request.POST)
        request.method = "POST"
        response = Login(request).oauth2token()
        assert response.headers["Content-Type"] == "application/json"
        assert response.headers["Pragma"] == "no-cache"
        assert response.headers["Vary"] == "Origin, Cookie"
        assert response.headers["Cache-Control"] == "max-age=10, no-store, public"
        data = json.loads(response.body)
        assert set(data.keys()) == {"access_token", "expires_in", "token_type", "refresh_token"}
        assert data["expires_in"] == 3600
        assert data["token_type"] == "Bearer"
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]

        # Test refresh token
        request = create_dummy_request()
        request.POST = {
            "client_id": "qgis",
            "client_secret": "1234",
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        request.body = urllib.parse.urlencode(request.POST)
        request.method = "POST"
        response = Login(request).oauth2token()
        data = json.loads(response.body)
        assert set(data.keys()) == {"access_token", "expires_in", "token_type", "refresh_token", "scope"}
        assert data["expires_in"] == 3600
        assert data["token_type"] == "Bearer"
        assert data["access_token"] != access_token
        assert data["refresh_token"] != refresh_token
        access_token = data["access_token"]

        # Test is login with new token
        request = create_dummy_request()
        request.headers["Authorization"] = "Bearer " + access_token
        response = Login(request).loginuser()
        assert set(response.keys()) == {
            "functionalities",
            "is_intranet",
            "two_factor_enable",
            "username",
            "email",
            "roles",
        }
        assert response["username"] == "__test_user1"

    def test_oauth2_protocol_test_login_get_token_refresh_token_wrong_code(self) -> None:
        from c2cgeoportal_geoportal.views.login import Login

        # Test login
        url = None
        request = create_dummy_request(authentication=True)
        request.POST = {"login": "__test_user1", "password": "__test_user1"}
        request.GET = {
            "client_id": "qgis",
            # "client_secret": "1234",
            "redirect_uri": "http://127.0.0.1:7070/",
            "response_type": "code",
            "type": "oauth2",
        }
        request.method = "POST"
        request.body = ""
        with pytest.raises(pyramid.httpexceptions.HTTPFound) as exc_info:
            Login(request).login()
        url = exc_info.value.headers["Location"]
        url_split = urllib.parse.urlsplit(url)
        query = dict(urllib.parse.parse_qsl(url_split.query))
        assert "code" in query
        code = query["code"]

        # Test get token
        request = create_dummy_request(authentication=True)
        request.POST = {
            "client_id": "qgis",
            "client_secret": "1234",
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": "http://127.0.0.1:7070/",
        }
        request.body = urllib.parse.urlencode(request.POST)
        request.method = "POST"
        response = Login(request).oauth2token()
        assert response.headers["Content-Type"] == "application/json"
        assert response.headers["Pragma"] == "no-cache"
        assert response.headers["Vary"] == "Origin, Cookie"
        assert response.headers["Cache-Control"] == "max-age=10, no-store, public"
        data = json.loads(response.body)
        assert set(data.keys()) == {"access_token", "expires_in", "token_type", "refresh_token"}
        assert data["expires_in"] == 3600
        assert data["token_type"] == "Bearer"
        data["access_token"]
        refresh_token = data["refresh_token"]

        # Test refresh token
        request = create_dummy_request()
        request.POST = {
            "client_id": "qgis",
            "client_secret": "1111",
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        request.body = urllib.parse.urlencode(request.POST)
        request.method = "POST"
        with pytest.raises(pyramid.httpexceptions.HTTPUnauthorized):
            Login(request).oauth2token()

    def test_oauth2_protocol_test_refresh_token_wrong_token(self) -> None:
        from c2cgeoportal_geoportal.views.login import Login

        # Test refresh token
        request = create_dummy_request()
        request.POST = {
            "client_id": "qgis",
            "client_secret": "1234",
            "grant_type": "refresh_token",
            "refresh_token": "1111",
        }
        request.body = urllib.parse.urlencode(request.POST)
        request.method = "POST"
        with pytest.raises(pyramid.httpexceptions.HTTPBadRequest):
            Login(request).oauth2token()

    def test_is_login_wrong_token(self) -> None:
        from c2cgeoportal_geoportal.views.login import Login

        # Test is login with new token
        request = create_dummy_request()
        request.headers["Authorization"] = "Bearer 1111"
        response = Login(request).loginuser()
        assert set(response.keys()) == {
            "functionalities",
            "is_intranet",
            "two_factor_enable",
        }

    def test_oauth2_2fa(self) -> None:
        from c2cgeoportal_geoportal.views.login import Login

        url = None
        request = create_dummy_request()
        request.POST = {"login": "__test_user2", "password": "__test_user2"}
        request.GET = {
            "client_id": "qgis",
            # "client_secret": "1234",
            "redirect_uri": "http://127.0.0.1:7070/",
            "response_type": "code",
            "type": "oauth2",
        }
        request.method = "POST"
        request.body = ""
        pyramid.testing.setUp(request=request, registry=init_registry())
        request.registry.settings["authentication"] = {"two_factor": True}

        with pytest.raises(pyramid.httpexceptions.HTTPFound) as exc_info:
            Login(request).login()
        url = exc_info.value.headers["Location"]
        assert url == "http://example.com/notlogin/view?"

    #    def test_oauth2_2fa_wrong_code(self) -> None:
    #        from c2cgeoportal_geoportal.views.login import Login
    #
    #        url = None
    #        request = create_dummy_request()
    #        request.POST = {"login": "__test_user2", "password": "__test_user2"}
    #        request.GET = {
    #            "client_id": "qgis",
    #            "client_secret": "1111",
    #            "redirect_uri": "http://127.0.0.1:7070/",
    #            "response_type": "code",
    #            "type": "oauth2",
    #        }
    #        request.method = "POST"
    #        request.body = ""
    #        pyramid.testing.setUp(request=request, registry=init_registry())
    #        request.registry.settings["authentication"] = {"two_factor": True}
    #        assert False

    def test_notlogin(self) -> None:
        from c2cgeoportal_geoportal.views.login import Login

        request = create_dummy_request()
        response = Login(request).notlogin()
        assert response == {"lang": "fr"}
