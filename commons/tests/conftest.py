import os
from logging.config import fileConfig

import plaster
import pytest
import transaction
from c2c.template.config import config
from sqlalchemy.exc import DBAPIError

from c2cgeoportal_commons.testing import generate_mappers, get_engine, get_session_factory, get_tm_session
from c2cgeoportal_commons.testing.initializedb import truncate_tables


@pytest.fixture(scope="session")
@pytest.mark.usefixtures("settings")
def dbsession(settings):
    generate_mappers()
    engine = get_engine(settings)
    session_factory = get_session_factory(engine)
    session = get_tm_session(session_factory, transaction.manager)
    truncate_tables(session)
    return session


@pytest.fixture(scope="function")
@pytest.mark.usefixtures("dbsession")
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


def raise_db_error(_):
    raise DBAPIError("this is a test !", None, None)


@pytest.fixture(scope="function")
@pytest.mark.usefixtures("dbsession")
def raise_db_error_on_query(dbsession):
    query = dbsession.query
    dbsession.query = raise_db_error
    yield
    dbsession.query = query
