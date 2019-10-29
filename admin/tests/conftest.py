import threading
from wsgiref.simple_server import make_server

from pyramid import testing
from pyramid.paster import bootstrap
import pytest
from sqlalchemy.exc import DBAPIError
import transaction
from webtest import TestApp as WebTestApp  # Avoid warning with pytest

from c2cgeoportal_commons.testing import generate_mappers, get_engine, get_session_factory, get_tm_session
from c2cgeoportal_commons.testing.initializedb import truncate_tables


@pytest.fixture(scope="session")
@pytest.mark.usefixtures("settings")
def dbsession(settings):
    generate_mappers()
    engine = get_engine(settings)
    truncate_tables(engine)
    session_factory = get_session_factory(engine)
    session = get_tm_session(session_factory, transaction.manager)
    yield session


@pytest.fixture(scope="function")
@pytest.mark.usefixtures("dbsession")
def transact(dbsession):
    t = dbsession.begin_nested()
    yield t
    t.rollback()
    dbsession.expire_all()


def raise_db_error(_):
    raise DBAPIError("this is a test !", None, None)


@pytest.fixture(scope="function")
@pytest.mark.usefixtures("dbsession")
def raise_db_error_on_query(dbsession):
    query = dbsession.query
    dbsession.query = raise_db_error
    yield
    dbsession.query = query


@pytest.fixture(scope="session")
def app_env():
    file_name = "/opt/c2cgeoportal/admin/tests/tests.ini"
    with bootstrap(file_name) as env:
        yield env


@pytest.fixture(scope="session")
@pytest.mark.usefixtures("app_env", "dbsession")
def app(app_env, dbsession):
    config = testing.setUp(registry=app_env["registry"])
    config.add_request_method(lambda request: dbsession, "dbsession", reify=True)
    config.add_route("user_add", "user_add")
    config.add_route("users_nb", "users_nb")
    config.scan(package="tests")
    app = config.make_wsgi_app()
    yield app


@pytest.fixture(scope="session")
@pytest.mark.usefixtures("app_env")
def settings(app_env):
    yield app_env.get("registry").settings


@pytest.fixture(scope="session")  # noqa: F811
@pytest.mark.usefixtures("app")
def test_app(request, app):
    testapp = WebTestApp(app)
    yield testapp


@pytest.fixture(scope="session")  # noqa: F811
@pytest.mark.usefixtures("app")
def selenium_app(app):
    srv = make_server("", 6544, app)
    threading.Thread(target=srv.serve_forever).start()
    yield ("http://localhost:6544")
    srv.shutdown()
