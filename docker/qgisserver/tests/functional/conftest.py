import os
from unittest.mock import Mock, patch

import pytest
from c2c.template.config import config
from c2cgeoportal_commons.testing import generate_mappers
from qgis.server import QgsServerInterface
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="session")
def settings():
    settings = {}
    config.init(os.environ.get("GEOMAPFISH_CONFIG", "/etc/qgisserver/geomapfish.yaml"))
    settings.update(config.get_config())
    return settings


@pytest.fixture(scope="module")
def DBSession(settings):  # noqa: ignore=N802
    generate_mappers()
    engine = create_engine(config["sqlalchemy_slave.url"], pool_timeout=10)
    session_factory = sessionmaker()
    session_factory.configure(bind=engine)

    with patch("geomapfish_qgisserver.accesscontrol.create_session_factory", return_value=session_factory):
        yield session_factory


@pytest.fixture(scope="module")
def clean_dbsession(DBSession):  # noqa: ignore=N803
    from c2cgeoportal_commons.models.main import (
        OGCServer,
        RestrictionArea,
        Role,
        TreeItem,
        layer_ra,
        role_ra,
    )
    from c2cgeoportal_commons.models.static import User, user_role

    def clean():
        dbsession = DBSession()
        dbsession.execute(layer_ra.delete())
        dbsession.query(TreeItem).delete()
        dbsession.query(OGCServer).delete()
        dbsession.execute(role_ra.delete())
        dbsession.query(RestrictionArea).delete()
        dbsession.execute(user_role.delete())
        dbsession.query(User).delete()
        dbsession.query(Role).delete()
        dbsession.commit()
        dbsession.close()

    clean()
    yield DBSession
    clean()


@pytest.fixture
def server_iface():
    result = Mock(spec=QgsServerInterface)
    return result


@pytest.fixture(scope="module")
def qgs_access_control_filter():
    """
    Mock some QgsAccessControlFilter methods:

    - __init__ which does not accept a mocked QgsServerInterface;
    - serverInterface to return the right server_iface.
    """

    class DummyQgsAccessControlFilter:
        def __init__(self, server_iface) -> None:
            self.server_iface = server_iface

        def serverInterface(self):  # noqa: ignore=N806
            return self.server_iface

    with patch.multiple(
        "geomapfish_qgisserver.accesscontrol.QgsAccessControlFilter",
        __init__=DummyQgsAccessControlFilter.__init__,
        serverInterface=DummyQgsAccessControlFilter.serverInterface,
    ) as mocks:
        yield mocks


@pytest.fixture(scope="class")
def single_ogc_server_env():
    with patch.dict(
        "os.environ",
        {
            "GEOMAPFISH_OGCSERVER": "qgisserver1",
        },
    ):
        yield


@pytest.fixture(scope="class")
def multiple_ogc_server_env():
    with patch.dict(
        "os.environ",
        {
            "GEOMAPFISH_ACCESSCONTROL_CONFIG": "/etc/qgisserver/multiple_ogc_server.yaml",
        },
    ):
        yield


@pytest.fixture(scope="class")
def auto_multi_ogc_server_env():
    with patch.dict(
        "os.environ",
        {
            "GEOMAPFISH_ACCESSCONTROL_BASE_URL": "http://qgis",
            "QGIS_PROJECT_FILE": "",
        },
    ):
        yield


@pytest.fixture(scope="class")
def auto_single_ogc_server_env():
    with patch.dict(
        "os.environ",
        {
            "GEOMAPFISH_ACCESSCONTROL_BASE_URL": "http://qgis",
            "QGIS_PROJECT_FILE": "qgisserver2",
        },
    ):
        yield
