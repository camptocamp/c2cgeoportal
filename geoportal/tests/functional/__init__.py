# -*- coding: utf-8 -*-

# Copyright (c) 2013-2019, Camptocamp SA
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
Pyramid application test package
"""

from configparser import ConfigParser

import tests
import transaction
import webob.acceptparse
from c2c.template.config import config as configuration
from pyramid import testing

import c2cgeoportal_geoportal
import c2cgeoportal_geoportal.lib
from c2cgeoportal_commons import models
from c2cgeoportal_geoportal.lib import caching

mapserv_url = "http://mapserver:8080/"
config = None


def cleanup_db():
    """ Cleanup the database """
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
    from c2cgeoportal_commons.models.static import Shorturl, User

    transaction.commit()
    for ra in models.DBSession.query(RestrictionArea).all():
        ra.roles = []
        models.DBSession.delete(ra)
    for ti in models.DBSession.query(TreeItem).all():
        models.DBSession.delete(ti)
    models.DBSession.query(OGCServer).delete()
    models.DBSession.query(Interface).delete()
    for r in models.DBSession.query(Role).all():
        r.functionalities = []
        models.DBSession.delete(r)
    models.DBSession.query(User).delete()
    models.DBSession.query(Functionality).delete()
    models.DBSession.query(FullTextSearch).delete()
    models.DBSession.query(Shorturl).delete()
    transaction.commit()


def setup_db():
    """ Cleanup the database """
    cleanup_db()

    from c2cgeoportal_commons.models import DBSession
    from c2cgeoportal_commons.models.main import Role

    DBSession.add_all([Role(name) for name in ("anonymous", "registered", "intranet")])

    transaction.commit()

    c2cgeoportal_geoportal.lib.ogc_server_wms_url_ids = None
    c2cgeoportal_geoportal.lib.ogc_server_wfs_url_ids = None

    caching.init_region({"backend": "dogpile.cache.null"}, "std")
    caching.init_region({"backend": "dogpile.cache.null"}, "obj")
    caching.invalidate_region()


def setup_common():
    global config

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
    }
    config = testing.setUp(settings=configuration.get_config())

    c2cgeoportal_geoportal.init_dbsessions(config.get_settings(), config)

    setup_db()


def teardown_common():
    cleanup_db()
    testing.tearDown()

    models.DBSession.close()
    models.DBSession = None
    models.DBSessions = {}


def create_default_ogcserver():
    from c2cgeoportal_commons.models import DBSession
    from c2cgeoportal_commons.models.main import OGCServer

    transaction.commit()
    ogcserver = OGCServer(name="__test_ogc_server")
    ogcserver.url = mapserv_url
    DBSession.add(ogcserver)
    transaction.commit()
    caching.invalidate_region()

    return ogcserver


def _get_user(username):
    from c2cgeoportal_commons.models import DBSession
    from c2cgeoportal_commons.models.static import User

    return DBSession.query(User).filter(User.username == username).one()


def create_dummy_request(additional_settings=None, authentication=True, user=None, *args, **kargs):
    if additional_settings is None:
        additional_settings = {}
    from c2cgeoportal_geoportal import create_get_user_from_request, default_user_validator
    from c2cgeoportal_geoportal.lib.authentication import create_authentication

    request = tests.create_dummy_request(
        {
            "host_forward_host": [],
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
    request.accept_language = webob.acceptparse.create_accept_language_header(
        "fr-CH,fr;q=0.8,en;q=0.5,en-US;q=0.3"
    )
    request.registry.settings.update(additional_settings)
    request.referer = "http://example.com/app"
    request.path_info_peek = lambda: "main"
    request.interface_name = "main"
    request.get_user = _get_user
    request.registry.validate_user = default_user_validator
    request.c2c_request_id = "test"
    if authentication and user is None:
        authentication_settings = {
            "authtkt_cookie_name": "__test",
            "authtkt_secret": "long enough secret!!  00000000000000000000000000000000000000000000000",
        }
        authentication_settings.update(additional_settings)
        request._get_authentication_policy = lambda: create_authentication(authentication_settings)
    elif user is not None:
        config.testing_securitypolicy(user)
    request.set_property(
        create_get_user_from_request({"authorized_referers": [request.referer]}), name="user", reify=True
    )
    return request


def fill_tech_user_functionality(name, functionalities):
    from c2cgeoportal_commons.models import DBSession
    from c2cgeoportal_commons.models.main import Functionality, Role

    role = DBSession.query(Role).filter_by(name=name).one()
    role.functionalities = [Functionality(name, value) for name, value in functionalities]
    DBSession.add(role)
    transaction.commit()
    caching.invalidate_region()
