import os
import pytest
import transaction
from pyramid import testing

from pyramid.paster import bootstrap
from webtest import TestApp as WebTestApp  # Avoid warning with pytest
from wsgiref.simple_server import make_server
import threading

from c2cgeoportal_commons.testing.initializedb import init_db, truncate_tables
from c2cgeoportal_commons.testing import get_engine, get_session_factory, get_tm_session, generate_mappers
from sqlalchemy.exc import DBAPIError


@pytest.fixture(scope='session')
@pytest.mark.usefixtures("settings")
def dbsession(settings):
    generate_mappers()
    engine = get_engine(settings)
    init_db(engine, settings['alembic_ini'], force=True)
    truncate_tables(engine)
    session_factory = get_session_factory(engine)
    session = get_tm_session(session_factory, transaction.manager)
    yield session


@pytest.fixture(scope='function')
@pytest.mark.usefixtures("dbsession")
def transact(dbsession):
    t = dbsession.begin_nested()
    yield t
    t.rollback()
    dbsession.expire_all()


def raise_db_error(_):
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
    file_name = 'tests.ini' if os.path.exists('tests.ini') else 'admin/tests.ini'
    with bootstrap(file_name) as env:
        yield env


@pytest.fixture(scope="session")
@pytest.mark.usefixtures("app_env", "dbsession")
def app(app_env, dbsession):
    config = testing.setUp(registry=app_env['registry'])
    config.add_request_method(lambda request: dbsession, 'dbsession', reify=True)
    config.add_route('user_add', 'user_add')
    config.add_route('users_nb', 'users_nb')
    config.scan(package='tests')
    app = config.make_wsgi_app()
    yield app


@pytest.fixture(scope="session")
@pytest.mark.usefixtures("app_env")
def settings(app_env):
    yield app_env.get('registry').settings


@pytest.fixture(scope='session')  # noqa: F811
@pytest.mark.usefixtures("app")
def test_app(request, app):
    testapp = WebTestApp(app)
    yield testapp


@pytest.fixture(scope='session')  # noqa: F811
@pytest.mark.usefixtures("app")
def selenium_app(app):
    srv = make_server('', 6544, app)
    threading.Thread(target=srv.serve_forever).start()
    yield('http://localhost:6544')
    srv.shutdown()
