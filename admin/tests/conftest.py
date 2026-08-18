# Copyright (c) 2025-2026, Camptocamp SA
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


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

from c2cgeoportal_commons.testing import (
    generate_mappers,
    get_engine,
    get_session_factory,
    get_tm_session,
)
from c2cgeoportal_commons.testing.initializedb import truncate_tables


@pytest.fixture(scope="session")
def dbsession(settings: dict[str, Any]) -> Session:
    generate_mappers()
    engine = get_engine(settings)
    session_factory = get_session_factory(engine)
    session = get_tm_session(session_factory, transaction.manager)
    truncate_tables(session)
    return session


@pytest.fixture
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


@pytest.fixture
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
def app(app_env: AppEnvironment, dbsession: Session) -> Router:
    config = testing.setUp(registry=app_env["registry"])
    config.add_request_method(lambda request: dbsession, "dbsession", reify=True)
    config.add_route("user_add", "user_add")
    config.add_route("users_nb", "users_nb")
    config.add_route("base", "/", static=True)
    config.scan(package="tests")
    app = config.make_wsgi_app()
    return app


@pytest.fixture(scope="session")
def settings(app_env: AppEnvironment) -> Any:
    return app_env.get("registry").settings


@pytest.fixture(scope="session")  # noqa: ignore=F811
def test_app(request: pyramid.request.Request, app: Router) -> WebTestApp:
    testapp = WebTestApp(app)
    return testapp
