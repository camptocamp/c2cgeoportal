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

    def test_view(self, dbsession):
        from c2cgeoportal_admin.views.users import user_view
        info = user_view(DummyRequest(dbsession=dbsession))
        assert info['first'] == 'babar', 'view contain one user'
        assert info['size'] == 1
        assert info['project'] == 'c2cgeoportal_admin', 'view associated project is c2cgeoportal_admin'

    @pytest.mark.usefixtures("raise_db_error_on_query")
    def test_failing_view(self, dbsession):
        from c2cgeoportal_admin.views.users import user_view
        info = user_view(DummyRequest(dbsession=dbsession))
        assert info.status_int == 500, '500 status when db error'

    @pytest.mark.usefixtures("app")
    def test_view_rendering_in_app(self, dbsession, app):
        res = app.get('/users_nb', status=200)
        assert "['users len is: 1', <br/>, 'first is: babar', <br/>, 'projetc is: c2cgeoportal_admin', <br/>]" == str(res.html.contents), 'what a beautifull soup !'

    @pytest.mark.usefixtures("app")
    def test_commit_in_app(self, dbsession, app):
        res = app.get('/test', status=200)
        res = app.get('/users_nb', status=200)
        assert "['users len is: 2', <br/>, 'first is: babar', <br/>, 'projetc is: c2cgeoportal_admin', <br/>]" == str(res.html.contents), 'what a beautifull soup !'

    @pytest.mark.usefixtures("app")
    def test_commit_in_app_rollbacked(self, dbsession, app):
        res = app.get('/users_nb', status=200)
        assert "['users len is: 1', <br/>, 'first is: babar', <br/>, 'projetc is: c2cgeoportal_admin', <br/>]" == str(res.html.contents), 'what a beautifull soup !'
