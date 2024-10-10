# Copyright (c) 2021-2024, Camptocamp SA
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

# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.

import logging
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import pyramid.request
import pytest
import sqlalchemy.orm
import transaction
from c2c.template.config import config as configuration
from pyramid.testing import DummyRequest
from sqlalchemy.orm.session import Session, SessionTransaction
from tests.functional import setup_common as setup_module

from c2cgeoportal_commons.testing import generate_mappers, get_engine, get_session_factory, get_tm_session
from c2cgeoportal_commons.testing.initializedb import truncate_tables
from c2cgeoportal_geoportal.lib import caching

_LOG = logging.getLogger(__name__)
mapserv_url = "http://mapserver:8080/"

if TYPE_CHECKING:
    from c2cgeoportal_commons.models import main, static


@pytest.fixture
def settings():
    setup_module()
    yield {**configuration.get_config()}


@pytest.fixture
def dbsession_old(settings: dict[str, Any]) -> Session:
    from c2cgeoportal_commons.models import DBSession

    truncate_tables(DBSession)
    with patch("c2cgeoportal_geoportal.views.vector_tiles.DBSession", new=DBSession):
        yield DBSession
    truncate_tables(DBSession)


@pytest.fixture
def dbsession(settings: dict[str, Any]) -> Session:
    generate_mappers()
    engine = get_engine(settings)
    session_factory = get_session_factory(engine)
    session = get_tm_session(session_factory, transaction.manager)
    truncate_tables(session)
    with patch("c2cgeoportal_commons.models.DBSession", new=session):
        yield session
    truncate_tables(session)


@pytest.fixture
def transact_old(dbsession_old) -> SessionTransaction:
    t = dbsession_old.begin_nested()
    yield t
    try:
        t.rollback()
    except sqlalchemy.exc.ResourceClosedError:  # pragma: no cover
        _LOG.warning("Transaction already closed")
    dbsession_old.expire_all()


@pytest.fixture
def transact(dbsession) -> SessionTransaction:
    t = dbsession.begin_nested()
    yield t
    try:
        t.rollback()
    except sqlalchemy.exc.ResourceClosedError:  # pragma: no cover
        _LOG.warning("Transaction already closed")
    dbsession.expire_all()


@pytest.fixture
def dummy_request(dbsession_old) -> pyramid.request.Request:
    """
    A lightweight dummy request.

    This request is ultra-lightweight and should be used only when the request
    itself is not a large focus in the call-stack.  It is much easier to mock
    and control side-effects using this object, however:

    - It does not have request extensions applied.
    - Threadlocals are not properly pushed.

    """
    request = DummyRequest()
    request.host = "example.com"
    request.dbsession = dbsession_old

    return request


@pytest.fixture
def default_ogcserver(dbsession_old, transact_old) -> "main.OGCServer":
    from c2cgeoportal_commons.models.main import OGCServer

    del transact_old

    dbsession_old.flush()
    ogcserver = dbsession_old.query(OGCServer).filter(OGCServer.name == "__test_ogc_server").one_or_none()
    if ogcserver is None:
        ogcserver = OGCServer(name="__test_ogc_server")
    ogcserver.url = mapserv_url
    dbsession_old.add(ogcserver)
    dbsession_old.flush()

    yield ogcserver


@pytest.fixture
def some_user(dbsession_old, transact_old) -> "static.User":
    from c2cgeoportal_commons.models.static import User

    del transact_old

    user = User(username="__test_user", password="__test_user")
    dbsession_old.add(user)
    dbsession_old.flush()

    yield user


@pytest.fixture
def admin_user(dbsession_old, transact_old) -> "static.User":
    from c2cgeoportal_commons.models.main import Role
    from c2cgeoportal_commons.models.static import User

    del transact_old

    role = Role(name="role_admin")
    user = User(username="__test_user", password="__test_user", settings_role=role, roles=[role])
    dbsession_old.add_all([role, user])
    dbsession_old.flush()

    yield user


@pytest.fixture()
@pytest.mark.usefixtures("dbsession")
def default_ogcserver(dbsession: Session) -> "main.OGCServer":
    from c2cgeoportal_commons.models.main import OGCServer

    dbsession.flush()
    ogcserver = dbsession.query(OGCServer).filter(OGCServer.name == "__test_ogc_server").one_or_none()
    if ogcserver is None:
        ogcserver = OGCServer(name="__test_ogc_server")
    ogcserver.url = mapserv_url
    dbsession.add(ogcserver)
    caching.invalidate_region()

    return ogcserver
