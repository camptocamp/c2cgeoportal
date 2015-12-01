# -*- coding: utf-8 -*-

# Copyright (c) 2013-2014, Camptocamp SA
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

import transaction
import os
import json
import urllib
from geoalchemy2 import WKTElement
from pyramid import testing
from owslib.wms import WebMapService

from c2cgeoportal.tests.functional import (  # noqa
    tear_down_common as tearDownModule,
    set_up_common as setUpModule,
    mapserv_url, host, create_dummy_request)

import logging
log = logging.getLogger(__name__)


@attr(functional=True)
class TestEntryView(TestCase):

    def setUp(self):  # noqa
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None

        from c2cgeoportal.models import DBSession, User, Role, LayerV1, \
            RestrictionArea, Theme, LayerGroup, Functionality, Interface, \
            LayerInternalWMS

        role1 = Role(name=u"__test_role1")
        user1 = User(username=u"__test_user1", password=u"__test_user1", role=role1)
        user1.email = "__test_user1@example.com"

        role2 = Role(name=u"__test_role2", extent=WKTElement(
            "POLYGON((1 2, 1 4, 3 4, 3 2, 1 2))", srid=21781
        ))
        user2 = User(username=u"__test_user2", password=u"__test_user2", role=role2)

        main = Interface(name=u"main")
        mobile = Interface(name=u"mobile")

        public_layer = LayerV1(name=u"__test_public_layer", public=True)
        public_layer.is_checked = False
        public_layer.interfaces = [main, mobile]

        private_layer = LayerV1(name=u"__test_private_layer", public=False)
        private_layer.geo_table = "a_schema.a_geo_table"
        private_layer.interfaces = [main, mobile]

        public_layer2 = LayerInternalWMS(
            name=u"__test_public_layer2", layer=u"__test_public_layer_bis", public=True)
        public_layer2.interfaces = [main, mobile]

        private_layer2 = LayerInternalWMS(
            name=u"__test_private_layer2", layer=u"__test_private_layer_bis", public=False)
        private_layer2.interfaces = [main, mobile]

        public_layer_not_mapfile = LayerInternalWMS(
            name=u"__test_public_layer_not_mapfile", layer=u"__test_public_layer_not_in_mapfile", public=True)
        public_layer_not_mapfile.interfaces = [main, mobile]

        layer_in_group = LayerV1(name=u"__test_layer_in_group")
        layer_in_group.interfaces = [main, mobile]
        layer_group = LayerGroup(name=u"__test_layer_group")
        layer_group.children = [layer_in_group]

        layer_wmsgroup = LayerV1(name=u"test_wmsfeaturesgroup")
        layer_wmsgroup.is_checked = False
        layer_wmsgroup.interfaces = [main, mobile]

        group = LayerGroup(name=u"__test_layer_group")
        group.children = [
            public_layer, private_layer, layer_group, layer_wmsgroup,
            public_layer2, public_layer_not_mapfile, private_layer2
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

        DBSession.add_all([
            user1, user2, public_layer, private_layer, public_layer2, private_layer2
        ])

        transaction.commit()

    def tearDown(self):  # noqa
        testing.tearDown()

        from c2cgeoportal.models import DBSession, User, Role, Layer, \
            RestrictionArea, Theme, LayerGroup, Interface

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
        for layergroup in DBSession.query(LayerGroup).all():
            DBSession.delete(layergroup)
        for layer in DBSession.query(Layer).all():
            DBSession.delete(layer)
        DBSession.query(Interface).filter(
            Interface.name == "main"
        ).delete()

        transaction.commit()

    #
    # login/logout tests
    #

    def test_login(self):
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
        self.assertEquals(response.body, "true")

        request = self._create_request_obj(POST={
            "login": u"__test_user1",
            "password": u"bad password",
        })
        response = Entry(request).login()
        self.assertEquals(response.status_int, 401)

    def test_logout_no_auth(self):
        from c2cgeoportal.views.entry import Entry

        request = self._create_request_obj(path="/", params={
            "came_from": "/came_from"
        })
        entry = Entry(request)
        response = entry.logout()
        self.assertEquals(response.status_int, 404)

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
        user, username, password = entry._loginresetpassword()

        request = self._create_request_obj(POST={
            "login": username,
            "password": password,
        })
        response = Entry(request).login()
        self.assertEquals(response.status_int, 200)
        self.assertEquals(response.body, "true")

    #
    # viewer view tests
    #

    def _create_request_obj(self, username=None, params={}, **kwargs):
        from c2cgeoportal.models import DBSession, User

        request = create_dummy_request(**kwargs)
        request.static_url = lambda url: "/dummy/static/url"
        request.route_url = lambda url, **kwargs: \
            request.registry.settings["mapserverproxy"]["mapserv_url"]
        request.interface_name = "main"
        request.params = params

        if username is not None:
            request.user = DBSession.query(User) \
                .filter_by(username=username).one()

        return request

    def _create_entry_obj(self, **kwargs):
        from c2cgeoportal.views.entry import Entry

        return Entry(self._create_request_obj(**kwargs))

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
            set(json.loads(response["serverError"])),
            set([
                u"The layer '__test_layer_in_group' is not defined in WMS capabilities",
            ])
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

    def test_mobileconfig_no_auth_no_theme(self):
        entry = self._create_entry_obj()
        response = entry.mobileconfig()

        self.assertEqual(response["themes"], [])

    def test_mobileconfig_no_auth_theme(self):
        entry = self._create_entry_obj(params={"theme": u"__test_theme"})
        entry.request.interface_name = "mobile"
        response = entry.mobileconfig()

        self.assertEqual(
            [t["name"] for t in response["themes"]],
            ["__test_theme"]
        )
        theme = response["themes"][0]
        self.assertEqual(
            set([l["name"] for l in theme["allLayers"]]),
            set([u"__test_layer_in_group", u"__test_public_layer", u"test_wmsfeaturesgroup"])
        )

        self.assertEqual(theme["layers"], ["__test_layer_in_group"])

        info = response["info"]
        self.assertEqual(
            info,
            {"username": ""}
        )

    def test_mobileconfig_no_auth_default_theme(self):
        entry = self._create_entry_obj()
        entry.request.interface_name = "mobile"
        entry.request.registry.settings["functionalities"] = {
            "anonymous": {
                "mobile_default_theme": u"__test_theme"
            }
        }
        response = entry.mobileconfig()

        theme = response["themes"][0]
        layers = theme["allLayers"]
        self.assertEqual(len(layers), 3)

    def test_mobileconfig_wmsgroup(self):
        entry = self._create_entry_obj(params={"theme": u"__test_theme"})
        entry.request.interface_name = "mobile"
        response = entry.mobileconfig()

        theme = response["themes"][0]
        layers = theme["allLayers"]
        self.assertEqual(
            layers,
            [{
                "name": u"test_wmsfeaturesgroup",
                "minResolutionHint": 1.76,
                "maxResolutionHint": 8.82,
                "childLayers": [{
                    "name": "test_wmsfeatures",
                    "minResolutionHint": 1.76,
                    "maxResolutionHint": 8.82,
                }]
            }, {
                "name": u"__test_layer_in_group"
            }, {
                "name": u"__test_public_layer"
            }]
        )

    def test_mobileconfig_auth_theme(self):
        entry = self._create_entry_obj(
            params={"theme": u"__test_theme"}, username=u"__test_user1"
        )
        entry.request.interface_name = "mobile"
        response = entry.mobileconfig()

        theme = response["themes"][0]
        layers = theme["allLayers"]

        self.assertEqual(set([
            layer["name"] for layer in layers
        ]), set([
            u"__test_layer_in_group", u"__test_public_layer",
            u"__test_private_layer", u"test_wmsfeaturesgroup"
        ]))

        self.assertEqual(
            set(theme["layers"]),
            set([u"__test_layer_in_group", u"__test_private_layer"])

        )
        info = response["info"]
        self.assertEqual(
            info,
            {"username": "__test_user1"}
        )

    def test_theme(self):
        from c2cgeoportal.models import DBSession, User
        from c2cgeoportal.views.entry import Entry
        request = self._create_request_obj()
        entry = Entry(request)

        # unautenticated
        themes, errors = entry._themes(None, "main")
        self.assertEquals(len(themes), 1)
        layers = set([l["name"] for l in themes[0]["children"][0]["children"]])
        self.assertEquals(layers, set([
            u"test_wmsfeaturesgroup",
            u"__test_layer_group",
            u"__test_public_layer",
        ]))
        self.assertEquals(errors, set([
            u"The layer '__test_layer_in_group' is not defined in WMS capabilities",
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
        self.assertEquals(len(themes), 1)
        layers = set([l["name"] for l in themes[0]["children"][0]["children"]])
        self.assertEquals(layers, set([
            u"test_wmsfeaturesgroup",
            u"__test_layer_group",
            u"__test_public_layer",
            u"__test_private_layer",
        ]))
        self.assertEquals(errors, set([
            u"The layer '__test_layer_in_group' is not defined in WMS capabilities",
        ]))

        # mapfile error
        request.params = {}
        request.registry.settings["mapserverproxy"]["mapserv_url"] = mapserv_url + "?map=not_a_mapfile"
        from c2cgeoportal import caching
        caching.invalidate_region()
        themes, errors = entry._themes(None, "main")
        self.assertEquals(errors, set([
            u"The layer '__test_public_layer' is not defined in WMS capabilities",
            u"The layer '__test_layer_in_group' is not defined in WMS capabilities",
            u"The layer 'test_wmsfeaturesgroup' is not defined in WMS capabilities",
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
        layers = set([l["name"] for l in themes["themes"][0]["children"][0]["children"]])
        self.assertEquals(layers, set([
            u"__test_public_layer_not_mapfile",
            u"__test_public_layer2",
        ]))
        self.assertEquals(set(themes["errors"]), set([
            u"The layer '__test_public_layer_not_in_mapfile' is not defined in WMS capabilities",
        ]))

        # autenticated
        request.params = {
            "version": "2"
        }
        request.user = DBSession.query(User).filter_by(username=u"__test_user1").one()
        themes = entry.themes()
        self.assertEquals(len(themes["themes"]), 1)
        layers = set([l["name"] for l in themes["themes"][0]["children"][0]["children"]])
        self.assertEquals(layers, set([
            u"__test_public_layer_not_mapfile",
            u"__test_public_layer2",
            u"__test_private_layer2",
        ]))
        self.assertEquals(set(themes["errors"]), set([
            u"The layer '__test_public_layer_not_in_mapfile' is not defined in WMS capabilities",
        ]))

    def test_theme_geoserver(self):
        from c2cgeoportal.models import DBSession, User
        from c2cgeoportal.views.entry import Entry
        request = self._create_request_obj()
        request.registry.settings["mapserverproxy"]["geoserver"] = True
        entry = Entry(request)

        # unautenticated v1
        themes, errors = entry._themes(None, "main")
        self.assertEquals(len(themes), 1)
        layers = set([l["name"] for l in themes[0]["children"][0]["children"]])
        self.assertEquals(layers, set([
            u"test_wmsfeaturesgroup",
            u"__test_public_layer",
        ]))
        self.assertEquals(errors, set([]))

        # autenticated v1
        request.params = {}
        request.user = DBSession.query(User).filter_by(username=u"__test_user1").one()
        themes, errors = entry._themes(request.user.role.id)
        self.assertEquals(len(themes), 1)
        layers = set([l["name"] for l in themes[0]["children"][0]["children"]])
        self.assertEquals(layers, set([
            u"test_wmsfeaturesgroup",
            u"__test_public_layer",
            u"__test_private_layer",
        ]))
        self.assertEquals(errors, set([]))

        # unautenticated v2
        request.params = {
            "version": "2"
        }
        request.user = None
        themes = entry.themes()
        self.assertEquals(len(themes["themes"]), 1)
        layers = set([l["name"] for l in themes["themes"][0]["children"][0]["children"]])
        self.assertEquals(layers, set([
            u"__test_public_layer2",
        ]))
        self.assertEquals(themes["errors"], [])

        # autenticated v2
        request.params = {
            "version": "2"
        }
        request.user = DBSession.query(User).filter_by(username=u"__test_user1").one()
        themes = entry.themes()
        self.assertEquals(len(themes["themes"]), 1)
        layers = set([l["name"] for l in themes["themes"][0]["children"][0]["children"]])
        self.assertEquals(layers, set([
            u"__test_public_layer2",
            u"__test_private_layer2",
        ]))
        self.assertEquals(themes["errors"], [])

    def test_wfs_types(self):
        from c2cgeoportal.views.entry import Entry

        request = self._create_request_obj()
        request.registry.settings["mapserverproxy"].update({
            "external_mapserv_url": request.registry.settings["mapserverproxy"]["mapserv_url"],
        })
        entry = Entry(request)

        response = entry.get_cgxp_viewer_vars()
        self.assertEquals(
            set(json.loads(response["serverError"])),
            set([
                u"The layer '__test_layer_in_group' is not defined in WMS capabilities",
            ])
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
        ])
        self.assertEquals(set(json.loads(response["WFSTypes"])), result)
        self.assertEquals(set(json.loads(response["externalWFSTypes"])), result)

    def test_permalink_themes(self):
        from c2cgeoportal.views.entry import Entry
        request = self._create_request_obj()
        request.registry.settings["mapserverproxy"]["external_mapserv_url"] = \
            request.registry.settings["mapserverproxy"]["mapserv_url"]
        request.params = {
            "permalink_themes": "my_themes",
        }
        entry = Entry(request)

        response = entry.get_cgxp_viewer_vars()
        self.assertEquals(response["permalink_themes"], '["my_themes"]')

    def test_mobile_cache_version(self):
        from c2cgeoportal.views.entry import Entry

        request = self._create_request_obj()
        request.user = None
        entry = Entry(request)
        request.current_route_url = lambda **kwargs: "http://example.com/current/view"
        result = entry.mobile()
        self.assertRegexpMatches(result["url_params"], "cache_version=[0-9a-f]*")
        self.assertRegexpMatches(result["extra_params"], "cache_version=[0-9a-f]*")
        self.assertEquals(result["url_params"], result["extra_params"])

        result2 = entry.mobile()
        self.assertEquals(result2["url_params"], result["url_params"])
        self.assertEquals(result2["extra_params"], result["extra_params"])

    def test_auth_mobile_cache_version(self):
        from c2cgeoportal.views.entry import Entry

        request = self._create_request_obj(username=u"__test_user1")
        entry = Entry(request)
        request.current_route_url = lambda **kwargs: "http://example.com/current/view"
        result = entry.mobile()
        self.assertRegexpMatches(result["url_params"], "cache_version=[0-9a-f]*")
        self.assertRegexpMatches(result["extra_params"], "role=__test_role1&cache_version=[0-9a-f]*")

        result2 = entry.mobile()
        self.assertEquals(result2["url_params"], result["url_params"])
        self.assertEquals(result2["extra_params"], result["extra_params"])

    def test_auth_mobile(self):
        from c2cgeoportal.views.entry import Entry

        request = self._create_request_obj(username=u"__test_user1")
        request.params = {
            u"test": u"éàè"
        }
        entry = Entry(request)
        request.current_route_url = lambda **kwargs: "http://example.com/current/view"
        result = entry.mobile()
        self.assertRegexpMatches(
            result["extra_params"],
            "test=" + urllib.quote("éàè") + "&role=__test_role1&cache_version=[0-9a-f]*"
        )

    def test_entry_points(self):
        from c2cgeoportal.views.entry import Entry

        request = self._create_request_obj()
        request.current_route_url = lambda **kwargs: "http://example.com/current/view"
        mapserv = request.registry.settings["mapserverproxy"]["mapserv_url"]
        request.registry.settings.update({
            "mapserverproxy": {
                "mapserv_url": mapserv,
                "external_mapserv_url": mapserv,
                "geoserver": False,
            },
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

        result = entry.get_cgxp_index_vars()
        self.assertEquals(
            set(result.keys()),
            set(["lang", "debug", "extra_params", "mobile_url", "no_redirect"])
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
            '{"layer_test": {"label": "%s"}}' % mapserv
        )

        result = entry.get_ngeo_index_vars()
        self.assertEquals(set(result.keys()), set([
            "lang", "debug", "user", "functionality", "queryer_attribute_urls",
        ]))
        result = entry.get_ngeo_permalinktheme_vars()
        self.assertEquals(set(result.keys()), set([
            "lang", "debug", "user", "functionality", "queryer_attribute_urls", "permalink_themes",
        ]))

        result = entry.mobile()
        self.assertEquals(
            set(result.keys()),
            set(["lang", "came_from", "url_params", "extra_params"])
        )

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

    def test_auth_home(self):
        from c2cgeoportal.views.entry import Entry
        from c2cgeoportal.models import User, Role

        request = self._create_request_obj()
        mapserv = request.registry.settings["mapserverproxy"]["mapserv_url"]
        request.registry.settings.update({
            "mapserverproxy": {
                "mapserv_url": mapserv,
                "external_mapserv_url": mapserv,
                "geoserver": False,
            },
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
            set(["lang", "debug", "extra_params", "mobile_url", "no_redirect"])
        )
        self.assertEquals(
            set(result["extra_params"].keys()),
            set(["lang"])
        )
        self.assertEquals(result["extra_params"]["lang"], "fr")

    def test_entry_points_version(self):
        from c2cgeoportal.views.entry import Entry

        mapfile = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "c2cgeoportal_test.map"
        )
        mapserv = "%s?map=%s&" % (mapserv_url, mapfile)

        request = testing.DummyRequest()
        request.user = None
        request.headers["Host"] = host

        request.static_url = lambda url: "http://example.com/dummy/static/url"
        request.route_url = lambda url, **kwargs: mapserv
        request.registry.settings = {
            "mapserverproxy": {
                "mapserv_url": mapserv,
                "external_mapserv_url": mapserv,
                "geoserver": False,
            },
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
            set(["lang", "debug", "extra_params", "mobile_url", "no_redirect"])
        )

    def test_entry_points_wfs(self):
        from c2cgeoportal.views.entry import Entry
        from c2cgeoportal.models import User, Role

        request = self._create_request_obj()
        mapserv = request.registry.settings["mapserverproxy"]["mapserv_url"]
        request.registry.settings.update({
            "mapserverproxy": {
                "mapserv_url": mapserv,
                "external_mapserv_url": mapserv,
                "geoserver": False,
            },
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
                "lang", "debug", "extra_params", "mobile_url", "no_redirect"
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
        mapserv = request.registry.settings["mapserverproxy"]["mapserv_url"]
        request.registry.settings.update({
            "mapserverproxy": {
                "mapserv_url": mapserv,
                "external_mapserv_url": mapserv,
                "mapserv_wfs_url": mapserv,
                "external_mapserv_wfs_url": mapserv,
                "geoserver": False,
            },
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
            set(["lang", "debug", "extra_params", "mobile_url", "no_redirect"])
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
            set(["lang", "debug", "extra_params", "mobile_url", "no_redirect"])
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
                "lang", "mobile_url", "permalink_themes",
                "no_redirect", "debug", "extra_params",
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
                "lang", "mobile_url", "permalink_themes", "no_redirect", "debug", "extra_params"
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
            "", LayerGroup(), layers=[], wms=None, wms_layers=[], time=TimeInformation()), (None, set())
        )

        layer = LayerV1()
        layer.id = 20
        layer.name = "test internal WMS"
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
        self.assertEqual(entry._layer(layer, wms=None, wms_layers=[], time=TimeInformation()), ({
            "id": 20,
            "name": "test internal WMS",
            "metadataURL": "http://example.com/tiwms",
            "isChecked": True,
            "icon": "/dummy/route/mapserverproxy?"
            "LAYER=test internal WMS&SERVICE=WMS&FORMAT=image/png&"
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
        }, set(["The layer 'test internal WMS' is not defined in WMS capabilities"])))

        layer = LayerV1()
        layer.id = 20
        layer.name = "test external WMS"
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
        self.assertEqual(entry._layer(layer, wms=None, wms_layers=[], time=TimeInformation), ({
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
        self.assertEqual(entry._layer(layer, wms=None, wms_layers=[], time=TimeInformation()), ({
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
        layer.is_checked = False
        layer.layer_type = "WMTS"
        layer.url = "http://example.com/WMTS-Capabilities.xml"
        layer.wms_url = "http://example.com/"
        layer.legend = False
        layer.is_legend_expanded = False
        layer.min_resolution = 10
        layer.max_resolution = 1000
        layer.public = True
        self.assertEqual(entry._layer(layer, wms=None, wms_layers=[], time=TimeInformation()), ({
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
        layer.is_checked = False
        layer.layer_type = "WMTS"
        layer.url = "http://example.com/WMTS-Capabilities.xml"
        layer.wms_layers = "test"
        layer.legend = False
        layer.is_legend_expanded = False
        layer.min_resolution = 10
        layer.max_resolution = 1000
        layer.public = True
        self.assertEqual(entry._layer(layer, wms=None, wms_layers=[], time=TimeInformation()), ({
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
        layer.is_checked = False
        layer.layer_type = "no 2D"
        layer.legend = False
        layer.is_legend_expanded = False
        layer.metadata_url = "http://example.com/wmsfeatures.metadata"
        layer.public = True
        self.assertEqual(entry._layer(layer, wms=None, wms_layers=[], time=TimeInformation()), ({
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
        mapserv = "%s?map=%s&" % (mapserv_url, mapfile)
        url = mapserv + "&".join(["=".join(p) for p in params])
        http = httplib2.Http()
        h = {"Host": host}
        resp, xml = http.request(url, method="GET", headers=h)

        wms = WebMapService(None, xml=xml)
        wms_layers = list(wms.contents)

        layer = LayerV1()
        layer.id = 20
        layer.name = "test_wmsfeaturesgroup"
        layer.layer_type = "internal WMS"
        layer.image_type = "image/png"
        layer.is_checked = False
        layer.legend = False
        layer.is_legend_expanded = False
        layer.public = True
        self.assertEqual(entry._layer(layer, wms=wms, wms_layers=wms_layers, time=TimeInformation()), ({
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
        layer_t1.layer_type = "internal WMS"
        layer_t1.image_type = "image/png"
        layer_t1.is_checked = False
        layer_t1.legend = False
        layer_t1.is_legend_expanded = False
        layer_t1.public = True
        layer_t1.time_mode = "single"
        time = TimeInformation()
        entry._layer(layer_t1, wms=wms, wms_layers=wms_layers, time=time)
        self.assertEqual(time.to_dict(), {
            "resolution": "year",
            "interval": (1, 0, 0, 0),
            "maxValue": "2010-01-01T00:00:00Z",
            "minValue": "2000-01-01T00:00:00Z",
            "mode": "single",
            "widget": "slider",
            "minDefValue": "2000-01-01T00:00:00Z",
            "maxDefValue": None,
        })

        layer_t2 = LayerV1()
        layer_t2.id = 30
        layer_t2.name = "test_wmstime2"
        layer_t2.layer_type = "internal WMS"
        layer_t2.image_type = "image/png"
        layer_t2.is_checked = False
        layer_t2.legend = False
        layer_t2.is_legend_expanded = False
        layer_t2.public = True
        layer_t2.time_mode = "single"
        layer_t2.time_widget = "slider"
        time = TimeInformation()
        entry._layer(layer_t2, wms=wms, wms_layers=wms_layers, time=time)
        self.assertEqual(time.to_dict(), {
            "resolution": "year",
            "interval": (1, 0, 0, 0),
            "maxValue": "2020-01-01T00:00:00Z",
            "minValue": "2015-01-01T00:00:00Z",
            "mode": "single",
            "widget": "slider",
            "minDefValue": "2015-01-01T00:00:00Z",
            "maxDefValue": None,
        })

        group = LayerGroup()
        group.name = "time"
        group.children = [layer_t1, layer_t2]
        time = TimeInformation()
        entry._group("", group, [layer_t1.name, layer_t2.name], wms=wms, wms_layers=wms_layers, time=time)
        self.assertEqual(time.to_dict(), {
            "resolution": "year",
            "interval": (1, 0, 0, 0),
            "maxValue": "2020-01-01T00:00:00Z",
            "minValue": "2000-01-01T00:00:00Z",
            "mode": "single",
            "widget": "slider",
            "minDefValue": "2000-01-01T00:00:00Z",
            "maxDefValue": None,
        })

        layer = LayerV1()
        layer.id = 20
        layer.name = "test_wmstimegroup"
        layer.layer_type = "internal WMS"
        layer.image_type = "image/png"
        layer.is_checked = False
        layer.legend = False
        layer.is_legend_expanded = False
        layer.public = True
        layer.time_mode = "single"
        layer.time_widget = "datepicker"
        time = TimeInformation()
        entry._layer(layer, wms=wms, wms_layers=wms_layers, time=time)
        self.assertEqual(time.to_dict(), {
            "resolution": "year",
            "interval": (1, 0, 0, 0),
            "maxValue": "2020-01-01T00:00:00Z",
            "minValue": "2000-01-01T00:00:00Z",
            "mode": "single",
            "widget": "datepicker",
            "minDefValue": "2000-01-01T00:00:00Z",
            "maxDefValue": None,
        })

        layer = LayerV1()
        layer.id = 20
        layer.name = "test WMTS"
        layer.is_checked = False
        layer.layer_type = "WMTS"
        layer.url = "http://example.com/WMTS-Capabilities.xml"
        layer.wms_layers = "test_wmsfeatures"
        layer.legend = False
        layer.is_legend_expanded = False
        layer.public = True
        self.assertEqual(entry._layer(layer, wms=wms, wms_layers=wms_layers, time=TimeInformation()), ({
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
        layer.is_checked = False
        layer.layer_type = "WMTS"
        layer.url = "http://example.com/WMTS-Capabilities.xml"
        layer.wms_layers = "foo"
        layer.query_layers = "test_wmsfeatures"
        layer.legend = False
        layer.is_legend_expanded = False
        layer.public = True
        self.assertEqual(entry._layer(layer, wms=wms, wms_layers=wms_layers, time=TimeInformation()), ({
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
        layer.is_checked = False
        layer.layer_type = "internal WMS"
        layer.image_type = "image/png"
        layer.legend = False
        layer.is_legend_expanded = False
        layer.public = True
        group1.children = [group2]
        group2.children = [layer]
        self.assertEqual(entry._group("", group1, [layer.name], wms=None, wms_layers=[], time=TimeInformation()), ({
            "id": 11,
            "isExpanded": False,
            "isInternalWMS": True,
            "name": "block",
            "isBaseLayer": False,
            "metadata": {},
            "children": [{
                "id": 12,
                "isExpanded": False,
                "isInternalWMS": True,
                "name": "node",
                "isBaseLayer": False,
                "metadataURL": "http://example.com/group.metadata",
                "metadata": {},
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
        }, set(["The layer 'test layer in group' is not defined in WMS capabilities"])))

    def _assert_has_error(self, errors, error):
        self.assertIn(error, errors)
        self.assertEquals(
            len([e for e in errors if e == error]), 1,
            "Error '%s' more than one time in errors:\n%r" % (error, errors),
        )

    def test_internalwms(self):
        from c2cgeoportal.views.entry import Entry
        from c2cgeoportal.models import LayerV1, LayerGroup
        from c2cgeoportal.lib.wmstparsing import TimeInformation

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
        _, errors = entry._group("", group1, [], catalogue=False, wms=None, wms_layers=[], time=TimeInformation())
        self._assert_has_error(errors, "Group '' cannot be in group '' (internal/external mix).")

        group1 = LayerGroup()
        group1.is_internal_wms = False
        group2 = LayerGroup()
        group2.is_internal_wms = True
        group1.children = [group2]
        _, errors = entry._group("", group1, [], catalogue=False, wms=None, wms_layers=[], time=TimeInformation())
        self._assert_has_error(errors, "Group '' cannot be in group '' (internal/external mix).")

        group = LayerGroup()
        group.is_internal_wms = True
        layer = LayerV1()
        layer.layer_type = "internal WMS"
        group.children = [layer]
        _, errors = entry._group("", group, [layer.name], catalogue=False, wms=None, wms_layers=[], time=TimeInformation())
        self.assertEqual(errors, set([
            u"The layer '' is not defined in WMS capabilities",
        ]))

        group = LayerGroup()
        group.is_internal_wms = True
        layer = LayerV1()
        layer.layer_type = "external WMS"
        group.children = [layer]
        _, errors = entry._group("", group, [layer.name], catalogue=False, wms=None, wms_layers=[], time=TimeInformation())
        self._assert_has_error(errors, "Layer '' cannot be in the group '' (internal/external mix).")

        group = LayerGroup()
        group.is_internal_wms = True
        layer = LayerV1()
        layer.layer_type = "WMTS"
        group.children = [layer]
        _, errors = entry._group("", group, [layer.name], catalogue=False, wms=None, wms_layers=[], time=TimeInformation())
        self._assert_has_error(errors, "Layer '' cannot be in the group '' (internal/external mix).")

        group = LayerGroup()
        group.is_internal_wms = True
        layer = LayerV1()
        layer.layer_type = "no 2D"
        group.children = [layer]
        _, errors = entry._group("", group, [layer.name], catalogue=False, wms=None, wms_layers=[], time=TimeInformation())
        self._assert_has_error(errors, "Layer '' cannot be in the group '' (internal/external mix).")

        group = LayerGroup()
        group.is_internal_wms = False
        layer = LayerV1()
        layer.layer_type = "internal WMS"
        group.children = [layer]
        _, errors = entry._group("", group, [layer.name], catalogue=False, wms=None, wms_layers=[], time=TimeInformation())
        self._assert_has_error(errors, "Layer '' cannot be in the group '' (internal/external mix).")

        group = LayerGroup()
        group.is_internal_wms = False
        layer = LayerV1()
        layer.layer_type = "external WMS"
        group.children = [layer]
        _, errors = entry._group("", group, [layer.name], catalogue=False, wms=None, wms_layers=[], time=TimeInformation(), min_levels=0)
        self.assertEqual(errors, set())

        group = LayerGroup()
        group.is_internal_wms = False
        layer = LayerV1()
        layer.layer_type = "WMTS"
        group.children = [layer]
        _, errors = entry._group("", group, [layer.name], catalogue=False, wms=None, wms_layers=[], time=TimeInformation(), min_levels=0)
        self.assertEqual(errors, set())

        group = LayerGroup()
        group.is_internal_wms = False
        layer = LayerV1()
        layer.layer_type = "no 2D"
        group.children = [layer]
        _, errors = entry._group("", group, [layer.name], catalogue=False, wms=None, wms_layers=[], time=TimeInformation(), min_levels=0)
        self.assertEqual(errors, set())

    def test_loginchange(self):
        from c2cgeoportal.views.entry import Entry
        from c2cgeoportal.models import User
        from pyramid.httpexceptions import HTTPBadRequest, HTTPUnauthorized
        try:
            from hashlib import sha1
            sha1  # suppress pyflakes warning
        except ImportError:  # pragma: nocover
            from sha import new as sha1  # noqa

        request = self._create_request_obj()
        entry = Entry(request)
        self.assertRaises(HTTPBadRequest, entry.loginchange)

        request = self._create_request_obj(params={
            "lang": "en"
        }, POST={
            "newPassword": "1234",
            "confirmNewPassword": "12345",
        })
        entry = Entry(request)
        self.assertRaises(HTTPUnauthorized, entry.loginchange)

        request.user = User()
        self.assertEquals(request.user.is_password_changed, False)
        self.assertEquals(request.user._password, unicode(sha1("").hexdigest()))
        self.assertRaises(HTTPBadRequest, entry.loginchange)

        request = self._create_request_obj(params={
            "lang": "en"
        }, POST={
            "newPassword": "1234",
            "confirmNewPassword": "1234"
        })
        request.user = User()
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
