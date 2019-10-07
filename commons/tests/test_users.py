# pylint: disable=no-self-use

import pytest


@pytest.fixture(scope='class')
@pytest.mark.usefixtures("dbsession")
def insert_users_test_data(dbsession):
    from c2cgeoportal_commons.models.static import User
    from c2cgeoportal_commons.models.main import Role
    user = User("babar")
    user.roles = [Role(name='Role1'), Role(name='Role2')]
    t = dbsession.begin_nested()
    dbsession.add(user)
    dbsession.flush()
    yield
    t.rollback()


@pytest.mark.usefixtures("insert_users_test_data", "transact")
class TestUser:

    def test_select(self, dbsession):
        from c2cgeoportal_commons.models.static import User
        users = dbsession.query(User).all()
        assert len(users) == 1, "querying for users"
        assert users[0].username == 'babar', "user from test data is babar"
        assert 2 == len(users[0].roles)

    def test_remove(self, dbsession):
        from c2cgeoportal_commons.models.static import User
        from c2cgeoportal_commons.models.static import user_role
        users = dbsession.query(User).all()
        dbsession.delete(users[0])
        users = dbsession.query(User).all()
        assert len(users) == 0, "removed a user"
        assert 0 == dbsession.query(user_role).\
            count()

    def test_add(self, dbsession):
        from c2cgeoportal_commons.models.static import User
        from c2cgeoportal_commons.models.main import Role
        from c2cgeoportal_commons.models.static import user_role
        user = User(username="momo")
        user.roles = [Role(name='Role3')]
        dbsession.begin_nested()
        dbsession.add(user)
        dbsession.commit()
        assert dbsession.query(User).count() == 2, "added a user"
        dbsession.expire(user)
        assert user.username == 'momo', "added user is momo"
        assert 1 == len(user.roles)
        assert user.roles[0].name == 'Role3'
        assert 1 == dbsession.query(user_role).\
            filter(user_role.c.user_id == user.id).\
            count()

    @staticmethod
    def test_edit(dbsession):
        from c2cgeoportal_commons.models.static import User
        from c2cgeoportal_commons.models.main import Role
        from c2cgeoportal_commons.models.static import user_role
        user = dbsession.query(User).first()
        assert 2 == len(user.roles)
        user.roles = [Role(name='Role4')]
        dbsession.flush()
        dbsession.expire(user)
        assert 1 == len(user.roles)
        assert user.roles[0].name == 'Role4'
        assert 1 == dbsession.query(user_role).\
            filter(user_role.c.user_id == user.id).\
            count()
