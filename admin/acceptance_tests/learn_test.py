import pytest
from pyramid.testing import DummyRequest

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

    @pytest.mark.usefixtures("app")
    def test_view_rendering_in_app(self, dbsession, app):
        res = app.get('/users_nb', status=200)
        assert "['users len is: 1', <br/>, 'first is: babar', <br/>, 'projetc is: c2cgeoportal_admin', <br/>]" == str(res.html.contents), 'what a beautifull soup !'

    @pytest.mark.usefixtures("app")
    def test_commit_in_app(self, dbsession, app):
        res = app.get('/user_add', status=200)
        res = app.get('/users_nb', status=200)
        assert "['users len is: 2', <br/>, 'first is: babar', <br/>, 'projetc is: c2cgeoportal_admin', <br/>]" == str(res.html.contents), 'what a beautifull soup !'

    @pytest.mark.usefixtures("app")
    def test_commit_in_app_rollbacked(self, dbsession, app):
        res = app.get('/users_nb', status=200)
        assert "['users len is: 1', <br/>, 'first is: babar', <br/>, 'projetc is: c2cgeoportal_admin', <br/>]" == str(res.html.contents), 'what a beautifull soup !'
