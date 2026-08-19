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


@pytest.fixture(scope="class")
def insert_roles_test_data(dbsession):
    from c2cgeoportal_commons.models.main import Role
    from c2cgeoportal_commons.models.static import User

    role = Role("secretary")

    user = User("user1", roles=[role])

    t = dbsession.begin_nested()

    dbsession.add(role)
    dbsession.add(user)
    dbsession.flush()

    yield

    t.rollback()


@pytest.mark.usefixtures("insert_roles_test_data", "transact")
class TestRole:
    def test_select(self, dbsession) -> None:
        from c2cgeoportal_commons.models.main import Role

        roles = dbsession.query(Role).all()
        assert len(roles) == 1, "querying for roles"
        assert roles[0].name == "secretary", "role from test data is secretary"

    def test_delete(self, dbsession) -> None:
        from c2cgeoportal_commons.models.main import Role
        from c2cgeoportal_commons.models.static import user_role

        roles = dbsession.query(Role).all()
        dbsession.delete(roles[0])
        roles = dbsession.query(Role).all()
        assert len(roles) == 0, "removed a role"
        assert dbsession.query(user_role).count() == 0

    def test_delete_cascade_to_tsearch(self, dbsession) -> None:
        from sqlalchemy import func

        from c2cgeoportal_commons.models.main import FullTextSearch, Role

        role = dbsession.query(Role).filter(Role.name == "secretary").one()
        role_id = role.id

        fts = FullTextSearch()
        fts.label = "Text to search"
        fts.role = role
        fts.ts = func.to_tsvector("french", fts.label)
        dbsession.add(fts)
        dbsession.flush()

        dbsession.delete(role)
        dbsession.flush()

        assert dbsession.query(FullTextSearch).filter(FullTextSearch.role_id == role_id).count() == 0
