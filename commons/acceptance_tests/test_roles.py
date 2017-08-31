import pytest

@pytest.fixture(scope='class')
@pytest.mark.usefixtures("dbsession")
def insertRolesTestData(dbsession):
    from c2cgeoportal_commons.models.main import Role
    role = Role("secretary")
    transaction = dbsession.begin_nested()
    dbsession.add(role)

    yield

    transaction.rollback()

@pytest.mark.usefixtures("insertRolesTestData", "transact")
class TestRole():

    def test_no_user(self, dbsession):
        from c2cgeoportal_commons.models.main import User
        users = dbsession.query(User).all()
        assert len(users) == 0, "querying for users"

    def test_select(self, dbsession):
        from c2cgeoportal_commons.models.main import Role
        roles = dbsession.query(Role).all()
        assert len(roles) == 1, "querying for roles"
        assert roles[0].name == 'secretary', "role from test data is secretary"
