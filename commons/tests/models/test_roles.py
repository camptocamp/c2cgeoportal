# pylint: disable=no-self-use

import pytest


@pytest.fixture(scope="class")
@pytest.mark.usefixtures("dbsession")
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
    def test_select(self, dbsession):
        from c2cgeoportal_commons.models.main import Role

        roles = dbsession.query(Role).all()
        assert len(roles) == 1, "querying for roles"
        assert roles[0].name == "secretary", "role from test data is secretary"

    def test_delete(self, dbsession):
        from c2cgeoportal_commons.models.main import Role
        from c2cgeoportal_commons.models.static import user_role

        roles = dbsession.query(Role).all()
        dbsession.delete(roles[0])
        roles = dbsession.query(Role).all()
        assert len(roles) == 0, "removed a role"
        assert dbsession.query(user_role).count() == 0

    def test_delete_cascade_to_tsearch(self, dbsession):
        from c2cgeoportal_commons.models.main import FullTextSearch, Role
        from sqlalchemy import func

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
