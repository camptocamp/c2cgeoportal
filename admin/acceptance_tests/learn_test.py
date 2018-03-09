# pylint: disable=no-self-use

import pytest
from pyramid.view import view_config

from c2cgeoportal_commons.models import DBSession


@pytest.fixture(scope='class')
@pytest.mark.usefixtures('dbsession')
def insert_users_test_data(dbsession):
    from c2cgeoportal_commons.models.static import User
    user = User('babar')
    dbsession.begin_nested()
    dbsession.add(user)
    dbsession.flush()
    yield
    dbsession.rollback()


@view_config(route_name='user_add', renderer='./learn_test.jinja2')
def view_committing_user(request):
    from c2cgeoportal_commons.models.static import User
    user = User("momo")
    session = DBSession()  # pylint: disable=not-callable
    session.add(user)
    return {}


@view_config(route_name='users_nb', renderer='./learn_test.jinja2')
def view_displaying_users_nb(request):
    from c2cgeoportal_commons.models.static import User
    users = DBSession.query(User).all()
    username = 'None'
    if len(users) > 0:
        username = users[0].username
    return {'size': len(users), 'first': username,
            'project': 'c2cgeoportal_admin'}


@pytest.mark.usefixtures('insert_users_test_data', 'transact')
class TestUser:

    @pytest.mark.usefixtures('test_app')
    def test_view_rendering_in_app(self, dbsession, test_app):
        res = test_app.get('/users_nb', status=200)
        expected = ("['users len is: 1', <br/>,"
                    " 'first is: babar', <br/>,"
                    " 'project is: c2cgeoportal_admin', <br/>]")
        assert expected == str(res.html.contents)

    @pytest.mark.usefixtures("test_app")
    def test_commit_in_app(self, dbsession, test_app):
        res = test_app.get('/user_add', status=200)
        res = test_app.get('/users_nb', status=200)
        expected = ("['users len is: 2', <br/>,"
                    " 'first is: babar', <br/>,"
                    " 'project is: c2cgeoportal_admin', <br/>]")
        assert expected == str(res.html.contents)

    @pytest.mark.usefixtures("test_app")
    def test_commit_in_app_rollbacked(self, dbsession, test_app):
        res = test_app.get('/users_nb', status=200)
        expected = ("['users len is: 1', <br/>,"
                    " 'first is: babar', <br/>,"
                    " 'project is: c2cgeoportal_admin', <br/>]")
        assert expected == str(res.html.contents)
