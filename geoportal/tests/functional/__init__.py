# Copyright (c) 2013-2024, Camptocamp SA
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


"""
Pyramid application test package.
"""

import logging
from configparser import ConfigParser
from typing import TYPE_CHECKING, Any

import pyramid.registry
import pyramid.request
import tests
import transaction
import webob.acceptparse
from c2c.template.config import config as configuration
from pyramid import testing
from sqlalchemy.orm.session import Session

import c2cgeoportal_geoportal
import c2cgeoportal_geoportal.lib
from c2cgeoportal_commons import models
from c2cgeoportal_geoportal.lib import caching

if TYPE_CHECKING:
    from c2cgeoportal_commons.models import main, static

_LOG = logging.getLogger(__name__)
mapserv_url = "http://mapserver:8080/"
config = None


class DummyRoute:
    """Dummy route for matched_route in testing."""

    name: str = "dummy"
    pattern: str = "dummy"


def cleanup_db() -> None:
    """
    Cleanup the database.
    """
    from c2cgeoportal_commons import models
    from c2cgeoportal_commons.models.main import (
        FullTextSearch,
        Functionality,
        Interface,
        OGCServer,
        RestrictionArea,
        Role,
        TreeItem,
    )
    from c2cgeoportal_commons.models.static import OAuth2Client, Shorturl, User

    with models.DBSession() as session:
        for ra in session.query(RestrictionArea).all():
            ra.roles = []
            session.delete(ra)
        for ti in session.query(TreeItem).all():
            session.delete(ti)
        session.query(OGCServer).delete()
        session.query(Interface).delete()
        for r in session.query(Role).all():
            r.functionalities = []
            session.delete(r)
        session.query(User).delete()
        session.query(Functionality).delete()
        session.query(FullTextSearch).delete()
        session.query(Shorturl).delete()
        session.query(OAuth2Client).delete()
        try:
            transaction.commit()
        except Exception as e:
            _LOG.error(e)
            transaction.abort()


def setup_db() -> None:
    """
    Cleanup the database.
    """
    cleanup_db()

    from c2cgeoportal_commons.models import DBSession
    from c2cgeoportal_commons.models.main import Role

    with DBSession() as session:
        session.add_all([Role(name) for name in ("anonymous", "registered", "intranet")])

        transaction.commit()

    c2cgeoportal_geoportal.lib.ogc_server_wms_url_ids = None
    c2cgeoportal_geoportal.lib.ogc_server_wfs_url_ids = None

    caching.init_region({"backend": "dogpile.cache.null"}, "std")
    caching.init_region({"backend": "dogpile.cache.null"}, "obj")
    caching.init_region({"backend": "dogpile.cache.null"}, "ogc-server")
    caching.invalidate_region()


def get_settings() -> dict[str, Any]:
    logging.getLogger("c2cgeoportal_geoportal").setLevel(logging.DEBUG)

    configfile = "/opt/c2cgeoportal/geoportal/tests/tests.ini"
    cfg = ConfigParser()
    cfg.read(configfile)
    db_url = cfg.get("test", "sqlalchemy.url")

    assert db_url is not None
    configuration._config = {
        "sqlalchemy.url": db_url,
        "sqlalchemy_slave.url": db_url,
        "srid": 21781,
        "schema": "main",
        "schema_static": "main_static",
        "default_max_age": 86400,
        "app.cfg": "/opt/c2cgeoportal/geoportal/tests/config.yaml",
        "package": "c2cgeoportal",
        "enable_admin_interface": True,
        "getitfixed": {"enabled": False},
        "vector_tiles": {
            "srid": 21781,
            "extent": [599900, 199950, 600100, 200050],
            "resolutions": [4000, 2000, 1000, 500, 250, 100, 50, 20, 10, 5, 2.5, 1, 0.5, 0.25, 0.1, 0.05],
        },
    }

    return configuration.get_config()


def setup_common() -> None:
    global config

    config = testing.setUp(settings=get_settings())

    c2cgeoportal_geoportal.init_db_sessions(config.get_settings(), config)

    setup_db()


def teardown_common() -> None:
    cleanup_db()
    testing.tearDown()

    models.DBSession.close()
    models.DBSession = None
    models.DBSessions = {}


def create_default_ogcserver(session: Session) -> "main.OGCServer":
    from c2cgeoportal_commons.models.main import OGCServer

    session.flush()
    ogcserver = session.query(OGCServer).filter(OGCServer.name == "__test_ogc_server").one_or_none()
    if ogcserver is None:
        ogcserver = OGCServer(name="__test_ogc_server")
    ogcserver.url = mapserv_url
    session.add(ogcserver)
    caching.invalidate_region()

    return ogcserver


def _get_user(username: str) -> "static.User":
    from c2cgeoportal_commons.models import DBSession
    from c2cgeoportal_commons.models.static import User

    return DBSession.query(User).filter(User.username == username).one()


def init_registry(registry=None):
    from c2cgeoportal_geoportal import default_user_validator

    registry = registry if registry is not None else pyramid.registry.Registry()

    registry.validate_user = default_user_validator

    return registry


def testing_legacySecurityPolicy(
    config, userid=None, groupids=(), permissive=True, remember_result=None, forget_result=None
):
    """Compatibility mode for deprecated AuthorizationPolicy and AuthenticationPolicy in our tests"""
    from pyramid.interfaces import IAuthenticationPolicy, IAuthorizationPolicy, ISecurityPolicy
    from pyramid.security import LegacySecurityPolicy
    from pyramid.testing import DummySecurityPolicy

    policy = DummySecurityPolicy(userid, groupids, permissive, remember_result, forget_result)
    config.registry.registerUtility(policy, IAuthorizationPolicy)
    config.registry.registerUtility(policy, IAuthenticationPolicy)

    security_policy = LegacySecurityPolicy()
    config.registry.registerUtility(security_policy, ISecurityPolicy)
    return policy


def create_dummy_request(
    additional_settings=None, authentication=True, user=None, *args: Any, **kargs: Any
) -> pyramid.request.Request:
    from pyramid.interfaces import IAuthenticationPolicy

    from c2cgeoportal_geoportal import create_get_user_from_request
    from c2cgeoportal_geoportal.lib.authentication import create_authentication

    if additional_settings is None:
        additional_settings = {}

    pyramid.testing.tearDown()

    request = tests.create_dummy_request(
        {
            "functionalities": {"available_in_templates": []},
            "layers": {"geometry_validation": True},
            "admin_interface": {
                "available_functionalities": [{"name": "mapserver_substitution", "single": False}],
                "available_metadata": [{"name": "lastUpdateDateColumn"}, {"name": "lastUpdateUserColumn"}],
            },
        },
        *args,
        **kargs,
    )
    request.host = "example.com"
    request.referrer = "example.com"

    global config
    config = pyramid.testing.setUp(
        request=request,
        registry=request.registry,
        settings=get_settings(),
    )

    request.accept_language = webob.acceptparse.create_accept_language_header(
        "fr-CH,fr;q=0.8,en;q=0.5,en-US;q=0.3"
    )
    request.registry.settings.update(additional_settings)
    request.referrer = "http://example.com/app"
    request.path_info_peek = lambda: "main"
    request.interface_name = "main"
    request.get_user = _get_user
    request.c2c_request_id = "test"
    request.matched_route = DummyRoute()
    init_registry(request.registry)

    if authentication and user is None:
        authentication_settings = {
            "authtkt_cookie_name": "__test",
            "authtkt_secret": "long enough secret!!  00000000000000000000000000000000000000000000000",
            "authentication": {},
        }
        authentication_settings.update(additional_settings)

        testing_legacySecurityPolicy(config)
        config.registry.registerUtility(create_authentication(authentication_settings), IAuthenticationPolicy)

    elif user is not None:
        config.testing_securitypolicy(user)
    request.set_property(
        create_get_user_from_request({"authorized_referers": [request.referrer]}), name="user", reify=True
    )

    return request


def fill_tech_user_functionality(name, functionalities, session: Session) -> None:
    from c2cgeoportal_commons.models.main import Functionality, Role

    role = session.query(Role).filter_by(name=name).one()
    role.functionalities = [Functionality(name, value) for name, value in functionalities]
    session.add(role)
    caching.invalidate_region()
