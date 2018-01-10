# -*- coding: utf-8 -*-

# Copyright (c) 2013-2018, Camptocamp SA
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

import os
from ConfigParser import ConfigParser
from webob.acceptparse import Accept

from pyramid import testing
import c2cgeoportal
from c2cgeoportal import tests
from c2cgeoportal.lib import functionality, caching


mapserv_url = "http://mapserver/"
db_url = None

curdir = os.path.dirname(os.path.abspath(__file__))
configfile = os.path.realpath(os.path.join(curdir, "test.ini"))

if os.path.exists(configfile):
    cfg = ConfigParser()
    cfg.read(configfile)
    db_url = cfg.get("test", "sqlalchemy.url")

caching.init_region({"backend": "dogpile.cache.memory"})
config = None


def cleanup_db():
    """ Cleanup the database """
    import transaction
    from c2cgeoportal.models import DBSession, OGCServer, TreeItem, Role, User, RestrictionArea, \
        Interface, Functionality, FullTextSearch, Shorturl

    transaction.commit()
    for ra in DBSession.query(RestrictionArea).all():
        ra.roles = []
        DBSession.delete(ra)
    for ti in DBSession.query(TreeItem).all():
        DBSession.delete(ti)
    DBSession.query(OGCServer).delete()
    DBSession.query(Interface).delete()
    for r in DBSession.query(Role).all():
        r.functionnalities = []
        DBSession.delete(r)
    DBSession.query(User).delete()
    DBSession.query(Functionality).delete()
    DBSession.query(FullTextSearch).delete()
    DBSession.query(Shorturl).delete()
    transaction.commit()

    caching.invalidate_region()


def set_up_common():
    global config
    config = testing.setUp()

    c2cgeoportal.schema = "main"
    c2cgeoportal.srid = 21781
    functionality.FUNCTIONALITIES_TYPES = None

    # verify that we have a working database connection before going forward
    from sqlalchemy import create_engine
    engine = create_engine(db_url)
    engine.connect()

    import sqlahelper
    sqlahelper.add_engine(engine)

    cleanup_db()


def tear_down_common():
    cleanup_db()
    testing.tearDown()
    functionality.FUNCTIONALITIES_TYPES = None

    import sqlahelper
    sqlahelper.reset()


def create_default_ogcserver():
    import transaction
    from c2cgeoportal.models import DBSession, OGCServer

    transaction.commit()
    ogcserver = OGCServer(name="__test_ogc_server")
    ogcserver.url = mapserv_url
    ogcserver_external = OGCServer(name="__test_external_ogc_server")
    ogcserver_external.url = mapserv_url + "?external=true&"
    DBSession.add_all([ogcserver, ogcserver_external])
    transaction.commit()

    return ogcserver, ogcserver_external


def _get_user(username):
    from c2cgeoportal.models import DBSession, User

    return DBSession.query(User).filter(User.username == username).one()


def create_dummy_request(additional_settings=None, authentication=True, user=None, *args, **kargs):
    if additional_settings is None:
        additional_settings = {}
    from c2cgeoportal.pyramid_ import default_user_validator
    from c2cgeoportal.pyramid_ import create_get_user_from_request
    from c2cgeoportal.lib.authentication import create_authentication
    request = tests.create_dummy_request({
        "host_forward_host": [],
        "mapserverproxy": {
            "default_ogc_server": "__test_ogc_server",
            "external_ogc_server": "__test_external_ogc_server",
        },
        "functionalities": {
            "registered": {},
            "anonymous": {},
            "available_in_templates": []
        },
        "layers": {
            "geometry_validation": True
        }
    }, *args, **kargs)
    request.accept_language = Accept("fr-CH,fr;q=0.8,en;q=0.5,en-US;q=0.3")
    request.registry.settings.update(additional_settings)
    request.referer = "http://example.com/app"
    request.path_info_peek = lambda: "main"
    request.interface_name = "main"
    request.get_user = _get_user
    request.registry.validate_user = default_user_validator
    request.client_addr = None
    if authentication and user is None:
        request._get_authentication_policy = lambda: create_authentication({
            "authtkt_cookie_name": "__test",
            "authtkt_secret": "123",
        })
    elif user is not None:
        config.testing_securitypolicy(user)
    request.set_property(
        create_get_user_from_request({"authorized_referers": [request.referer]}),
        name="user",
        reify=True
    )
    return request
