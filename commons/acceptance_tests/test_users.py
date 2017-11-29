import pytest


@pytest.fixture(scope='class')
@pytest.mark.usefixtures("dbsession")
def insert_users_test_data(dbsession):
    from c2cgeoportal_commons.models.static import User
    user = User("babar")
    t = dbsession.begin_nested()
    dbsession.add(user)
    yield
    t.rollback()


@pytest.mark.usefixtures("insert_users_test_data", "transact")
class TestUser:

    def test_select(self, dbsession):
        from c2cgeoportal_commons.models.static import User
        users = dbsession.query(User).all()
        assert len(users) == 1, "querying for users"
        assert users[0].username == 'babar', "user from test data is babar"

    def test_remove(self, dbsession):
        from c2cgeoportal_commons.models.static import User
        users = dbsession.query(User).all()
        dbsession.delete(users[0])
        users = dbsession.query(User).all()
        assert len(users) == 0, "removed a user"

    def test_add(self, dbsession):
        from c2cgeoportal_commons.models.static import User
        user = User("momo")
        dbsession.begin_nested()
        dbsession.add(user)
        dbsession.commit()
        users = dbsession.query(User).all()
        assert len(users) == 2, "added a user"
        assert users[0].username == 'babar', "user from test data is babar"
        assert users[1].username == 'momo', "added user is momo"

    def test_no_role(self, dbsession):
        from c2cgeoportal_commons.models.main import Role
        roles = dbsession.query(Role).all()
        assert len(roles) == 0, "querying for role"
