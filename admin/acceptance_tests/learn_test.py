# pylint: disable=no-self-use

import pytest


@pytest.fixture(scope='class')
@pytest.mark.usefixtures("dbsession")
def insert_users_test_data(dbsession):
    from c2cgeoportal_commons.models.static import User
    user = User("babar")
    dbsession.begin_nested()
    dbsession.add(user)
    yield
    dbsession.rollback()


@pytest.mark.usefixtures("insert_users_test_data", "transact")
class TestUser:

    @pytest.mark.usefixtures("test_app")
    def test_view_rendering_in_app(self, dbsession, test_app):
        res = test_app.get('/users_nb', status=200)
        expected = ("['users len is: 1', <br/>,"
                    " 'first is: babar', <br/>,"
                    " 'projetc is: c2cgeoportal_admin', <br/>]")
        assert expected == str(res.html.contents)

    @pytest.mark.usefixtures("test_app")
    def test_commit_in_app(self, dbsession, test_app):
        res = test_app.get('/user_add', status=200)
        res = test_app.get('/users_nb', status=200)
        expected = ("['users len is: 2', <br/>,"
                    " 'first is: babar', <br/>,"
                    " 'projetc is: c2cgeoportal_admin', <br/>]")
        assert expected == str(res.html.contents)

    @pytest.mark.usefixtures("test_app")
    def test_commit_in_app_rollbacked(self, dbsession, test_app):
        res = test_app.get('/users_nb', status=200)
        expected = ("['users len is: 1', <br/>,"
                    " 'first is: babar', <br/>,"
                    " 'projetc is: c2cgeoportal_admin', <br/>]")
        assert expected == str(res.html.contents)
