# -*- coding: utf-8 -*-

import os
from unittest.mock import Mock, patch

from c2c.template.config import config
import pytest
from qgis.server import QgsServerInterface
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from c2cgeoportal_commons.testing import generate_mappers


@pytest.fixture(scope="session")
def settings():
    settings = {}
    config.init(os.environ.get("GEOMAPFISH_CONFIG", "/etc/qgisserver/geomapfish.yaml"))
    settings.update(config.get_config())
    return settings


@pytest.fixture(scope="module")
@pytest.mark.usefixtures("settings")
def DBSession(settings):  # noqa: N802
    generate_mappers()
    engine = create_engine(config["sqlalchemy_slave.url"], pool_timeout=10)
    session_factory = sessionmaker()
    session_factory.configure(bind=engine)
    DBSession = scoped_session(session_factory)  # noqa: N806

    def fake_create_scoped_session():
        return DBSession

    with patch(
        "geomapfish_qgisserver.accesscontrol.create_scoped_session", return_value=fake_create_scoped_session
    ):
        yield DBSession


@pytest.fixture(scope="function")
def server_iface():
    yield Mock(spec=QgsServerInterface)


@pytest.fixture(scope="module")
def qgs_access_control_filter():
    """
    Mock some QgsAccessControlFilter methods:
    - __init__ which does not accept a mocked QgsServerInterface;
    - serverInterface to return the right server_iface.
    """

    class DummyQgsAccessControlFilter:
        def __init__(self, server_iface):
            self.server_iface = server_iface

        def serverInterface(self):  # noqa
            return self.server_iface

    with patch.multiple(
        "geomapfish_qgisserver.accesscontrol.QgsAccessControlFilter",
        __init__=DummyQgsAccessControlFilter.__init__,
        serverInterface=DummyQgsAccessControlFilter.serverInterface,
    ) as mocks:
        yield mocks


@pytest.fixture(scope="class")
def single_ogc_server_env():
    os.environ["GEOMAPFISH_OGCSERVER"] = "qgisserver1"
    yield
    del os.environ["GEOMAPFISH_OGCSERVER"]


@pytest.fixture(scope="class")
def multiple_ogc_server_env():
    os.environ["GEOMAPFISH_ACCESSCONTROL_CONFIG"] = "/etc/qgisserver/multiple_ogc_server.yaml"
    yield
    del os.environ["GEOMAPFISH_ACCESSCONTROL_CONFIG"]
