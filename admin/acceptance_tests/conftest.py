import pytest
from pyramid import testing
from pyramid.paster import bootstrap
from pyramid.view import view_config
from webtest import TestApp
from wsgiref.simple_server import make_server
import threading

from c2cgeoportal_commons.tests import (  # noqa: F401
    dbsession,
    transact,
    raise_db_error_on_query,
)


@pytest.fixture(scope="session")
def app_env():
    with bootstrap('tests.ini') as env:
        yield env


@pytest.fixture(scope="session")
@pytest.mark.usefixtures("app_env")
def settings(app_env):
    yield app_env.get('registry').settings


@pytest.fixture()  # noqa: F811
@pytest.mark.usefixtures("dbsession", "app_env")
def test_app(request, dbsession, settings, app_env):
    config = testing.setUp(registry=app_env['registry'])
    config.add_request_method(lambda request: dbsession, 'dbsession', reify=True)
    config.add_route('user_add', 'user_add')
    config.add_route('users_nb', 'users_nb')
    config.scan(package='acceptance_tests')
    app = config.make_wsgi_app()
    testapp = TestApp(app)
    yield testapp


@pytest.fixture(scope='session')  # noqa: F811
@pytest.mark.usefixtures("dbsession", "app_env")
def selenium_app(request, dbsession, settings, app_env):
    app = app_env.get('app')
    srv = make_server('', 6543, app)
    threading.Thread(target=srv.serve_forever).start()
    yield()
    srv.shutdown()


@view_config(route_name='user_add', renderer='./learn_test.jinja2')
def view_committing_user(request):
    from c2cgeoportal_commons.models.main import User
    user = User("momo")
    t = request.dbsession.begin_nested()
    request.dbsession.add(user)
    t.commit()
    return {}


@view_config(route_name='users_nb', renderer='./learn_test.jinja2')
def view_displaying_users_nb(request):
    from c2cgeoportal_commons.models.main import User
    users = request.dbsession.query(User).all()
    username = 'None'
    if len(users) > 0:
        username = users[0].username
    return {'size': len(users), 'first': username, 'project': 'c2cgeoportal_admin'}
