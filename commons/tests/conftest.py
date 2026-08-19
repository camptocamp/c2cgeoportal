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


import os
from logging.config import fileConfig
from typing import NoReturn

import plaster
import pytest
import transaction
from c2c.template.config import config
from sqlalchemy.exc import DBAPIError

from c2cgeoportal_commons.testing import (
    generate_mappers,
    get_engine,
    get_session_factory,
    get_tm_session,
)
from c2cgeoportal_commons.testing.initializedb import truncate_tables


@pytest.fixture(scope="session")
def dbsession(settings):
    generate_mappers()
    engine = get_engine(settings)
    session_factory = get_session_factory(engine)
    session = get_tm_session(session_factory, transaction.manager)
    truncate_tables(session)
    return session


@pytest.fixture
def transact(dbsession):
    t = dbsession.begin_nested()
    yield
    t.rollback()


@pytest.fixture(scope="session")
def settings():
    config_uri = "/opt/c2cgeoportal/commons/tests/tests.ini"
    fileConfig(config_uri, defaults=dict(os.environ))
    settings = plaster.get_settings(config_uri, "tests")
    config.init(settings.get("app.cfg"))
    settings.update(config.get_config())
    return settings


def raise_db_error(_) -> NoReturn:
    raise DBAPIError("this is a test !", None, None)


@pytest.fixture
def raise_db_error_on_query(dbsession):
    query = dbsession.query
    dbsession.query = raise_db_error
    yield
    dbsession.query = query
