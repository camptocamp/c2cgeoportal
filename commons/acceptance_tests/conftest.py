# -*- coding: utf-8 -*-

import os
import pytest
from logging.config import fileConfig

import plaster
from sqlalchemy.exc import DBAPIError
import transaction

from c2cgeoportal_commons.testing.initializedb import init_db, truncate_tables
from c2cgeoportal_commons.testing import get_engine, get_session_factory, get_tm_session, generate_mappers
from c2cgeoportal_commons.config import config


@pytest.fixture(scope='session')
@pytest.mark.usefixtures('settings')
def dbsession(settings):
    generate_mappers()
    engine = get_engine(settings)
    init_db(engine, settings['alembic_ini'], force=True)
    truncate_tables(engine)
    session_factory = get_session_factory(engine)
    session = get_tm_session(session_factory, transaction.manager)
    return session


@pytest.fixture(scope='function')
@pytest.mark.usefixtures('dbsession')
def transact(dbsession):
    t = dbsession.begin_nested()
    yield
    t.rollback()


@pytest.fixture(scope='session')
def settings():
    config_uri = 'tests.ini' if os.path.exists('tests.ini') else 'commons/tests.ini'
    fileConfig(config_uri, defaults=dict(os.environ))
    settings = plaster.get_settings(config_uri, 'tests')
    config.init(settings.get('app.cfg'))
    settings.update(config.get_config())
    return settings


def raise_db_error(_):
    raise DBAPIError('this is a test !', None, None)


@pytest.fixture(scope='function')
@pytest.mark.usefixtures("dbsession")
def raise_db_error_on_query(dbsession):
    query = dbsession.query
    dbsession.query = raise_db_error
    yield
    dbsession.query = query
