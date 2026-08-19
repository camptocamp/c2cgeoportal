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
import sqlalchemy.exc


@pytest.fixture(scope="class")
def insert_users_test_data(dbsession):
    from c2cgeoportal_commons.models.main import Role
    from c2cgeoportal_commons.models.static import User

    user = User("babar")
    user.roles = [Role(name="Role1"), Role(name="Role2")]
    t = dbsession.begin_nested()
    dbsession.add(user)
    dbsession.flush()
    yield
    try:
        t.rollback()
    except sqlalchemy.exc.ResourceClosedError as error:
        print(error)


@pytest.mark.usefixtures("insert_users_test_data", "transact")
class TestUser:
    def test_select(self, dbsession) -> None:
        from c2cgeoportal_commons.models.static import User

        users = dbsession.query(User).all()
        assert len(users) == 1, "querying for users"
        assert users[0].username == "babar", "user from test data is babar"
        assert len(users[0].roles) == 2

    def test_remove(self, dbsession) -> None:
        from c2cgeoportal_commons.models.static import User, user_role

        users = dbsession.query(User).all()
        dbsession.delete(users[0])
        users = dbsession.query(User).all()
        assert len(users) == 0, "removed a user"
        assert dbsession.query(user_role).count() == 0

    def test_add(self, dbsession) -> None:
        from c2cgeoportal_commons.models.main import Role
        from c2cgeoportal_commons.models.static import User, user_role

        user = User(username="momo")
        user.roles = [Role(name="Role3")]
        dbsession.begin_nested()
        dbsession.add(user)
        assert dbsession.query(User).count() == 2, "added a user"
        dbsession.expire(user)
        assert user.username == "momo", "added user is momo"
        assert len(user.roles) == 1
        assert user.roles[0].name == "Role3"
        assert dbsession.query(user_role).filter(user_role.c.user_id == user.id).count() == 1

    @staticmethod
    def test_edit(dbsession):
        from c2cgeoportal_commons.models.main import Role
        from c2cgeoportal_commons.models.static import User, user_role

        user = dbsession.query(User).first()
        assert len(user.roles) == 2
        user.roles = [Role(name="Role4")]
        dbsession.flush()
        dbsession.expire(user)
        assert len(user.roles) == 1
        assert user.roles[0].name == "Role4"
        assert dbsession.query(user_role).filter(user_role.c.user_id == user.id).count() == 1
