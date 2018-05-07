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


from unittest import TestCase

import re
import transaction
import json
from geoalchemy2 import WKTElement
from pyramid import testing

from tests.functional import (  # noqa
    teardown_common as teardown_module,
    setup_common as setup_module,
    mapserv_url, create_dummy_request,
    create_default_ogcserver, cleanup_db
)

import logging
log = logging.getLogger(__name__)


class TestEntryView(TestCase):

    def setup_method(self, _):
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None
        self._tables = []

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import Role, LayerV1, \
            RestrictionArea, Theme, LayerGroup, Functionality, Interface, \
            LayerWMS, OGCServer, FullTextSearch, OGCSERVER_TYPE_GEOSERVER, OGCSERVER_AUTH_GEOSERVER
        from c2cgeoportal_commons.models.static import User
        from sqlalchemy import Column, Table, types, func
        from sqlalchemy.ext.declarative import declarative_base
        from geoalchemy2 import Geometry

        cleanup_db()

        role1 = Role(name="__test_role1")
        user1 = User(username="__test_user1", password="__test_user1", role=role1)
        user1.email = "__test_user1@example.com"

        role2 = Role(name="__test_role2", extent=WKTElement(
            "POLYGON((1 2, 1 4, 3 4, 3 2, 1 2))", srid=21781
        ))
        user2 = User(username="__test_user2", password="__test_user2", role=role2)

        main = Interface(name="desktop")
        mobile = Interface(name="mobile")

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

        public_layer = LayerV1(name="__test_public_layer", public=True)
        public_layer.is_checked = False
        public_layer.interfaces = [main, mobile]

        private_layer = LayerV1(name="__test_private_layer", public=False)
        private_layer.geo_table = "geodata.a_geo_table"
        private_layer.interfaces = [main, mobile]

        ogcserver, _ = create_default_ogcserver()
        ogcserver_normapfile = OGCServer(name="__test_ogc_server_notmapfile")
        ogcserver_normapfile.url = mapserv_url + "?map=not_a_mapfile"
        ogcserver_geoserver = OGCServer(name="__test_ogc_server_geoserver")
        ogcserver_geoserver.url = mapserv_url
        ogcserver_geoserver.type = OGCSERVER_TYPE_GEOSERVER
        ogcserver_geoserver.auth = OGCSERVER_AUTH_GEOSERVER

        private_layerv2 = LayerWMS(name="__test_private_layer", public=False)
        private_layerv2.layer = "__test_private_layer"
        private_layerv2.geo_table = "a_schema.a_geo_table"
        private_layerv2.interfaces = [main, mobile]
        private_layerv2.ogc_server = ogcserver

        public_layer2 = LayerWMS(
            name="__test_public_layer2", layer="__test_public_layer_bis", public=True)
        public_layer2.interfaces = [main, mobile]
        public_layer2.ogc_server = ogcserver

        private_layer2 = LayerWMS(
            name="__test_private_layer2", layer="__test_private_layer_bis", public=False)
        private_layer2.interfaces = [main, mobile]
        private_layer2.ogc_server = ogcserver

        public_layer_not_mapfile = LayerWMS(
            name="__test_public_layer_not_mapfile", layer="__test_public_layer_not_in_mapfile", public=True)
        public_layer_not_mapfile.interfaces = [main, mobile]
        public_layer_not_mapfile.ogc_server = ogcserver

        public_layer_no_layers = LayerWMS(
            name="__test_public_layer_no_layers", public=True)
        public_layer_no_layers.interfaces = [main, mobile]
        public_layer_no_layers.ogc_server = ogcserver

        layer_in_group = LayerV1(name="__test_layer_in_group")
        layer_in_group.interfaces = [main, mobile]
        layer_group = LayerGroup(name="__test_layer_group_1")
        layer_group.children = [layer_in_group]

        layer_wmsgroup = LayerV1(name="test_wmsfeaturesgroup")
        layer_wmsgroup.is_checked = False
        layer_wmsgroup.interfaces = [main, mobile]

        group = LayerGroup(name="__test_layer_group_2")
        group.children = [
            public_layer, private_layer, private_layerv2, layer_group, layer_wmsgroup,
            public_layer2, public_layer_not_mapfile, public_layer_no_layers,
            private_layer2
        ]
        theme = Theme(name="__test_theme")
        theme.children = [group]
        theme.interfaces = [main]

        functionality1 = Functionality(name="test_name", value="test_value_1")
        functionality2 = Functionality(name="test_name", value="test_value_2")
        theme.functionalities = [functionality1, functionality2]

        poly = "POLYGON((-100 0, -100 20, 100 20, 100 0, -100 0))"

        area = WKTElement(poly, srid=21781)
        RestrictionArea(
            name="__test_ra1", description="", layers=[private_layer, private_layerv2, private_layer2],
            roles=[role1], area=area
        )

        area = WKTElement(poly, srid=21781)
        RestrictionArea(
            name="__test_ra2", description="", layers=[private_layer, private_layerv2, private_layer2],
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
            public_layer, private_layer, private_layerv2, public_layer2, private_layer2,
            entry1, entry2, entry3,
        ])

        DBSession.flush()

        self.role1_id = role1.id

        transaction.commit()

    def teardown_method(self, _):
        testing.tearDown()

        cleanup_db()

    #
    # login/logout tests
    #

    def test_login(self):
        from pyramid.httpexceptions import HTTPBadRequest
        from c2cgeoportal_geoportal.views.entry import Entry

        request = self._create_request_obj(params={
            "came_from": "/came_from",
        }, POST={
            "login": "__test_user1",
            "password": "__test_user1",
        })
        response = Entry(request).login()
        self.assertEqual(response.status_int, 302)
        self.assertEqual(response.headers["Location"], "/came_from")

        request = self._create_request_obj(POST={
            "login": "__test_user1",
            "password": "__test_user1",
        })
        response = Entry(request).login()
        self.assertEqual(response.status_int, 200)
        self.assertEqual(json.loads(response.body.decode("utf-8")), {
            "success": True,
            "username": "__test_user1",
            "is_password_changed": False,
            "role_name": "__test_role1",
            "role_id": self.role1_id,
            "functionalities": {},
        })

        request = self._create_request_obj(POST={
            "login": "__test_user1",
            "password": "bad password",
        })
        entry = Entry(request)
        self.assertRaises(HTTPBadRequest, entry.login)

    def test_logout_no_auth(self):
        from pyramid.httpexceptions import HTTPBadRequest
        from c2cgeoportal_geoportal.views.entry import Entry

        request = self._create_request_obj(path="/", params={
            "came_from": "/came_from"
        })
        entry = Entry(request)
        self.assertRaises(HTTPBadRequest, entry.logout)

    def test_logout(self):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User
        from c2cgeoportal_geoportal.views.entry import Entry

        request = self._create_request_obj(path="/")
        request.user = DBSession.query(User).filter_by(
            username="__test_user1"
        ).one()
        response = Entry(request).logout()
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.body.decode("utf-8"), "true")

        request = self._create_request_obj(path="/")
        request.route_url = lambda url: "/dummy/route/url"
        request.user = DBSession.query(User).filter_by(
            username="__test_user1"
        ).one()
        response = Entry(request).logout()
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.body.decode("utf-8"), "true")

    def test_reset_password(self):
        from c2cgeoportal_geoportal.views.entry import Entry

        request = self._create_request_obj(POST={
            "login": "__test_user1",
        })
        entry = Entry(request)
        _, username, password, _ = entry._loginresetpassword()

        request = self._create_request_obj(POST={
            "login": username,
            "password": password,
        })
        response = Entry(request).login()
        self.assertEqual(response.status_int, 200)
        self.assertEqual(json.loads(response.body.decode("utf-8")), {
            "success": True,
            "username": "__test_user1",
            "is_password_changed": True,
            "role_name": "__test_role1",
            "role_id": self.role1_id,
            "functionalities": {},
        })

    #
    # viewer view tests
    #

    @staticmethod
    def _create_request_obj(username=None, params=None, **kwargs):
        if params is None:
            params = {}
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User

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
        from c2cgeoportal_geoportal.views.entry import Entry

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
        entry = self._create_entry_obj(username="__test_user1")
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
        entry = self._create_entry_obj(username="__test_user2", params={
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
        self.assertEqual(
            {layer["name"] for layer in layers},
            {"__test_public_layer", "__test_private_layer", "test_wmsfeaturesgroup", "__test_layer_group_1"}
        )

        self.assertEqual([
            "editable" in layer
            for layer in layers
            if layer["name"] == "test_wmsfeaturesgroup"
        ], [False])

        self.assertEqual([
            "editable" in layer
            for layer in layers
            if layer["name"] == "__test_private_layer"
        ], [True])

        self.assertEqual([
            "editable" in layer
            for layer in layers
            if layer["name"] == "__test_public_layer"
        ], [False])

    def test_theme(self):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User
        from c2cgeoportal_geoportal.views.entry import Entry
        request = self._create_request_obj()
        entry = Entry(request)

        # unautenticated
        themes, errors = entry._themes(None, "desktop")
        self.assertEqual(errors, {
            "The layer '__test_layer_in_group' (__test_layer_in_group) is not defined in WMS capabilities from '__test_ogc_server'",
        })
        self.assertEqual(len(themes), 1)
        layers = {l["name"] for l in themes[0]["children"][0]["children"]}
        self.assertEqual(layers, {
            "test_wmsfeaturesgroup",
            "__test_layer_group_1",
            "__test_public_layer",
        })

        # authenticated on parent
        request.params = {
            "role_id": DBSession.query(User).filter_by(username="__test_user1").one().role.id
        }
        request.client_addr = "127.0.0.1"
        themes = entry.themes()
        self.assertEqual(len(themes), 1)
        layers = [l["name"] for l in themes[0]["children"][0]["children"]]
        self.assertTrue("__test_public_layer" in layers)
        self.assertTrue("__test_private_layer" in layers)

        # authenticated
        request.params = {}
        request.user = DBSession.query(User).filter_by(username="__test_user1").one()
        themes, errors = entry._themes(request.user.role.id)
        self.assertEqual(errors, {
            "The layer '__test_layer_in_group' (__test_layer_in_group) is not defined in WMS capabilities from '__test_ogc_server'",
        })
        self.assertEqual(len(themes), 1)
        layers = {l["name"] for l in themes[0]["children"][0]["children"]}
        self.assertEqual(layers, {
            "test_wmsfeaturesgroup",
            "__test_layer_group_1",
            "__test_public_layer",
            "__test_private_layer",
        })

    def test_notmapfile(self):
        # mapfile error
        from c2cgeoportal_geoportal.views.entry import Entry
        request = self._create_request_obj(additional_settings={
            "mapserverproxy": {
                "default_ogc_server": "__test_ogc_server_notmapfile",
            }
        })
        entry = Entry(request)
        request.params = {}

        from c2cgeoportal_geoportal.lib import caching
        caching.invalidate_region()
        _, errors = entry._themes(None, "desktop")
        self.assertEqual({e[:43] for e in errors}, {
            "The layer '__test_public_layer' (__test_pub",
            "The layer '__test_layer_in_group' (__test_l",
            "The layer 'test_wmsfeaturesgroup' (test_wms",
            "GetCapabilities from URL http://mapserver/?"
        })

    def test_themev2(self):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User
        from c2cgeoportal_geoportal.views.entry import Entry
        request = self._create_request_obj()
        entry = Entry(request)

        # unautenticated
        request.params = {
            "version": "2"
        }
        themes = entry.themes()
        self.assertEqual(len(themes["themes"]), 1)
        layers = {l["name"] for l in themes["themes"][0]["children"][0]["children"]}
        self.assertEqual(layers, {
            "__test_public_layer2",
            "__test_public_layer_not_mapfile",
        })

        self.assertEqual(set(themes["errors"]), {
            "The layer '__test_public_layer_not_in_mapfile' (__test_public_layer_not_mapfile) is not defined in WMS capabilities from '__test_ogc_server'",
            "The layer '__test_public_layer_no_layers' do not have any layers",
        })

        # authenticated
        request.params = {
            "version": "2"
        }
        request.user = DBSession.query(User).filter_by(username="__test_user1").one()
        themes = entry.themes()
        self.assertEqual(len(themes["themes"]), 1)
        layers = {l["name"] for l in themes["themes"][0]["children"][0]["children"]}
        self.assertEqual(layers, {
            "__test_public_layer2",
            "__test_private_layer",
            "__test_private_layer2",
            "__test_public_layer_not_mapfile",
        })
        self.assertEqual(set(themes["errors"]), {
            "The layer '__test_public_layer_not_in_mapfile' (__test_public_layer_not_mapfile) is not defined in WMS capabilities from '__test_ogc_server'",
            "The layer '__test_public_layer_no_layers' do not have any layers",
        })

    def test_theme_geoserver(self):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User
        from c2cgeoportal_geoportal.views.entry import Entry
        request = self._create_request_obj(additional_settings={
            "mapserverproxy": {
                "default_ogc_server": "__test_ogc_server_geoserver",
            }
        })
        entry = Entry(request)

        # unautenticated v1
        themes, errors = entry._themes(None, "desktop")
        self.assertEqual(errors, set())
        self.assertEqual(len(themes), 1)
        layers = {l["name"] for l in themes[0]["children"][0]["children"]}
        self.assertEqual(layers, {
            "test_wmsfeaturesgroup",
            "__test_public_layer",
            "__test_layer_group_1",
        })

        # authenticated v1
        request.params = {}
        request.user = DBSession.query(User).filter_by(username="__test_user1").one()
        themes, errors = entry._themes(request.user.role.id)
        self.assertEqual(errors, set())
        self.assertEqual(len(themes), 1)
        layers = {l["name"] for l in themes[0]["children"][0]["children"]}
        self.assertEqual(layers, {
            "test_wmsfeaturesgroup",
            "__test_public_layer",
            "__test_private_layer",
            "__test_layer_group_1",
        })

        # do not test anything related to geoserver ...
        # unautenticated v2
        request.params = {
            "version": "2"
        }
        request.user = None
        themes = entry.themes()
        self.assertEqual(set(themes["errors"]), {
            "The layer '__test_public_layer_not_in_mapfile' (__test_public_layer_not_mapfile) is not defined in WMS capabilities from '__test_ogc_server'",
            "The layer '__test_public_layer_no_layers' do not have any layers",
        })
        self.assertEqual(len(themes["themes"]), 1)
        layers = {l["name"] for l in themes["themes"][0]["children"][0]["children"]}
        self.assertEqual(layers, {
            "__test_public_layer2",
            "__test_public_layer_not_mapfile",
        })

        # authenticated v2
        request.params = {
            "version": "2"
        }
        request.user = DBSession.query(User).filter_by(username="__test_user1").one()
        themes = entry.themes()
        self.assertEqual(set(themes["errors"]), {
            "The layer '__test_public_layer_not_in_mapfile' (__test_public_layer_not_mapfile) is not defined in WMS capabilities from '__test_ogc_server'",
            "The layer '__test_public_layer_no_layers' do not have any layers",
        })
        self.assertEqual(len(themes["themes"]), 1)
        layers = {l["name"] for l in themes["themes"][0]["children"][0]["children"]}
        self.assertEqual(layers, {
            "__test_public_layer2",
            "__test_private_layer",
            "__test_private_layer2",
            "__test_public_layer_not_mapfile",
        })

    def test_wfs_types(self):
        from c2cgeoportal_geoportal.views.entry import Entry

        request = self._create_request_obj()
        entry = Entry(request)

        response = entry.get_cgxp_viewer_vars()
        self.assertEqual(
            self._get_filtered_errors(json.loads(response["serverError"])),
            set()
        )

        result = {
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
            "__test_private_layer0",
            "__test_private_layer1",
            "__test_private_layer2",
            "__test_private_layer3",
            "__test_private_layer4",
            "__test_private_layer5",
            "__test_private_layer6",
            "__test_private_layer7",
            "__test_private_layer8",
            "__test_private_layer9",
        }

        self.assertEqual(set(json.loads(response["WFSTypes"])), result)
        self.assertEqual(set(json.loads(response["externalWFSTypes"])), result)

    def test_permalink_themes(self):
        from c2cgeoportal_geoportal.views.entry import Entry
        request = self._create_request_obj()
        request.params = {
            "permalink_themes": "my_themes",
        }
        entry = Entry(request)

        response = entry.get_cgxp_viewer_vars()
        self.assertEqual(response["permalink_themes"], '["my_themes"]')

    def _create_entry(self):
        from c2cgeoportal_geoportal.views.entry import Entry

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
        entry, _ = self._create_entry()

        result = entry.get_cgxp_index_vars()
        self.assertEqual(
            set(result.keys()),
            {"lang", "debug", "extra_params"}
        )
        result = entry.get_cgxp_viewer_vars()
        self.assertEqual(set(result.keys()), {
            "lang", "tiles_url", "debug",
            "serverError", "themes", "functionality",
            "WFSTypes", "externalWFSTypes", "user", "queryer_attribute_urls",
            "version_role_params", "version_params",
        })
        self.assertEqual(
            result["queryer_attribute_urls"],
            '{{"layer_test": {{"label": "{0!s}"}}}}'.format(mapserv_url)
        )

        result = entry.get_ngeo_index_vars()
        self.assertEqual(set(result.keys()), {
            "debug", "fulltextsearch_groups", "wfs_types"
        })
        result = entry.get_ngeo_permalinktheme_vars()
        self.assertEqual(set(result.keys()), {
            "debug", "fulltextsearch_groups", "permalink_themes", "wfs_types"
        })

        result = entry.apijs()
        self.assertEqual(
            set(result.keys()),
            {"lang", "debug", "queryable_layers", "tiles_url", "url_params"}
        )
        result = entry.xapijs()
        self.assertEqual(
            set(result.keys()),
            {"lang", "debug", "queryable_layers", "tiles_url", "url_params"}
        )
        result = entry.apihelp()
        self.assertEqual(set(result.keys()), {"lang", "debug"})
        result = entry.xapihelp()
        self.assertEqual(set(result.keys()), {"lang", "debug"})

    def test_ngeo_vars(self):
        entry, _ = self._create_entry()
        result = entry.get_ngeo_index_vars()
        self.assertEqual(
            set(result["fulltextsearch_groups"]),
            {"layer1"},
        )

    def test_auth_home(self):
        from c2cgeoportal_geoportal.views.entry import Entry
        from c2cgeoportal_commons.models.main import Role
        from c2cgeoportal_commons.models.static import User

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
        self.assertEqual(
            set(result.keys()),
            {"lang", "debug", "extra_params"}
        )
        self.assertEqual(
            set(result["extra_params"].keys()),
            {"lang"}
        )
        self.assertEqual(result["extra_params"]["lang"], "fr")

    def test_entry_points_version(self):
        from c2cgeoportal_geoportal.views.entry import Entry

        request = testing.DummyRequest()
        request.user = None

        request.static_url = lambda url: "http://example.com/dummy/static/url"
        request.route_url = lambda url, **kwargs: mapserv_url
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
        self.assertEqual(
            set(result.keys()),
            {"lang", "debug", "extra_params"}
        )

    def test_entry_points_wfs(self):
        from c2cgeoportal_geoportal.views.entry import Entry
        from c2cgeoportal_commons.models.main import Role
        from c2cgeoportal_commons.models.static import User

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
        self.assertEqual(
            set(result.keys()),
            {"lang", "debug", "extra_params"}
        )
        self.assertEqual(
            set(result["extra_params"].keys()),
            {"lang"},
        )
        self.assertEqual(result["extra_params"]["lang"], "fr")

    def test_entry_points_wfs_url(self):
        from c2cgeoportal_geoportal.views.entry import Entry

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
        self.assertEqual(
            set(result.keys()),
            {"lang", "debug", "extra_params"}
        )
        result = entry.get_cgxp_viewer_vars()

    def test_entry_points_noexternal(self):
        from c2cgeoportal_geoportal.views.entry import Entry

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
        self.assertEqual(
            set(result.keys()),
            {"lang", "debug", "extra_params"}
        )
        result = entry.get_cgxp_viewer_vars()

    def test_permalink_theme(self):
        from c2cgeoportal_geoportal.views.entry import Entry
        request = self._create_request_obj()
        entry = Entry(request)

        request.matchdict = {
            "themes": ["theme"],
        }
        result = entry.get_cgxp_permalinktheme_vars()
        self.assertEqual(
            set(result.keys()),
            {"lang", "permalink_themes", "debug", "extra_params"}
        )
        self.assertEqual(
            set(result["extra_params"].keys()),
            {"lang", "permalink_themes"}
        )
        self.assertEqual(result["extra_params"]["lang"], "fr")
        self.assertEqual(result["extra_params"]["permalink_themes"], ["theme"])
        self.assertEqual(result["permalink_themes"], ["theme"])

        request.matchdict = {
            "themes": ["theme1", "theme2"],
        }
        result = entry.get_cgxp_permalinktheme_vars()
        self.assertEqual(
            set(result.keys()),
            {"lang", "permalink_themes", "debug", "extra_params"}
        )
        self.assertEqual(
            set(result["extra_params"].keys()),
            {"lang", "permalink_themes"}
        )
        self.assertEqual(result["extra_params"]["lang"], "fr")
        self.assertEqual(result["extra_params"]["permalink_themes"], ["theme1", "theme2"])
        self.assertEqual(result["permalink_themes"], ["theme1", "theme2"])

    def test_layer(self):
        import httplib2
        from c2cgeoportal_geoportal.views.entry import Entry
        from c2cgeoportal_commons.models.main import LayerV1, LayerGroup
        from c2cgeoportal_geoportal.lib.wmstparsing import TimeInformation

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

        layer_info, errors = entry._layer(layer)
        # pylint: disable=unsupported-assignment-operation
        layer_info["icon"] = None
        self.assertEqual(layer_info, {
            "id": 20,
            "name": "test internal WMS",
            "metadataURL": "http://example.com/tiwms",
            "isChecked": True,
            "icon": None,
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
        })
        self.assertEqual(errors, {
            "The layer 'test internal WMS' (test internal WMS) is not defined in WMS capabilities from '__test_ogc_server'"
        })

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
            "dimensions": {"DATE": "1012"},
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
            "name": "test no 2D",
            "isChecked": False,
            "type": "no 2D",
            "legend": False,
            "isLegendExpanded": False,
            "metadataURL": "http://example.com/wmsfeatures.metadata",
            "public": True,
            "metadata": {},
        }, set()))

        params = (
            ("SERVICE", "WMS"),
            ("VERSION", "1.1.1"),
            ("REQUEST", "GetCapabilities"),
        )
        url = mapserv_url + "?" + "&".join(["=".join(p) for p in params])
        http = httplib2.Http()
        http.request(url, method="GET")

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
            "name": "test_wmsfeaturesgroup",
            "type": "internal WMS",
            "isChecked": False,
            "legend": False,
            "isLegendExpanded": False,
            "imageType": "image/png",
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
                "name": "test_wmsfeatures",
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
        }, {"The layer 'test layer in group' (test layer in group) is not defined in WMS capabilities from '__test_ogc_server'"}))

    def _assert_has_error(self, errors, error):
        self.assertIn(error, errors)
        self.assertEqual(
            len([e for e in errors if e == error]), 1,
            "Error '{0!s}' more than one time in errors:\n{1!r}".format(error, errors),
        )

    def test_internalwms(self):
        from c2cgeoportal_geoportal.views.entry import Entry
        from c2cgeoportal_commons.models.main import LayerV1, LayerGroup

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
        self.assertEqual(errors, {
            "The layer '' () is not defined in WMS capabilities from '__test_ogc_server'",
        })

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
        from c2cgeoportal_geoportal.views.entry import Entry

        request = self._create_request_obj(username="__test_user1", params={
            "lang": "en"
        }, POST={})
        entry = Entry(request)
        self.assertRaises(HTTPBadRequest, entry.loginchange)

    def test_loginchange_wrong_old(self):
        from pyramid.httpexceptions import HTTPBadRequest
        from c2cgeoportal_geoportal.views.entry import Entry

        request = self._create_request_obj(username="__test_user1", params={
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
        from c2cgeoportal_geoportal.views.entry import Entry

        request = self._create_request_obj(username="__test_user1", params={
            "lang": "en"
        }, POST={
            "oldPassword": "__test_user1",
            "newPassword": "1234",
            "confirmNewPassword": "12345",
        })
        entry = Entry(request)
        self.assertRaises(HTTPBadRequest, entry.loginchange)

    def test_loginchange_good_is_password_changed(self):
        from c2cgeoportal_geoportal.views.entry import Entry
        from hashlib import sha1

        request = self._create_request_obj(username="__test_user1", params={
            "lang": "en"
        }, POST={
            "oldPassword": "__test_user1",
            "newPassword": "1234",
            "confirmNewPassword": "1234"
        })
        self.assertEqual(request.user.is_password_changed, False)
        self.assertEqual(request.user._password, str(sha1("__test_user1".encode("utf-8")).hexdigest()))
        entry = Entry(request)
        self.assertNotEqual(entry.loginchange(), None)
        self.assertEqual(request.user.is_password_changed, True)
        self.assertEqual(request.user._password, str(sha1("1234".encode("utf-8")).hexdigest()))

    def test_json_extent(self):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import Role

        role = DBSession.query(Role).filter(Role.name == "__test_role1").one()
        self.assertEqual(role.bounds, None)

        role = DBSession.query(Role).filter(Role.name == "__test_role2").one()
        self.assertEqual(role.bounds, (1, 2, 3, 4))
