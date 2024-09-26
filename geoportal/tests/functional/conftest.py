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

from unittest.mock import patch

import pytest
import sqlalchemy.orm
import transaction
from c2c.template.config import config as configuration
from pyramid.testing import DummyRequest
from tests.functional import setup_common as setup_module

from c2cgeoportal_geoportal.lib import caching

mapserv_url = "http://mapserver:8080/"


@pytest.fixture
def settings():
    setup_module()
    yield {**configuration.get_config()}


@pytest.fixture
def dbsession(settings):
    from c2cgeoportal_commons.models import DBSession

    with patch("c2cgeoportal_geoportal.views.vector_tiles.DBSession", new=DBSession):
        yield DBSession


@pytest.fixture
def transact(dbsession):
    t = dbsession.begin_nested()
    yield t
    t.rollback()
    dbsession.expire_all()


@pytest.fixture
def dummy_request(dbsession):
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
    request.dbsession = dbsession

    return request


@pytest.fixture
def default_ogcserver(dbsession, transact):
    from c2cgeoportal_commons.models.main import OGCServer

    del transact

    ogcserver = OGCServer(name="__test_ogc_server")
    ogcserver.url = mapserv_url
    dbsession.add(ogcserver)
    dbsession.flush()

    yield ogcserver


@pytest.fixture
def some_user(dbsession, transact):
    from c2cgeoportal_commons.models.static import User

    del transact

    user = User(username="__test_user", password="__test_user")
    dbsession.add(user)
    dbsession.flush()

    yield user


@pytest.fixture
def admin_user(dbsession, transact):
    from c2cgeoportal_commons.models.main import Role
    from c2cgeoportal_commons.models.static import User

    del transact

    role = Role(name="role_admin")
    user = User(username="__test_user", password="__test_user", settings_role=role, roles=[role])
    dbsession.add_all([role, user])
    dbsession.flush()

    yield user
