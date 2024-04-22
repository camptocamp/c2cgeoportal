from typing import Any

import pyramid.request
import pytest
import sqlalchemy.exc
import transaction
from pyramid import testing
from pyramid.paster import bootstrap
from pyramid.router import Router
from pyramid.scripting import AppEnvironment
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session, SessionTransaction
from webtest import TestApp as WebTestApp  # Avoid warning with pytest

from c2cgeoportal_commons.testing import generate_mappers, get_engine, get_session_factory, get_tm_session
from c2cgeoportal_commons.testing.initializedb import truncate_tables


@pytest.fixture(scope="session")
@pytest.mark.usefixtures("settings")
def dbsession(settings: dict[str, Any]) -> Session:
    generate_mappers()
    engine = get_engine(settings)
    session_factory = get_session_factory(engine)
    session = get_tm_session(session_factory, transaction.manager)
    truncate_tables(session)
    yield session


@pytest.fixture(scope="function")
@pytest.mark.usefixtures("dbsession")
def transact(dbsession: Session) -> SessionTransaction:
    t = dbsession.begin_nested()
    yield t
    try:
        t.rollback()
    except sqlalchemy.exc.ResourceClosedError:
        print("The transaction was already closed")
    dbsession.expire_all()


def raise_db_error(_: Any) -> None:
    raise DBAPIError("this is a test !", None, None)


@pytest.fixture(scope="function")
@pytest.mark.usefixtures("dbsession")
def raise_db_error_on_query(dbsession: Session) -> None:
    query = dbsession.query
    dbsession.query = raise_db_error
    yield
    dbsession.query = query


@pytest.fixture(scope="session")
def app_env() -> AppEnvironment:
    file_name = "/opt/c2cgeoportal/admin/tests/tests.ini"
    with bootstrap(file_name) as env:
        yield env


@pytest.fixture(scope="session")
@pytest.mark.usefixtures("app_env", "dbsession")
def app(app_env: AppEnvironment, dbsession: Session) -> Router:
    config = testing.setUp(registry=app_env["registry"])
    config.add_request_method(lambda request: dbsession, "dbsession", reify=True)
    config.add_route("user_add", "user_add")
    config.add_route("users_nb", "users_nb")
    config.add_route("base", "/", static=True)
    config.scan(package="tests")
    app = config.make_wsgi_app()
    yield app


@pytest.fixture(scope="session")
@pytest.mark.usefixtures("app_env")
def settings(app_env: AppEnvironment) -> Any:
    yield app_env.get("registry").settings


@pytest.fixture(scope="session")  # noqa: ignore=F811
@pytest.mark.usefixtures("app")
def test_app(request: pyramid.request.Request, app: Router) -> WebTestApp:
    testapp = WebTestApp(app)
    yield testapp
