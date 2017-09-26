# -*- coding: utf-8 -*-

# Copyright (c) 2013-2017, Camptocamp SA
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


from unittest2 import TestCase

import transaction
from geoalchemy2 import WKTElement
from pyramid import testing

from c2cgeoportal.lib import functionality
from tests.functional import (  # noqa
    teardown_common as teardown_module,
    setup_common as setup_module,
    mapserv_url, create_dummy_request, create_default_ogcserver,
)

import logging
log = logging.getLogger(__name__)


class TestThemeEditing(TestCase):

    def setup_method(self, _):
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None
        self._tables = []

        functionality.FUNCTIONALITIES_TYPES = None

        from c2cgeoportal.models import DBSession, User, Role, \
            RestrictionArea, TreeItem, Theme, LayerGroup, Interface, LayerWMS

        from sqlalchemy import Column, Table, types
        from sqlalchemy.ext.declarative import declarative_base
        from geoalchemy2 import Geometry

        for o in DBSession.query(RestrictionArea).all():
            DBSession.delete(o)
        for o in DBSession.query(Role).all():
            DBSession.delete(o)
        for o in DBSession.query(User).all():
            DBSession.delete(o)
        for o in DBSession.query(TreeItem).all():
            DBSession.delete(o)
        ogcserver, ogcserver_external = create_default_ogcserver()

        role1 = Role(name="__test_role1")
        role1.id = 999
        user1 = User(username="__test_user1", password="__test_user1", role=role1)
        user1.email = "__test_user1@example.com"

        role2 = Role(name="__test_role2", extent=WKTElement(
            "POLYGON((1 2, 1 4, 3 4, 3 2, 1 2))", srid=21781
        ))
        user2 = User(username="__test_user2", password="__test_user2", role=role2)

        main = Interface(name="main")

        engine = DBSession.c2c_rw_bind
        engine.connect()
        a_geo_table = Table(
            "a_geo_table", declarative_base(bind=engine).metadata,
            Column("id", types.Integer, primary_key=True),
            Column("geom", Geometry("POINT", srid=21781)),
            schema="geodata"
        )

        self._tables = [a_geo_table]
        a_geo_table.drop(checkfirst=True)
        a_geo_table.create()

        private_layer = LayerWMS(name="__test_private_layer", public=False)
        private_layer.layer = "__test_private_layer"
        private_layer.geo_table = "geodata.a_geo_table"
        private_layer.interfaces = [main]
        private_layer.ogc_server = ogcserver

        group = LayerGroup(name="__test_layer_group")
        group.children = [private_layer]

        theme = Theme(name="__test_theme")
        theme.children = [group]
        theme.interfaces = [main]

        DBSession.add(RestrictionArea(
            name="__test_ra1", description="", layers=[private_layer],
            roles=[role1],
        ))
        DBSession.add(RestrictionArea(
            name="__test_ra2", description="", layers=[private_layer],
            roles=[role2], readwrite=True,
        ))

        DBSession.add_all([
            user1, user2, role1, role2, theme, group, private_layer,
        ])

        transaction.commit()

    def teardown_method(self, _):
        testing.tearDown()

        functionality.FUNCTIONALITIES_TYPES = None

        from c2cgeoportal.models import DBSession, User, Role, Layer, \
            RestrictionArea, Theme, LayerGroup, Interface, OGCServer

        DBSession.query(User).filter(User.username == "__test_user1").delete()
        DBSession.query(User).filter(User.username == "__test_user2").delete()

        ra = DBSession.query(RestrictionArea).filter(
            RestrictionArea.name == "__test_ra1"
        ).one()
        ra.roles = []
        DBSession.delete(ra)
        ra = DBSession.query(RestrictionArea).filter(
            RestrictionArea.name == "__test_ra2"
        ).one()
        ra.roles = []
        DBSession.delete(ra)

        DBSession.query(Role).filter(Role.name == "__test_role1").delete()
        DBSession.query(Role).filter(Role.name == "__test_role2").delete()

        for t in DBSession.query(Theme).filter(Theme.name == "__test_theme").all():
            DBSession.delete(t)
        for g in DBSession.query(LayerGroup).all():
            DBSession.delete(g)
        for layer in DBSession.query(Layer).all():
            DBSession.delete(layer)
        DBSession.query(Interface).filter(
            Interface.name == "main"
        ).delete()
        DBSession.query(OGCServer).delete()

        for table in self._tables[::-1]:
            table.drop(checkfirst=True)

        transaction.commit()

    @staticmethod
    def _create_request_obj(username=None, params=None, **kwargs):
        if params is None:
            params = {}
        from c2cgeoportal.models import DBSession, User

        request = create_dummy_request(**kwargs)
        request.static_url = lambda url: "/dummy/static/url"
        request.route_url = lambda url, **kwargs: mapserv_url
        request.interface_name = "main"
        request.params = params

        if username is not None:
            request.user = DBSession.query(User) \
                .filter_by(username=username).one()

        return request

    def test_themev2_noauth_edit_permission(self):
        from c2cgeoportal.views.entry import Entry

        request = self._create_request_obj()
        request.params = {
            "interface": "main",
            "version": "2"
        }
        entry = Entry(request)
        themes = entry.themes()
        self.assertEqual(set(themes["errors"]), set())
        self.assertEqual([t["name"] for t in themes["themes"]], [])

    def test_themev2_auth_no_edit_permission(self):
        from c2cgeoportal.views.entry import Entry

        request = self._create_request_obj(username="__test_user1")
        request.params = {
            "interface": "main",
            "version": "2"
        }
        entry = Entry(request)
        themes = entry.themes()
        self.assertEqual(set(themes["errors"]), set())
        self.assertEqual([t["name"] for t in themes["themes"]], ["__test_theme"])
        self.assertEqual([c["name"] for c in themes["themes"][0]["children"]], ["__test_layer_group"])

        layers = themes["themes"][0]["children"][0]["children"]
        self.assertEqual([l["name"] for l in layers], ["__test_private_layer"])
        self.assertEqual("editable" in layers[0], False)

    def test_themev2_auth_edit_permission(self):
        from c2cgeoportal.views.entry import Entry

        request = self._create_request_obj(username="__test_user2", params={
            "min_levels": "0"
        })
        request.params = {
            "interface": "main",
            "version": "2"
        }

        entry = Entry(request)
        themes = entry.themes()
        self.assertEqual(set(themes["errors"]), set())
        self.assertEqual([t["name"] for t in themes["themes"]], ["__test_theme"])
        self.assertEqual([c["name"] for c in themes["themes"][0]["children"]], ["__test_layer_group"])

        layers = themes["themes"][0]["children"][0]["children"]
        self.assertEqual([l["name"] for l in layers], ["__test_private_layer"])
        self.assertEqual("editable" in layers[0], True)
        self.assertEqual(layers[0]["editable"], True)
