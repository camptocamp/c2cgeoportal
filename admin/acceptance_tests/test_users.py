import pytest

from pyramid import testing

def dummy_request(dbsession):
    return testing.DummyRequest(dbsession=dbsession)

@pytest.fixture(scope='class')
@pytest.mark.usefixtures("dbsession")
def insertUsersTestData(dbsession):
    from c2cgeoportal_commons.models.main import User
    user = User("babar")
    dbsession.begin_nested()
    dbsession.add(user)
    yield
    dbsession.rollback()

@pytest.mark.usefixtures("insertUsersTestData", "transact")
class TestUser():

    def test_view(self, dbsession):
        from c2cgeoportal_admin.views.user import user_view
        info = user_view(dummy_request(dbsession))
        assert info['first'].username == 'babar', 'view contain one user'
        assert info['project'] == 'c2cgeoportal_admin', 'view associated project is c2cgeoportal_admin'
            
    @pytest.mark.usefixtures("raise_db_error_on_query")
    def test_failing_view(self, dbsession):
        from c2cgeoportal_admin.views.user import user_view
        info = user_view(dummy_request(dbsession))
        assert info.status_int == 500, '500 status when db error' 
