# -*- coding: utf-8 -*-

import os

from c2c.template.config import config
import pytest
import transaction

from c2cgeoportal_commons.testing import generate_mappers, get_engine, get_session_factory, get_tm_session
from c2cgeoportal_commons.testing.initializedb import truncate_tables


@pytest.fixture(scope="session")
@pytest.mark.usefixtures("settings")
def dbsession(settings):
    generate_mappers()
    engine = get_engine(settings, prefix="sqlalchemy_slave.")
    truncate_tables(engine)
    session_factory = get_session_factory(engine)
    session = get_tm_session(session_factory, transaction.manager)
    return session


@pytest.fixture(scope="session")
def settings():
    settings = {}
    config.init(os.environ.get("GEOMAPFISH_CONFIG", "/etc/qgisserver/geomapfish.yaml"))
    settings.update(config.get_config())
    return settings
