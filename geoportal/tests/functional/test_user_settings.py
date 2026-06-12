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


import json
from io import BytesIO

import pytest

from tests.functional import create_dummy_request


@pytest.fixture
def settings_setup(dbsession, transact):
    from c2cgeoportal_commons.models.main import Role
    from c2cgeoportal_commons.models.static import User

    del transact

    role = Role(name="__test_role")
    user = User(username="__test_user", password="__test_user", settings_role=role, roles=[role])
    user.email = "__test_user@example.com"
    dbsession.add_all([user])
    dbsession.flush()
    return user


class TestUserSettingsView:
    @staticmethod
    def _create_request_obj(username=None, body=None, additional_settings=None):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User

        request = create_dummy_request(authentication=True, additional_settings=additional_settings)

        if username is not None:
            request.user = DBSession.query(User).filter_by(username=username).one()
        if body is not None:
            request.body = body
            request.body_file = BytesIO(body)
            request.content_length = len(body)
        return request

    def test_get_initial_settings_returns_empty_object(self, settings_setup) -> None:
        del settings_setup
        from c2cgeoportal_geoportal.views.user_settings import UserSettings

        request = self._create_request_obj(username="__test_user")
        response = UserSettings(request).get()
        assert response == {}

    def test_get_requires_authentication(self, settings_setup) -> None:
        del settings_setup
        from pyramid.httpexceptions import HTTPUnauthorized

        from c2cgeoportal_geoportal.views.user_settings import UserSettings

        request = self._create_request_obj()
        with pytest.raises(HTTPUnauthorized):
            UserSettings(request).get()

    def test_post_round_trip_and_overwrite(self, settings_setup) -> None:
        del settings_setup
        from c2cgeoportal_geoportal.views.user_settings import UserSettings

        request = self._create_request_obj(username="__test_user", body=b'{"a": 1, "b": {"c": true}}')
        response = UserSettings(request).update()
        assert response == {"a": 1, "b": {"c": True}}

        request = self._create_request_obj(username="__test_user")
        assert UserSettings(request).get() == {"a": 1, "b": {"c": True}}

        request = self._create_request_obj(username="__test_user", body=b'{"theme": "night"}')
        response = UserSettings(request).update()
        assert response == {"theme": "night"}

        request = self._create_request_obj(username="__test_user")
        assert UserSettings(request).get() == {"theme": "night"}

    def test_post_requires_json_object(self, settings_setup) -> None:
        del settings_setup
        from pyramid.httpexceptions import HTTPBadRequest

        from c2cgeoportal_geoportal.views.user_settings import UserSettings

        request = self._create_request_obj(username="__test_user", body=b'["not", "an", "object"]')
        with pytest.raises(HTTPBadRequest):
            UserSettings(request).update()

    def test_post_invalid_json(self, settings_setup) -> None:
        del settings_setup
        from pyramid.httpexceptions import HTTPBadRequest

        from c2cgeoportal_geoportal.views.user_settings import UserSettings

        request = self._create_request_obj(username="__test_user", body=b"not-json")
        with pytest.raises(HTTPBadRequest):
            UserSettings(request).update()

    def test_post_too_large(self, settings_setup) -> None:
        del settings_setup
        from pyramid.httpexceptions import HTTPRequestEntityTooLarge

        from c2cgeoportal_geoportal.views.user_settings import UserSettings

        body = json.dumps({"data": "x" * 200}).encode()
        request = self._create_request_obj(
            username="__test_user",
            body=body,
            additional_settings={"user_settings": {"max_payload_size": 100}},
        )

        with pytest.raises(HTTPRequestEntityTooLarge):
            UserSettings(request).update()

    def test_post_invalid_settings_configuration(self, settings_setup) -> None:
        del settings_setup
        from pyramid.httpexceptions import HTTPInternalServerError

        from c2cgeoportal_geoportal.views.user_settings import UserSettings

        request = self._create_request_obj(
            username="__test_user",
            body=b"{}",
            additional_settings={"user_settings": {"max_payload_size": "wrong"}},
        )

        with pytest.raises(HTTPInternalServerError):
            UserSettings(request).update()
