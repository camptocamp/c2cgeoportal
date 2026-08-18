# Copyright (c) 2025-2026, Camptocamp SA
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


# pylint: disable=no-self-use

import pytest
from pyramid.view import view_config


@pytest.fixture(scope="class")
def insert_users_test_data(dbsession):
    from c2cgeoportal_commons.models.static import User

    user = User("babar")
    dbsession.begin_nested()
    dbsession.add(user)
    dbsession.flush()
    yield
    dbsession.rollback()


@view_config(route_name="user_add", renderer="./test_learn.jinja2")
def view_committing_user(request):
    from c2cgeoportal_commons.models.static import User

    user = User("momo")
    t = request.dbsession.begin_nested()
    request.dbsession.add(user)
    t.commit()
    return {}


@view_config(route_name="users_nb", renderer="./test_learn.jinja2")
def view_displaying_users_nb(request):
    from c2cgeoportal_commons.models.static import User

    users = request.dbsession.query(User).all()
    username = "None"
    if len(users) > 0:
        username = users[0].username
    return {"size": len(users), "first": username, "project": "c2cgeoportal_admin"}


@pytest.mark.usefixtures("insert_users_test_data", "transact")
class TestUser:
    @pytest.mark.usefixtures("test_app")
    def test_view_rendering_in_app(self, dbsession, test_app) -> None:
        res = test_app.get("/users_nb", status=200)
        expected = (
            "['users len is: 1', <br/>, 'first is: babar', <br/>, 'project is: c2cgeoportal_admin', <br/>]"
        )
        assert expected == str(res.html.contents)

    @pytest.mark.usefixtures("test_app")
    def test_commit_in_app(self, dbsession, test_app) -> None:
        res = test_app.get("/user_add", status=200)
        res = test_app.get("/users_nb", status=200)
        expected = (
            "['users len is: 2', <br/>, 'first is: babar', <br/>, 'project is: c2cgeoportal_admin', <br/>]"
        )
        assert expected == str(res.html.contents)

    @pytest.mark.usefixtures("test_app")
    def test_commit_in_app_rollbacked(self, dbsession, test_app) -> None:
        res = test_app.get("/users_nb", status=200)
        expected = (
            "['users len is: 1', <br/>, 'first is: babar', <br/>, 'project is: c2cgeoportal_admin', <br/>]"
        )
        assert expected == str(res.html.contents)
