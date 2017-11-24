import pytest
import transaction
from pyramid import testing

from pyramid.paster import bootstrap
from pyramid.view import view_config
from webtest import TestApp
from wsgiref.simple_server import make_server
import threading

from c2cgeoportal_commons.scripts.initializedb import init_db
from c2cgeoportal_commons.models import get_engine, get_session_factory, get_tm_session, generate_mappers
from sqlalchemy.exc import DBAPIError


@pytest.fixture(scope='session')
@pytest.mark.usefixtures("settings")
def dbsession(settings):
    generate_mappers(settings)
    engine = get_engine(settings)
    init_db(engine, force=True)
    session_factory = get_session_factory(engine)
    session = get_tm_session(session_factory, transaction.manager)
    return session


@pytest.fixture(scope='function')
@pytest.mark.usefixtures("dbsession")
def transact(dbsession):
    t = dbsession.begin_nested()
    yield
    t.rollback()


def raise_db_error(Table):
    raise DBAPIError('this is a test !', None, None)


@pytest.fixture(scope='function')
@pytest.mark.usefixtures("dbsession")
def raise_db_error_on_query(dbsession):
    query = dbsession.query
    dbsession.query = raise_db_error
    yield
    dbsession.query = query


@pytest.fixture(scope="session")
def app_env():
    with bootstrap('tests.ini') as env:
        yield env


@pytest.fixture(scope="session")
@pytest.mark.usefixtures("app_env", "dbsession")
def app(app_env, dbsession):
    config = testing.setUp(registry=app_env['registry'])
    config.add_request_method(lambda request: dbsession, 'dbsession', reify=True)
    config.add_route('user_add', 'user_add')
    config.add_route('users_nb', 'users_nb')
    config.scan(package='acceptance_tests')
    app = config.make_wsgi_app()
    yield app


@pytest.fixture(scope="session")
@pytest.mark.usefixtures("app_env")
def settings(app_env):
    yield app_env.get('registry').settings


@pytest.fixture(scope='session')  # noqa: F811
@pytest.mark.usefixtures("app")
def test_app(request, app):
    testapp = TestApp(app)
    yield testapp


@pytest.fixture(scope='session')  # noqa: F811
@pytest.mark.usefixtures("app")
def selenium_app(app):
    srv = make_server('', 6544, app)
    threading.Thread(target=srv.serve_forever).start()
    yield('http://localhost:6544')
    srv.shutdown()


@view_config(route_name='user_add', renderer='./learn_test.jinja2')
def view_committing_user(request):
    from c2cgeoportal_commons.models.static import User
    user = User("momo")
    t = request.dbsession.begin_nested()
    request.dbsession.add(user)
    t.commit()
    return {}


@view_config(route_name='users_nb', renderer='./learn_test.jinja2')
def view_displaying_users_nb(request):
    from c2cgeoportal_commons.models.static import User
    users = request.dbsession.query(User).all()
    username = 'None'
    if len(users) > 0:
        username = users[0].username
    return {'size': len(users), 'first': username,
            'project': 'c2cgeoportal_admin'}
