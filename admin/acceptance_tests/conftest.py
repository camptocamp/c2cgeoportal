

import pytest
from pyramid import testing
from c2cgeoportal_commons.tests import dbsession, transact, raise_db_error_on_query
from wsgiref.simple_server import make_server
import threading

@pytest.fixture(scope='session')
def settings(request):
    return {
        'sqlalchemy.url': 'postgresql://www-data:www-data@localhost:5432/c2cgeoportal',
        'schema': 'main',
        'parent_schema': '',
        'srid': 3857,
        'pyramid.available_languages' : 'fr en'
    }

def prepare_app(dbsession, settings):
    config = testing.setUp(settings=settings)
    config.include('pyramid_jinja2')
    config.include('c2cgeoform')
    config.add_route('user_add', 'user_add')
    config.add_route('users_nb', 'users_nb')
    config.include('c2cgeoportal_admin.routes')
    config.include('c2cgeoportal_commons.models')
    config.scan(package='c2cgeoportal_admin.views')
    config.scan(package='acceptance_tests')
    config.add_request_method(lambda r:dbsession, 'dbsession', reify=True)
    app = config.make_wsgi_app()
    return app

@pytest.fixture(scope='session')
@pytest.mark.usefixtures("dbsession")
def test_app(request, dbsession, settings):
    app = prepare_app(dbsession, settings)
    from webtest import TestApp
    testapp = TestApp(app)
    return testapp;

HOST_BASE = "http://localhost:6543"

@pytest.fixture(scope='session')
@pytest.mark.usefixtures("dbsession")
def selenium_app(request, dbsession, settings):
    app = prepare_app(dbsession, settings)
    srv = make_server('', 6543, app)
    threading.Thread(target=srv.serve_forever).start()
    yield()
    srv.shutdown()

from pyramid.view import view_config

@view_config(route_name='user_add', renderer='./learn_test.jinja2')
def view_commiting_user(request):
    from c2cgeoportal_commons.models.main import User
    user = User("momo")
    t = request.dbsession.begin_nested()
    request.dbsession.add(user)
    t.commit()
    return {}

@view_config(route_name='users_nb', renderer='./learn_test.jinja2')
def view_displaying_users_nb(request):
    from c2cgeoportal_commons.models.main import User
    users = request.dbsession.query(User).all();
    username = 'None'
    if len(users) > 0:
        username = users[0].username
    return {'size': len(users), 'first': username, 'project': 'c2cgeoportal_admin'}
