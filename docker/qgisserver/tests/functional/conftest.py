# -*- coding: utf-8 -*-

import os
from c2c.template.config import config
import pytest
from unittest.mock import Mock, patch

import transaction
from qgis.server import QgsServerInterface

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


@pytest.fixture(scope='module')
def scoped_session(dbsession):
    with patch('geomapfish_qgisserver.accesscontrol.scoped_session',
               return_value=dbsession) as mock:
        yield mock


@pytest.fixture(scope='function')
def server_iface():
    yield Mock(spec=QgsServerInterface)


@pytest.fixture(scope='module')
def qgs_access_control_filter():
    """
    Mock some QgsAccessControlFilter methods:
    - __init__ which does not accept a mocked QgsServerInterface;
    - serverInterface to return the right server_iface.
    """
    class DummyQgsAccessControlFilter():

        def __init__(self, server_iface):
            self.server_iface = server_iface

        def serverInterface(self):
            return self.server_iface

    with patch.multiple('geomapfish_qgisserver.accesscontrol.QgsAccessControlFilter',
                        __init__=DummyQgsAccessControlFilter.__init__,
                        serverInterface=DummyQgsAccessControlFilter.serverInterface) as mocks:
        yield mocks


@pytest.fixture(scope='class')
def single_ogc_server_env(dbsession):
    os.environ['GEOMAPFISH_OGCSERVER'] = 'qgisserver1'
    yield
    del os.environ['GEOMAPFISH_OGCSERVER']


@pytest.fixture(scope='class')
def multiple_ogc_server_env(dbsession):
    os.environ['GEOMAPFISH_ACCESSCONTROL_CONFIG'] = '/etc/qgisserver/multiple_ogc_server.yaml'
    yield
    del os.environ['GEOMAPFISH_ACCESSCONTROL_CONFIG']
