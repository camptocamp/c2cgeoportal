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
from nose.plugins.attrib import attr

import re
import transaction
import os
import json
from geoalchemy2 import WKTElement
from pyramid import testing

from c2cgeoportal.lib import functionality
from c2cgeoportal.tests.functional import (  # noqa
    tear_down_common as tearDownModule,
    set_up_common as setUpModule,
    mapserv_url, mapserv, host, create_dummy_request,
    create_default_ogcserver,
)

import logging
log = logging.getLogger(__name__)


@attr(functional=True)
class TestEntryView(TestCase):

    def setUp(self):  # noqa
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None

        functionality.FUNCTIONALITIES_TYPES = None

        from c2cgeoportal.models import DBSession, User, Role, LayerV1, \
            RestrictionArea, Theme, LayerGroup, Functionality, Interface, \
            LayerWMS, OGCServer, FullTextSearch, OGCSERVER_TYPE_GEOSERVER, OGCSERVER_AUTH_GEOSERVER
        from sqlalchemy import func

        role1 = Role(name=u"__test_role1")
        role1.id = 999
        user1 = User(username=u"__test_user1", password=u"__test_user1", role=role1)
        user1.email = "__test_user1@example.com"

        role2 = Role(name=u"__test_role2", extent=WKTElement(
            "POLYGON((1 2, 1 4, 3 4, 3 2, 1 2))", srid=21781
        ))
        user2 = User(username=u"__test_user2", password=u"__test_user2", role=role2)

        main = Interface(name=u"desktop")
        mobile = Interface(name=u"mobile")

        public_layer = LayerV1(name=u"__test_public_layer", public=True)
        public_layer.is_checked = False
        public_layer.interfaces = [main, mobile]

        private_layer = LayerV1(name=u"__test_private_layer", public=False)
        private_layer.geo_table = "a_schema.a_geo_table"
        private_layer.interfaces = [main, mobile]

        ogcserver, ogcserver_external = create_default_ogcserver()
        ogcserver_normapfile = OGCServer(name="__test_ogc_server_notmapfile")
        ogcserver_normapfile.url = mapserv_url + "?map=not_a_mapfile"
        ogcserver_geoserver = OGCServer(name="__test_ogc_server_geoserver")
        ogcserver_geoserver.url = mapserv
        ogcserver_geoserver.type = OGCSERVER_TYPE_GEOSERVER
        ogcserver_geoserver.auth = OGCSERVER_AUTH_GEOSERVER

        public_layer2 = LayerWMS(
            name=u"__test_public_layer2", layer=u"__test_public_layer_bis", public=True)
        public_layer2.interfaces = [main, mobile]
        public_layer2.ogc_server = ogcserver

        private_layer2 = LayerWMS(
            name=u"__test_private_layer2", layer=u"__test_private_layer_bis", public=False)
        private_layer2.interfaces = [main, mobile]
        private_layer2.ogc_server = ogcserver

        public_layer_not_mapfile = LayerWMS(
            name=u"__test_public_layer_not_mapfile", layer=u"__test_public_layer_not_in_mapfile", public=True)
        public_layer_not_mapfile.interfaces = [main, mobile]
        public_layer_not_mapfile.ogc_server = ogcserver

        public_layer_no_layers = LayerWMS(
            name=u"__test_public_layer_no_layers", public=True)
        public_layer_no_layers.interfaces = [main, mobile]
        public_layer_no_layers.ogc_server = ogcserver

        layer_in_group = LayerV1(name=u"__test_layer_in_group")
        layer_in_group.interfaces = [main, mobile]
        layer_group = LayerGroup(name=u"__test_layer_group_1")
        layer_group.children = [layer_in_group]

        layer_wmsgroup = LayerV1(name=u"test_wmsfeaturesgroup")
        layer_wmsgroup.is_checked = False
        layer_wmsgroup.interfaces = [main, mobile]

        group = LayerGroup(name=u"__test_layer_group_2")
        group.children = [
            public_layer, private_layer, layer_group, layer_wmsgroup,
            public_layer2, public_layer_not_mapfile, public_layer_no_layers,
            private_layer2
        ]
        theme = Theme(name=u"__test_theme")
        theme.children = [group]
        theme.interfaces = [main]

        functionality1 = Functionality(name=u"test_name", value=u"test_value_1")
        functionality2 = Functionality(name=u"test_name", value=u"test_value_2")
        theme.functionalities = [functionality1, functionality2]

        poly = "POLYGON((-100 0, -100 20, 100 20, 100 0, -100 0))"

        area = WKTElement(poly, srid=21781)
        RestrictionArea(
            name=u"__test_ra1", description=u"", layers=[private_layer, private_layer2],
            roles=[role1], area=area
        )

        area = WKTElement(poly, srid=21781)
        RestrictionArea(
            name=u"__test_ra2", description=u"", layers=[private_layer, private_layer2],
            roles=[role2], area=area, readwrite=True
        )

        entry1 = FullTextSearch()
        entry1.label = "label1"
        entry1.layer_name = "layer1"
        entry1.ts = func.to_tsvector("french", "soleil travail")
        entry1.the_geom = WKTElement("POINT(-90 -45)", 21781)
        entry1.public = True

        entry2 = FullTextSearch()
        entry2.label = "label1"
        entry2.layer_name = "layer1"
        entry2.ts = func.to_tsvector("french", "soleil travail")
        entry2.the_geom = WKTElement("POINT(-90 -45)", 21781)
        entry2.public = True

        entry3 = FullTextSearch()
        entry3.label = "label1"
        entry3.layer_name = None
        entry3.ts = func.to_tsvector("french", "soleil travail")
        entry3.the_geom = WKTElement("POINT(-90 -45)", 21781)
        entry3.public = True

        DBSession.add_all([
            user1, user2, ogcserver_normapfile, ogcserver_geoserver,
            public_layer, private_layer, public_layer2, private_layer2,
            entry1, entry2, entry3,
        ])

        transaction.commit()

    @staticmethod
    def tearDown():  # noqa
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

        for layer in DBSession.query(Layer).all():
            DBSession.delete(layer)
        for g in DBSession.query(LayerGroup).all():
            DBSession.delete(g)
        for t in DBSession.query(Theme).all():
            DBSession.delete(t)
        DBSession.query(Interface).filter(
            Interface.name == "desktop"
        ).delete()
        DBSession.query(OGCServer).delete()

        transaction.commit()

    #
    # login/logout tests
    #

    def test_login(self):
        from pyramid.httpexceptions import HTTPBadRequest
        from c2cgeoportal.views.entry import Entry

        request = self._create_request_obj(params={
            "came_from": "/came_from",
        }, POST={
            "login": u"__test_user1",
            "password": u"__test_user1",
        })
        response = Entry(request).login()
        self.assertEquals(response.status_int, 302)
        self.assertEquals(response.headers["Location"], "/came_from")

        request = self._create_request_obj(POST={
            "login": u"__test_user1",
            "password": u"__test_user1",
        })
        response = Entry(request).login()
        self.assertEquals(response.status_int, 200)
        self.assertEquals(json.loads(response.body), {
            "success": True,
            "username": "__test_user1",
            "is_password_changed": False,
            "role_name": "__test_role1",
            "role_id": 999,
            "functionalities": {},
        })

        request = self._create_request_obj(POST={
            "login": u"__test_user1",
            "password": u"bad password",
        })
        entry = Entry(request)
        self.assertRaises(HTTPBadRequest, entry.login)

    def test_logout_no_auth(self):
        from pyramid.httpexceptions import HTTPBadRequest
        from c2cgeoportal.views.entry import Entry

        request = self._create_request_obj(path="/", params={
            "came_from": "/came_from"
        })
        entry = Entry(request)
        self.assertRaises(HTTPBadRequest, entry.logout)

    def test_logout(self):
        from c2cgeoportal.models import DBSession, User
        from c2cgeoportal.views.entry import Entry

        request = self._create_request_obj(path="/")
        request.user = DBSession.query(User).filter_by(
            username=u"__test_user1"
        ).one()
        response = Entry(request).logout()
        self.assertEquals(response.status_int, 200)
        self.assertEquals(response.body, "true")

        request = self._create_request_obj(path="/")
        request.route_url = lambda url: "/dummy/route/url"
        request.user = DBSession.query(User).filter_by(
            username=u"__test_user1"
        ).one()
        response = Entry(request).logout()
        self.assertEquals(response.status_int, 200)
        self.assertEquals(response.body, "true")

    def test_reset_password(self):
        from c2cgeoportal.views.entry import Entry

        request = self._create_request_obj(POST={
            "login": u"__test_user1",
        })
        entry = Entry(request)
        user, username, password, error = entry._loginresetpassword()

        request = self._create_request_obj(POST={
            "login": username,
            "password": password,
        })
        response = Entry(request).login()
        self.assertEquals(response.status_int, 200)
        self.assertEquals(json.loads(response.body), {
            "success": True,
            "username": "__test_user1",
            "is_password_changed": True,
            "role_name": "__test_role1",
            "role_id": 999,
            "functionalities": {},
        })

    #
    # viewer view tests
    #

    @staticmethod
    def _create_request_obj(username=None, params=None, **kwargs):
        if params is None:
            params = {}
        from c2cgeoportal.models import DBSession, User

        request = create_dummy_request(**kwargs)
        request.static_url = lambda url: "/dummy/static/url"
        request.route_url = lambda url, **kwargs: mapserv_url
        request.interface_name = "desktop"
        request.params = params

        if username is not None:
            request.user = DBSession.query(User) \
                .filter_by(username=username).one()

        return request

    def _create_entry_obj(self, **kwargs):
        from c2cgeoportal.views.entry import Entry

        return Entry(self._create_request_obj(**kwargs))

    @staticmethod
    def _get_filtered_errors(errors):
        regex = re.compile("The layer \\'[a-z0-9_]*\\' \([a-z0-9_]*\) is not defined in WMS capabilities from \\'[a-z0-9_]*\\'")
        errors = [e for e in errors if not regex.match(e)]
        return set(errors)

    def test_index_no_auth(self):
        entry = self._create_entry_obj()
        response = entry.get_cgxp_viewer_vars()
        assert "__test_public_layer" in response["themes"]
        assert "__test_private_layer" not in response["themes"]

    def test_index_auth_no_edit_permission(self):
        import json

        entry = self._create_entry_obj(username=u"__test_user1")
        response = entry.get_cgxp_viewer_vars()

        themes = json.loads(response["themes"])
        self.assertEqual(len(themes), 1)

        layers = themes[0]["children"][0]["children"]
        self.assertEqual(len(layers), 4)

        self.assertEqual([
            "editable" in layer
            for layer in themes[0]["children"][0]["children"]
            if layer["name"] == "test_wmsfeaturesgroup"
        ], [False])

        self.assertEqual([
            "editable" in layer
            for layer in themes[0]["children"][0]["children"]
            if layer["name"] == "__test_private_layer"
        ], [False])

        self.assertEqual([
            "editable" in layer
            for layer in themes[0]["children"][0]["children"]
            if layer["name"] == "__test_public_layer"
        ], [False])

    def test_index_auth_edit_permission(self):
        import json

        entry = self._create_entry_obj(username=u"__test_user2", params={
            "min_levels": "0"
        })
        response = entry.get_cgxp_viewer_vars()

        self.assertEqual(
            self._get_filtered_errors(json.loads(response["serverError"])),
            set()
        )

        themes = json.loads(response["themes"])
        self.assertEqual(len(themes), 1)

        layers = themes[0]["children"][0]["children"]
        self.assertEqual(len(layers), 4)

        self.assertEqual([
            "editable" in layer
            for layer in themes[0]["children"][0]["children"]
            if layer["name"] == "test_wmsfeaturesgroup"
        ], [False])

        self.assertEqual([
            "editable" in layer
            for layer in themes[0]["children"][0]["children"]
            if layer["name"] == "__test_private_layer"
        ], [True])

        self.assertEqual([
            "editable" in layer
            for layer in themes[0]["children"][0]["children"]
            if layer["name"] == "__test_public_layer"
        ], [False])

    def test_theme(self):
        from c2cgeoportal.models import DBSession, User
        from c2cgeoportal.views.entry import Entry
        request = self._create_request_obj()
        entry = Entry(request)

        # unautenticated
        themes, errors = entry._themes(None, "desktop")
        self.assertEquals(errors, set([
            u"The layer '__test_layer_in_group' (__test_layer_in_group) is not defined in WMS capabilities from '__test_ogc_server'",
        ]))
        self.assertEquals(len(themes), 1)
        layers = {l["name"] for l in themes[0]["children"][0]["children"]}
        self.assertEquals(layers, set([
            u"test_wmsfeaturesgroup",
            u"__test_layer_group_1",
            u"__test_public_layer",
        ]))

        # autenticated on parent
        request.params = {
            "role_id": DBSession.query(User).filter_by(username=u"__test_user1").one().role.id
        }
        request.client_addr = "127.0.0.1"
        themes = entry.themes()
        self.assertEquals(len(themes), 1)
        layers = [l["name"] for l in themes[0]["children"][0]["children"]]
        self.assertTrue("__test_public_layer" in layers)
        self.assertTrue("__test_private_layer" in layers)

        # autenticated
        request.params = {}
        request.user = DBSession.query(User).filter_by(username=u"__test_user1").one()
        themes, errors = entry._themes(request.user.role.id)
        self.assertEquals(errors, set([
            u"The layer '__test_layer_in_group' (__test_layer_in_group) is not defined in WMS capabilities from '__test_ogc_server'",
        ]))
        self.assertEquals(len(themes), 1)
        layers = {l["name"] for l in themes[0]["children"][0]["children"]}
        self.assertEquals(layers, set([
            u"test_wmsfeaturesgroup",
            u"__test_layer_group_1",
            u"__test_public_layer",
            u"__test_private_layer",
        ]))

    def test_notmapfile(self):
        # mapfile error
        from c2cgeoportal.views.entry import Entry
        request = self._create_request_obj(additional_settings={
            "mapserverproxy": {
                "default_ogc_server": "__test_ogc_server_notmapfile",
            }
        })
        entry = Entry(request)
        request.params = {}

        from c2cgeoportal.lib import caching
        caching.invalidate_region()
        themes, errors = entry._themes(None, "desktop")
        self.assertEquals(errors, set([
            u"The layer '__test_public_layer' (__test_public_layer) is not defined in WMS capabilities from '__test_ogc_server_notmapfile'",
            u"The layer '__test_layer_in_group' (__test_layer_in_group) is not defined in WMS capabilities from '__test_ogc_server_notmapfile'",
            u"The layer 'test_wmsfeaturesgroup' (test_wmsfeaturesgroup) is not defined in WMS capabilities from '__test_ogc_server_notmapfile'",
            u'GetCapabilities from URL http://localhost/cgi-bin/mapserv?map=not_a_mapfile&VERSION=1.1.1&REQUEST=GetCapabilities&SERVICE=WMS returns a wrong Content-Type: text/html\n<HTML>\n<HEAD><TITLE>MapServer Message</TITLE></HEAD>\n<!-- MapServer version 7.0.0 OUTPUT=PNG OUTPUT=JPEG OUTPUT=KML SUPPORTS=PROJ SUPPORTS=AGG SUPPORTS=FREETYPE SUPPORTS=CAIRO SUPPORTS=SVG_SYMBOLS SUPPORTS=RSVG SUPPORTS=ICONV SUPPORTS=WMS_SERVER SUPPORTS=WMS_CLIENT SUPPORTS=WFS_SERVER SUPPORTS=WFS_CLIENT SUPPORTS=WCS_SERVER SUPPORTS=SOS_SERVER SUPPORTS=FASTCGI SUPPORTS=THREADS SUPPORTS=GEOS INPUT=JPEG INPUT=POSTGIS INPUT=OGR INPUT=GDAL INPUT=SHAPEFILE -->\n<BODY BGCOLOR="#FFFFFF">\nmsLoadMap(): Regular expression error. MS_DEFAULT_MAPFILE_PATTERN validation failed.\n</BODY></HTML>',
        ]))

    def test_themev2(self):
        from c2cgeoportal.models import DBSession, User
        from c2cgeoportal.views.entry import Entry
        request = self._create_request_obj()
        entry = Entry(request)

        # unautenticated
        request.params = {
            "version": "2"
        }
        themes = entry.themes()
        self.assertEquals(len(themes["themes"]), 1)
        layers = {l["name"] for l in themes["themes"][0]["children"][0]["children"]}
        self.assertEquals(layers, set([
            u"__test_public_layer2",
            u"__test_public_layer_not_mapfile",
        ]))

        self.assertEquals(set(themes["errors"]), set([
            u"The layer '__test_public_layer_not_in_mapfile' (__test_public_layer_not_mapfile) is not defined in WMS capabilities from '__test_ogc_server'",
            u"The layer '__test_public_layer_no_layers' do not have any layers",
        ]))

        # autenticated
        request.params = {
            "version": "2"
        }
        request.user = DBSession.query(User).filter_by(username=u"__test_user1").one()
        themes = entry.themes()
        self.assertEquals(len(themes["themes"]), 1)
        layers = {l["name"] for l in themes["themes"][0]["children"][0]["children"]}
        self.assertEquals(layers, set([
            u"__test_public_layer2",
            u"__test_private_layer2",
            u"__test_public_layer_not_mapfile",
        ]))
        self.assertEquals(set(themes["errors"]), set([
            u"The layer '__test_public_layer_not_in_mapfile' (__test_public_layer_not_mapfile) is not defined in WMS capabilities from '__test_ogc_server'",
            u"The layer '__test_public_layer_no_layers' do not have any layers",
        ]))

    def test_theme_geoserver(self):
        from c2cgeoportal.models import DBSession, User
        from c2cgeoportal.views.entry import Entry
        request = self._create_request_obj(additional_settings={
            "mapserverproxy": {
                "default_ogc_server": "__test_ogc_server_geoserver",
            }
        })
        entry = Entry(request)

        # unautenticated v1
        themes, errors = entry._themes(None, "desktop")
        self.assertEquals(errors, set())
        self.assertEquals(len(themes), 1)
        layers = {l["name"] for l in themes[0]["children"][0]["children"]}
        self.assertEquals(layers, set([
            u"test_wmsfeaturesgroup",
            u"__test_public_layer",
            u"__test_layer_group_1",
        ]))

        # autenticated v1
        request.params = {}
        request.user = DBSession.query(User).filter_by(username=u"__test_user1").one()
        themes, errors = entry._themes(request.user.role.id)
        self.assertEquals(errors, set())
        self.assertEquals(len(themes), 1)
        layers = {l["name"] for l in themes[0]["children"][0]["children"]}
        self.assertEquals(layers, set([
            u"test_wmsfeaturesgroup",
            u"__test_public_layer",
            u"__test_private_layer",
            u"__test_layer_group_1",
        ]))

        # do not test anything related to geoserver ...
        # unautenticated v2
        request.params = {
            "version": "2"
        }
        request.user = None
        themes = entry.themes()
        self.assertEquals(set(themes["errors"]), set([
            u"The layer '__test_public_layer_not_in_mapfile' (__test_public_layer_not_mapfile) is not defined in WMS capabilities from '__test_ogc_server'",
            u"The layer '__test_public_layer_no_layers' do not have any layers",
        ]))
        self.assertEquals(len(themes["themes"]), 1)
        layers = {l["name"] for l in themes["themes"][0]["children"][0]["children"]}
        self.assertEquals(layers, set([
            u"__test_public_layer2",
            u"__test_public_layer_not_mapfile",
        ]))

        # autenticated v2
        request.params = {
            "version": "2"
        }
        request.user = DBSession.query(User).filter_by(username=u"__test_user1").one()
        themes = entry.themes()
        self.assertEquals(set(themes["errors"]), set([
            u"The layer '__test_public_layer_not_in_mapfile' (__test_public_layer_not_mapfile) is not defined in WMS capabilities from '__test_ogc_server'",
            u"The layer '__test_public_layer_no_layers' do not have any layers",
        ]))
        self.assertEquals(len(themes["themes"]), 1)
        layers = {l["name"] for l in themes["themes"][0]["children"][0]["children"]}
        self.assertEquals(layers, set([
            u"__test_public_layer2",
            u"__test_private_layer2",
            u"__test_public_layer_not_mapfile",
        ]))

    def test_wfs_types(self):
        from c2cgeoportal.views.entry import Entry

        request = self._create_request_obj()
        entry = Entry(request)

        response = entry.get_cgxp_viewer_vars()
        self.assertEquals(
            self._get_filtered_errors(json.loads(response["serverError"])),
            set()
        )

        result = set([
            "testpoint_unprotected",
            "testpoint_protected",
            "testpoint_protected_2",
            "testpoint_protected_query_with_collect",
            "testpoint_substitution",
            "testpoint_column_restriction",
            "test_wmsfeatures",
            "test_wmstime",
            "test_wmstime2",
            "__test_public_layer",
            "__test_private_layer",
            "__test_public_layer_bis",
            "__test_private_layer_bis",
            "__test_layer_internal_wms",
            "test_noscale",
            "test_minscale",
            "test_maxscale",
            "test_boothscale",
        ])

        self.assertEquals(set(json.loads(response["WFSTypes"])), result)
        self.assertEquals(set(json.loads(response["externalWFSTypes"])), result)

    def test_permalink_themes(self):
        from c2cgeoportal.views.entry import Entry
        request = self._create_request_obj()
        request.params = {
            "permalink_themes": "my_themes",
        }
        entry = Entry(request)

        response = entry.get_cgxp_viewer_vars()
        self.assertEquals(response["permalink_themes"], '["my_themes"]')

    def _create_entry(self):
        from c2cgeoportal.views.entry import Entry

        request = self._create_request_obj()
        request.current_route_url = lambda **kwargs: "http://example.com/current/view"
        request.registry.settings.update({
            "layers": {
                "enum": {
                    "layer_test": {
                        "attributes": {
                            "label": None
                        }
                    }
                }
            }
        })
        request.matchdict = {
            "themes": ["theme"],
        }
        entry = Entry(request)
        request.user = None
        return entry, request

    def test_entry_points(self):
        entry, request = self._create_entry()

        result = entry.get_cgxp_index_vars()
        self.assertEquals(
            set(result.keys()),
            set(["lang", "debug", "extra_params"])
        )
        result = entry.get_cgxp_viewer_vars()
        self.assertEquals(set(result.keys()), set([
            "lang", "tiles_url", "debug",
            "serverError", "themes", "external_themes", "functionality",
            "WFSTypes", "externalWFSTypes", "user", "queryer_attribute_urls",
            "version_role_params", "version_params",
        ]))
        self.assertEquals(
            result["queryer_attribute_urls"],
            '{{"layer_test": {{"label": "{0!s}"}}}}'.format(mapserv_url)
        )

        result = entry.get_ngeo_index_vars()
        self.assertEquals(set(result.keys()), set([
            "debug", "fulltextsearch_groups", "wfs_types"
        ]))
        result = entry.get_ngeo_permalinktheme_vars()
        self.assertEquals(set(result.keys()), set([
            "debug", "fulltextsearch_groups", "permalink_themes", "wfs_types"
        ]))

        result = entry.apijs()
        self.assertEquals(
            set(result.keys()),
            set(["lang", "debug", "queryable_layers", "tiles_url", "url_params"])
        )
        result = entry.xapijs()
        self.assertEquals(
            set(result.keys()),
            set(["lang", "debug", "queryable_layers", "tiles_url", "url_params"])
        )
        result = entry.apihelp()
        self.assertEquals(set(result.keys()), set(["lang", "debug"]))
        result = entry.xapihelp()
        self.assertEquals(set(result.keys()), set(["lang", "debug"]))

    def test_ngeo_vars(self):
        entry, _ = self._create_entry()
        result = entry.get_ngeo_index_vars()
        self.assertEquals(
            result["fulltextsearch_groups"],
            ["layer1"],
        )

    def test_auth_home(self):
        from c2cgeoportal.views.entry import Entry
        from c2cgeoportal.models import User, Role

        request = self._create_request_obj()
        request.registry.settings.update({
            "layers": {
                "enum": {
                    "layer_test": {
                        "attributes": {
                            "label": None
                        }
                    }
                }
            }
        })
        entry = Entry(request)
        request.user = User()
        request.user.username = "a user"
        request.user.role_name = "a role"
        request.user._cached_role = Role()
        request.user._cached_role.name = "a role"
        request.user._cached_role_name = "a role"

        result = entry.get_cgxp_index_vars()
        self.assertEquals(
            set(result.keys()),
            set(["lang", "debug", "extra_params"])
        )
        self.assertEquals(
            set(result["extra_params"].keys()),
            set(["lang"])
        )
        self.assertEquals(result["extra_params"]["lang"], "fr")

    def test_entry_points_version(self):
        from c2cgeoportal.views.entry import Entry

        request = testing.DummyRequest()
        request.user = None
        request.headers["Host"] = host

        request.static_url = lambda url: "http://example.com/dummy/static/url"
        request.route_url = lambda url, **kwargs: mapserv
        request.registry.settings = {
            "default_max_age": 76,
            "layers": {
                "enum": {
                    "layer_test": {
                        "attributes": {
                            "label": None
                        }
                    }
                }
            }
        }
        entry = Entry(request)
        request.user = None

        result = entry.get_cgxp_index_vars()
        self.assertEquals(
            set(result.keys()),
            set(["lang", "debug", "extra_params"])
        )

    def test_entry_points_wfs(self):
        from c2cgeoportal.views.entry import Entry
        from c2cgeoportal.models import User, Role

        request = self._create_request_obj()
        request.registry.settings.update({
            "layers": {
                "enum": {
                    "layer_test": {
                        "attributes": {
                            "label": None
                        }
                    }
                }
            }
        })
        entry = Entry(request)
        request.user = User()
        request.user.username = "a user"
        request.user.role_name = "a role"
        request.user._cached_role = Role()
        request.user._cached_role.name = "a role"
        request.user._cached_role_name = "a role"

        result = entry.get_cgxp_index_vars()
        self.assertEquals(
            set(result.keys()),
            set([
                "lang", "debug", "extra_params"
            ])
        )
        self.assertEquals(
            set(result["extra_params"].keys()),
            set(["lang"]),
        )
        self.assertEquals(result["extra_params"]["lang"], "fr")

    def test_entry_points_wfs_url(self):
        from c2cgeoportal.views.entry import Entry

        request = self._create_request_obj()
        request.registry.settings.update({
            "layers": {
                "enum": {
                    "layer_test": {
                        "attributes": {
                            "label": None
                        }
                    }
                }
            }
        })

        entry = Entry(request)

        result = entry.get_cgxp_index_vars()
        self.assertEquals(
            set(result.keys()),
            set(["lang", "debug", "extra_params"])
        )
        result = entry.get_cgxp_viewer_vars()

    def test_entry_points_noexternal(self):
        from c2cgeoportal.views.entry import Entry

        request = self._create_request_obj()
        request.registry.settings.update({
            "layers": {
                "enum": {
                    "layer_test": {
                        "attributes": {
                            "label": None
                        }
                    }
                }
            }
        })

        entry = Entry(request)

        result = entry.get_cgxp_index_vars()
        self.assertEquals(
            set(result.keys()),
            set(["lang", "debug", "extra_params"])
        )
        result = entry.get_cgxp_viewer_vars()

    def test_permalink_theme(self):
        from c2cgeoportal.views.entry import Entry
        request = self._create_request_obj()
        entry = Entry(request)

        request.matchdict = {
            "themes": ["theme"],
        }
        result = entry.get_cgxp_permalinktheme_vars()
        self.assertEquals(
            set(result.keys()),
            set([
                "lang", "permalink_themes",
                "debug", "extra_params",
            ])
        )
        self.assertEquals(
            set(result["extra_params"].keys()),
            set(["lang", "permalink_themes"])
        )
        self.assertEquals(result["extra_params"]["lang"], "fr")
        self.assertEquals(result["extra_params"]["permalink_themes"], ["theme"])
        self.assertEquals(result["permalink_themes"], ["theme"])

        request.matchdict = {
            "themes": ["theme1", "theme2"],
        }
        result = entry.get_cgxp_permalinktheme_vars()
        self.assertEquals(
            set(result.keys()),
            set([
                "lang", "permalink_themes", "debug", "extra_params"
            ])
        )
        self.assertEquals(
            set(result["extra_params"].keys()),
            set(["lang", "permalink_themes"])
        )
        self.assertEquals(result["extra_params"]["lang"], "fr")
        self.assertEquals(result["extra_params"]["permalink_themes"], ["theme1", "theme2"])
        self.assertEquals(result["permalink_themes"], ["theme1", "theme2"])

    def test_layer(self):
        import httplib2
        from c2cgeoportal.views.entry import Entry
        from c2cgeoportal.models import LayerV1, LayerGroup
        from c2cgeoportal.lib.wmstparsing import TimeInformation

        request = self._create_request_obj()
        request.static_url = lambda name: "/dummy/static/" + name
        request.route_url = lambda name: "/dummy/route/" + name
        request.registry.settings["package"] = "test_layer"
        entry = Entry(request)

        self.assertEqual(entry._group(
            "", LayerGroup(), layers=[]), (None, set())
        )

        layer = LayerV1()
        layer.id = 20
        layer.name = "test internal WMS"
        layer.layer = "test internal WMS"
        layer.metadata_url = "http://example.com/tiwms"
        layer.is_checked = True
        layer.layer_type = "internal WMS"
        layer.image_type = "image/png"
        layer.style = "my-style"
        layer.kml = "static:///tiwms.kml"
        layer.legend = True
        layer.legend_rule = "rule"
        layer.legend_image = "static://legend:static/tiwms-legend.png"
        layer.is_legend_expanded = False
        layer.min_resolution = 10
        layer.max_resolution = 1000
        layer.disclaimer = "Camptocamp"
        layer.identifier_attribute_field = "name"
        layer.geo_table = "tiwms"
        layer.public = True

        self.assertEqual(entry._layer(layer, role_id=None), ({
            "id": 20,
            "name": "test internal WMS",
            "metadataURL": "http://example.com/tiwms",
            "isChecked": True,
            "icon": "/dummy/route/mapserverproxy?"
            "LAYER=test+internal+WMS&SERVICE=WMS&FORMAT=image%2Fpng&"
            "REQUEST=GetLegendGraphic&RULE=rule&VERSION=1.1.1&TRANSPARENT=TRUE",
            "type": "internal WMS",
            "imageType": "image/png",
            "style": "my-style",
            "kml": "/dummy/static/c2cgeoportal:project/tiwms.kml",
            "legend": True,
            "legendImage": "/dummy/static/legend:static/tiwms-legend.png",
            "isLegendExpanded": False,
            "minResolutionHint": 10,
            "maxResolutionHint": 1000,
            "disclaimer": "Camptocamp",
            "identifierAttribute": "name",
            "public": True,
            "metadata": {},
        }, set(["The layer 'test internal WMS' (test internal WMS) is not defined in WMS capabilities from '__test_ogc_server'"])))

        layer = LayerV1()
        layer.id = 20
        layer.name = "test external WMS"
        layer.layer = "test external WMS"
        layer.is_checked = False
        layer.icon = "static:///tewms.png"
        layer.layer_type = "external WMS"
        layer.url = "http://example.com"
        layer.image_type = "image/jpeg"
        layer.is_single_tile = True
        layer.legend = False
        layer.is_legend_expanded = False
        layer.min_resolution = 10
        layer.max_resolution = 1000
        layer.public = True
        self.assertEqual(entry._layer(layer), ({
            "id": 20,
            "name": "test external WMS",
            "icon": "/dummy/static/c2cgeoportal:project/tewms.png",
            "isChecked": False,
            "type": "external WMS",
            "url": "http://example.com",
            "imageType": "image/jpeg",
            "isSingleTile": True,
            "legend": False,
            "isLegendExpanded": False,
            "minResolutionHint": 10,
            "maxResolutionHint": 1000,
            "public": True,
            "metadata": {},
        }, set()))

        layer = LayerV1()
        layer.id = 20
        layer.name = "test WMTS"
        layer.layer = "test WMTS"
        layer.is_checked = False
        layer.layer_type = "WMTS"
        layer.url = "http://example.com/WMTS-Capabilities.xml"
        layer.style = "wmts-style"
        layer.dimensions = '{"DATE": "1012"}'
        layer.matrix_set = "swissgrid"
        layer.wms_url = "http://example.com/"
        layer.wms_layers = "test"
        layer.legend = False
        layer.is_legend_expanded = False
        layer.min_resolution = 10
        layer.max_resolution = 1000
        layer.public = True
        self.assertEqual(entry._layer(layer), ({
            "id": 20,
            "name": "test WMTS",
            "isChecked": False,
            "type": "WMTS",
            "url": "http://example.com/WMTS-Capabilities.xml",
            "style": "wmts-style",
            "dimensions": {u"DATE": u"1012"},
            "matrixSet": "swissgrid",
            "wmsUrl": "http://example.com/",
            "wmsLayers": "test",
            "legend": False,
            "isLegendExpanded": False,
            "minResolutionHint": 10,
            "maxResolutionHint": 1000,
            "public": True,
            "metadata": {},
        }, set()))

        layer = LayerV1()
        layer.id = 20
        layer.name = "test WMTS"
        layer.layer = "test WMTS"
        layer.is_checked = False
        layer.layer_type = "WMTS"
        layer.url = "http://example.com/WMTS-Capabilities.xml"
        layer.wms_url = "http://example.com/"
        layer.legend = False
        layer.is_legend_expanded = False
        layer.min_resolution = 10
        layer.max_resolution = 1000
        layer.public = True
        self.assertEqual(entry._layer(layer), ({
            "id": 20,
            "name": "test WMTS",
            "isChecked": False,
            "type": "WMTS",
            "url": "http://example.com/WMTS-Capabilities.xml",
            "wmsUrl": "http://example.com/",
            "wmsLayers": "test WMTS",
            "legend": False,
            "isLegendExpanded": False,
            "minResolutionHint": 10,
            "maxResolutionHint": 1000,
            "public": True,
            "metadata": {},
        }, set()))

        layer = LayerV1()
        layer.id = 20
        layer.name = "test WMTS"
        layer.layer = "test WMTS"
        layer.is_checked = False
        layer.layer_type = "WMTS"
        layer.url = "http://example.com/WMTS-Capabilities.xml"
        layer.wms_layers = "test"
        layer.legend = False
        layer.is_legend_expanded = False
        layer.min_resolution = 10
        layer.max_resolution = 1000
        layer.public = True
        self.assertEqual(entry._layer(layer), ({
            "id": 20,
            "name": "test WMTS",
            "isChecked": False,
            "type": "WMTS",
            "url": "http://example.com/WMTS-Capabilities.xml",
            "wmsUrl": "/dummy/route/mapserverproxy",
            "wmsLayers": "test",
            "queryLayers": [],
            "legend": False,
            "isLegendExpanded": False,
            "minResolutionHint": 10,
            "maxResolutionHint": 1000,
            "public": True,
            "metadata": {},
        }, set()))

        layer = LayerV1()
        layer.id = 20
        layer.name = "test no 2D"
        layer.layer = "test no 2D"
        layer.is_checked = False
        layer.layer_type = "no 2D"
        layer.legend = False
        layer.is_legend_expanded = False
        layer.metadata_url = "http://example.com/wmsfeatures.metadata"
        layer.public = True
        self.assertEqual(entry._layer(layer), ({
            "id": 20,
            "name": u"test no 2D",
            "isChecked": False,
            "type": "no 2D",
            "legend": False,
            "isLegendExpanded": False,
            "metadataURL": u"http://example.com/wmsfeatures.metadata",
            "public": True,
            "metadata": {},
        }, set()))

        curdir = os.path.dirname(os.path.abspath(__file__))
        mapfile = os.path.join(curdir, "c2cgeoportal_test.map")

        mapfile = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "c2cgeoportal_test.map"
        )
        params = (
            ("map", mapfile),
            ("SERVICE", "WMS"),
            ("VERSION", "1.1.1"),
            ("REQUEST", "GetCapabilities"),
        )
        mapserv = "{0!s}?map={1!s}&".format(mapserv_url, mapfile)
        url = mapserv + "&".join(["=".join(p) for p in params])
        http = httplib2.Http()
        h = {"Host": host}
        resp, xml = http.request(url, method="GET", headers=h)

        layer = LayerV1()
        layer.id = 20
        layer.name = "test_wmsfeaturesgroup"
        layer.layer = "test_wmsfeaturesgroup"
        layer.layer_type = "internal WMS"
        layer.image_type = "image/png"
        layer.is_checked = False
        layer.legend = False
        layer.is_legend_expanded = False
        layer.public = True
        self.assertEqual(entry._layer(layer), ({
            "id": 20,
            "name": u"test_wmsfeaturesgroup",
            "type": "internal WMS",
            "isChecked": False,
            "legend": False,
            "isLegendExpanded": False,
            "imageType": u"image/png",
            "minResolutionHint": 1.76,
            "maxResolutionHint": 8.8200000000000003,
            "public": True,
            "queryable": 0,
            "metadataUrls": [{
                "url": "http://example.com/wmsfeatures.metadata",
                "type": "TC211",
                "format": "text/plain",
            }],
            "metadata": {},
            "childLayers": [{
                "name": u"test_wmsfeatures",
                "minResolutionHint": 1.76,
                "maxResolutionHint": 8.8200000000000003,
                "queryable": 1,
            }],
        }, set()))

        layer_t1 = LayerV1()
        layer_t1.id = 20
        layer_t1.name = "test_wmstime"
        layer_t1.layer = "test_wmstime"
        layer_t1.layer_type = "internal WMS"
        layer_t1.image_type = "image/png"
        layer_t1.is_checked = False
        layer_t1.legend = False
        layer_t1.is_legend_expanded = False
        layer_t1.public = True
        layer_t1.time_mode = "value"
        time = TimeInformation()
        entry._layer(layer_t1, time=time, mixed=False)
        self.assertEqual(time.to_dict(), {
            "resolution": "year",
            "interval": (1, 0, 0, 0),
            "maxValue": "2010-01-01T00:00:00Z",
            "minValue": "2000-01-01T00:00:00Z",
            "mode": "value",
            "widget": "slider",
            "minDefValue": "2000-01-01T00:00:00Z",
            "maxDefValue": None,
        })

        layer_t2 = LayerV1()
        layer_t2.id = 30
        layer_t2.name = "test_wmstime2"
        layer_t2.layer = "test_wmstime2"
        layer_t2.layer_type = "internal WMS"
        layer_t2.image_type = "image/png"
        layer_t2.is_checked = False
        layer_t2.legend = False
        layer_t2.is_legend_expanded = False
        layer_t2.public = True
        layer_t2.time_mode = "value"
        layer_t2.time_widget = "slider"
        time = TimeInformation()
        entry._layer(layer_t2, time=time, mixed=False)
        self.assertEqual(time.to_dict(), {
            "resolution": "year",
            "interval": (1, 0, 0, 0),
            "maxValue": "2020-01-01T00:00:00Z",
            "minValue": "2015-01-01T00:00:00Z",
            "mode": "value",
            "widget": "slider",
            "minDefValue": "2015-01-01T00:00:00Z",
            "maxDefValue": None,
        })

        group = LayerGroup()
        group.name = "time"
        group.children = [layer_t1, layer_t2]
        time = TimeInformation()
        entry._group(
            "", group, [layer_t1.name, layer_t2.name],
            time=time, mixed=False, depth=2
        )
        self.assertEqual(time.to_dict(), {
            "resolution": "year",
            "interval": (1, 0, 0, 0),
            "maxValue": "2020-01-01T00:00:00Z",
            "minValue": "2000-01-01T00:00:00Z",
            "mode": "value",
            "widget": "slider",
            "minDefValue": "2000-01-01T00:00:00Z",
            "maxDefValue": None,
        })

        layer = LayerV1()
        layer.id = 20
        layer.name = "test_wmstimegroup"
        layer.layer = "test_wmstimegroup"
        layer.layer_type = "internal WMS"
        layer.image_type = "image/png"
        layer.is_checked = False
        layer.legend = False
        layer.is_legend_expanded = False
        layer.public = True
        layer.time_mode = "value"
        layer.time_widget = "datepicker"
        time = TimeInformation()
        entry._layer(layer, time=time, mixed=False)
        self.assertEqual(time.to_dict(), {
            "resolution": "year",
            "interval": (1, 0, 0, 0),
            "maxValue": "2020-01-01T00:00:00Z",
            "minValue": "2000-01-01T00:00:00Z",
            "mode": "value",
            "widget": "datepicker",
            "minDefValue": "2000-01-01T00:00:00Z",
            "maxDefValue": None,
        })

        layer = LayerV1()
        layer.id = 20
        layer.name = "test WMTS"
        layer.layer = "test WMTS"
        layer.is_checked = False
        layer.layer_type = "WMTS"
        layer.url = "http://example.com/WMTS-Capabilities.xml"
        layer.wms_layers = "test_wmsfeatures"
        layer.legend = False
        layer.is_legend_expanded = False
        layer.public = True
        self.assertEqual(entry._layer(layer), ({
            "id": 20,
            "name": "test WMTS",
            "isChecked": False,
            "type": "WMTS",
            "url": "http://example.com/WMTS-Capabilities.xml",
            "wmsUrl": "/dummy/route/mapserverproxy",
            "wmsLayers": "test_wmsfeatures",
            "queryLayers": [{
                "name": "test_wmsfeatures",
                "minResolutionHint": 1.76,
                "maxResolutionHint": 8.8200000000000003
            }],
            "legend": False,
            "isLegendExpanded": False,
            "public": True,
            "metadata": {},
        }, set()))

        layer = LayerV1()
        layer.id = 20
        layer.name = "test WMTS"
        layer.layer = "test WMTS"
        layer.is_checked = False
        layer.layer_type = "WMTS"
        layer.url = "http://example.com/WMTS-Capabilities.xml"
        layer.wms_layers = "foo"
        layer.query_layers = "test_wmsfeatures"
        layer.legend = False
        layer.is_legend_expanded = False
        layer.public = True
        self.assertEqual(entry._layer(layer), ({
            "id": 20,
            "name": "test WMTS",
            "isChecked": False,
            "type": "WMTS",
            "url": "http://example.com/WMTS-Capabilities.xml",
            "wmsUrl": "/dummy/route/mapserverproxy",
            "wmsLayers": "foo",
            "queryLayers": [{
                "name": "test_wmsfeatures",
                "minResolutionHint": 1.76,
                "maxResolutionHint": 8.8200000000000003
            }],
            "legend": False,
            "isLegendExpanded": False,
            "public": True,
            "metadata": {},
        }, set()))

        group1 = LayerGroup()
        group1.name = "block"
        group1.id = 11
        group2 = LayerGroup()
        group2.id = 12
        group2.name = "node"
        group2.metadata_url = "http://example.com/group.metadata"
        layer = LayerV1()
        layer.id = 20
        layer.name = "test layer in group"
        layer.layer = "test layer in group"
        layer.is_checked = False
        layer.layer_type = "internal WMS"
        layer.image_type = "image/png"
        layer.legend = False
        layer.is_legend_expanded = False
        layer.public = True
        group1.children = [group2]
        group2.children = [layer]

        self.assertEqual(entry._group(
            "", group1, [layer.name],
        ), ({
            "id": 11,
            "isExpanded": False,
            "isInternalWMS": True,
            "name": "block",
            "isBaseLayer": False,
            "metadata": {},
            "mixed": False,
            "children": [{
                "id": 12,
                "isExpanded": False,
                "isInternalWMS": True,
                "name": "node",
                "isBaseLayer": False,
                "metadataURL": "http://example.com/group.metadata",
                "metadata": {},
                "mixed": False,
                "children": [{
                    "name": "test layer in group",
                    "id": 20,
                    "isChecked": False,
                    "type": "internal WMS",
                    "legend": False,
                    "isLegendExpanded": False,
                    "imageType": "image/png",
                    "public": True,
                    "metadata": {},
                }]
            }]
        }, set(["The layer 'test layer in group' (test layer in group) is not defined in WMS capabilities from '__test_ogc_server'"])))

    def _assert_has_error(self, errors, error):
        self.assertIn(error, errors)
        self.assertEquals(
            len([e for e in errors if e == error]), 1,
            "Error '{0!s}' more than one time in errors:\n{1!r}".format(error, errors),
        )

    def test_internalwms(self):
        from c2cgeoportal.views.entry import Entry
        from c2cgeoportal.models import LayerV1, LayerGroup

        request = self._create_request_obj()
        request.static_url = lambda name: "/dummy/static/" + name
        request.route_url = lambda name: "/dummy/route/" + name
        request.registry.settings["package"] = "test_layer"
        entry = Entry(request)

        group1 = LayerGroup()
        group1.is_internal_wms = True
        group2 = LayerGroup()
        group2.is_internal_wms = False
        group1.children = [group2]
        _, errors = entry._group("", group1, [], catalogue=False)
        self._assert_has_error(errors, "Group '' cannot be in group '' (internal/external mix).")

        group1 = LayerGroup()
        group1.is_internal_wms = False
        group2 = LayerGroup()
        group2.is_internal_wms = True
        group1.children = [group2]
        _, errors = entry._group("", group1, [], catalogue=False)
        self._assert_has_error(errors, "Group '' cannot be in group '' (internal/external mix).")

        group = LayerGroup()
        group.is_internal_wms = True
        layer = LayerV1()
        layer.layer_type = "internal WMS"
        group.children = [layer]
        _, errors = entry._group("", group, [layer.name], catalogue=False)
        self.assertEqual(errors, set([
            u"The layer '' () is not defined in WMS capabilities from '__test_ogc_server'",
        ]))

        group = LayerGroup()
        group.is_internal_wms = True
        layer = LayerV1()
        layer.layer_type = "external WMS"
        group.children = [layer]
        _, errors = entry._group("", group, [layer.name], catalogue=False)
        self._assert_has_error(errors, "Layer '' cannot be in the group '' (internal/external mix).")

        group = LayerGroup()
        group.is_internal_wms = True
        layer = LayerV1()
        layer.layer_type = "WMTS"
        group.children = [layer]
        _, errors = entry._group("", group, [layer.name], catalogue=False)
        self._assert_has_error(errors, "Layer '' cannot be in the group '' (internal/external mix).")

        group = LayerGroup()
        group.is_internal_wms = True
        layer = LayerV1()
        layer.layer_type = "no 2D"
        group.children = [layer]
        _, errors = entry._group("", group, [layer.name], catalogue=False)
        self._assert_has_error(errors, "Layer '' cannot be in the group '' (internal/external mix).")

        group = LayerGroup()
        group.is_internal_wms = False
        layer = LayerV1()
        layer.layer_type = "internal WMS"
        group.children = [layer]
        _, errors = entry._group("", group, [layer.name], catalogue=False)
        self._assert_has_error(errors, "Layer '' cannot be in the group '' (internal/external mix).")

        group = LayerGroup()
        group.is_internal_wms = False
        layer = LayerV1()
        layer.layer_type = "external WMS"
        group.children = [layer]
        _, errors = entry._group("", group, [layer.name], catalogue=False, min_levels=0)
        self.assertEqual(errors, set())

        group = LayerGroup()
        group.is_internal_wms = False
        layer = LayerV1()
        layer.layer_type = "WMTS"
        group.children = [layer]
        _, errors = entry._group("", group, [layer.name], catalogue=False, min_levels=0)
        self.assertEqual(errors, set())

        group = LayerGroup()
        group.is_internal_wms = False
        layer = LayerV1()
        layer.layer_type = "no 2D"
        group.children = [layer]
        _, errors = entry._group("", group, [layer.name], catalogue=False, min_levels=0)
        self.assertEqual(errors, set())

    def test_loginchange_no_params(self):
        from pyramid.httpexceptions import HTTPBadRequest
        from c2cgeoportal.views.entry import Entry

        request = self._create_request_obj(username=u"__test_user1", params={
            "lang": "en"
        }, POST={})
        entry = Entry(request)
        self.assertRaises(HTTPBadRequest, entry.loginchange)

    def test_loginchange_wrong_old(self):
        from pyramid.httpexceptions import HTTPBadRequest
        from c2cgeoportal.views.entry import Entry

        request = self._create_request_obj(username=u"__test_user1", params={
            "lang": "en"
        }, POST={
            "oldPassword": "",
            "newPassword": "1234",
            "confirmNewPassword": "12345",
        })
        entry = Entry(request)
        self.assertRaises(HTTPBadRequest, entry.loginchange)

    def test_loginchange_different(self):
        from pyramid.httpexceptions import HTTPBadRequest
        from c2cgeoportal.views.entry import Entry

        request = self._create_request_obj(username=u"__test_user1", params={
            "lang": "en"
        }, POST={
            "oldPassword": "__test_user1",
            "newPassword": "1234",
            "confirmNewPassword": "12345",
        })
        entry = Entry(request)
        self.assertRaises(HTTPBadRequest, entry.loginchange)

    def test_loginchange_good_is_password_changed(self):
        from c2cgeoportal.views.entry import Entry
        from hashlib import sha1

        request = self._create_request_obj(username=u"__test_user1", params={
            "lang": "en"
        }, POST={
            "oldPassword": "__test_user1",
            "newPassword": "1234",
            "confirmNewPassword": "1234"
        })
        self.assertEquals(request.user.is_password_changed, False)
        self.assertEquals(request.user._password, unicode(sha1("__test_user1").hexdigest()))
        entry = Entry(request)
        self.assertNotEqual(entry.loginchange(), None)
        self.assertEqual(request.user.is_password_changed, True)
        self.assertEqual(request.user._password, unicode(sha1("1234").hexdigest()))

    def test_json_extent(self):
        from c2cgeoportal.models import DBSession, Role

        role = DBSession.query(Role).filter(Role.name == "__test_role1").one()
        self.assertEqual(role.bounds, None)

        role = DBSession.query(Role).filter(Role.name == "__test_role2").one()
        self.assertEqual(role.bounds, (1, 2, 3, 4))
