# pylint: disable=no-self-use

import pytest
import sqlalchemy.exc


@pytest.fixture(scope="class")
@pytest.mark.usefixtures("dbsession")
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
    def test_select(self, dbsession):
        from c2cgeoportal_commons.models.static import User

        users = dbsession.query(User).all()
        assert len(users) == 1, "querying for users"
        assert users[0].username == "babar", "user from test data is babar"
        assert len(users[0].roles) == 2

    def test_remove(self, dbsession):
        from c2cgeoportal_commons.models.static import User, user_role

        users = dbsession.query(User).all()
        dbsession.delete(users[0])
        users = dbsession.query(User).all()
        assert len(users) == 0, "removed a user"
        assert dbsession.query(user_role).count() == 0

    def test_add(self, dbsession):
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
