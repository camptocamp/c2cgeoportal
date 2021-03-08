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

# pylint: disable=missing-docstring,attribute-defined-outside-init,protected-access

from unittest import TestCase

import transaction
from pyramid import testing
from tests.functional import create_default_ogcserver, create_dummy_request
from tests.functional import setup_common as setup_module  # noqa
from tests.functional import teardown_common as teardown_module  # noqa


class TestThemesPrivateView(TestCase):
    def setUp(self):  # noqa
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None

        self.clean()

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import (
            Interface,
            LayerGroup,
            LayerWMS,
            LayerWMTS,
            RestrictionArea,
            Role,
            Theme,
        )
        from c2cgeoportal_commons.models.static import User

        main = Interface(name="desktop")
        role = Role(name="__test_role")
        user = User(username="__test_user", password="__test_user", settings_role=role, roles=[role])
        user.email = "__test_user@example.com"
        role2 = Role(name="__test_role2")
        user2 = User(username="__test_user2", password="__test_user", settings_role=role, roles=[role, role2])
        user2.email = "__test_user@example.com"
        ogc_server_internal = create_default_ogcserver()

        layer_wms = LayerWMS(name="__test_layer_wms", public=True)
        layer_wms.layer = "__test_public_layer"
        layer_wms.interfaces = [main]
        layer_wms.ogc_server = ogc_server_internal

        layer_wms_private = LayerWMS(name="__test_layer_wms_private", public=False)
        layer_wms_private.layer = "testpoint_protected"
        layer_wms_private.interfaces = [main]
        layer_wms_private.ogc_server = ogc_server_internal

        layer_wms_private2 = LayerWMS(name="__test_layer_wms_private2", public=False)
        layer_wms_private2.layer = "__test_private_layer2"
        layer_wms_private2.interfaces = [main]
        layer_wms_private2.ogc_server = ogc_server_internal

        layer_wmts = LayerWMTS(name="__test_layer_wmts", public=True)
        layer_wmts.url = "http://example.com/1.0.0/WMTSCapabilities.xml"
        layer_wmts.layer = "map"
        layer_wmts.interfaces = [main]

        layer_wmts_private = LayerWMTS(name="__test_layer_wmts_private", public=True)
        layer_wmts_private.url = "http://example.com/1.0.0/WMTSCapabilities.xml"
        layer_wmts_private.layer = "map"
        layer_wmts_private.public = False
        layer_wmts_private.interfaces = [main]

        layer_group = LayerGroup(name="__test_layer_group")
        layer_group.children = [
            layer_wms,
            layer_wms_private,
            layer_wms_private2,
            layer_wmts,
            layer_wmts_private,
        ]

        theme = Theme(name="__test_theme")
        theme.interfaces = [main]
        theme.children = [layer_group]

        restriction_area = RestrictionArea(
            name="__test_ra1", layers=[layer_wms_private, layer_wmts_private], roles=[role]
        )
        restriction_area2 = RestrictionArea(name="__test_ra2", layers=[layer_wms_private2], roles=[role2])

        DBSession.add_all([theme, restriction_area, restriction_area2, user])

        transaction.commit()

    def tearDown(self):  # noqa
        self.clean()
        testing.tearDown()

    @staticmethod
    def clean():
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import Interface, OGCServer, RestrictionArea, Role, TreeItem
        from c2cgeoportal_commons.models.static import User

        for obj in DBSession.query(RestrictionArea).all():
            obj.roles = []
            obj.layers = []
            DBSession.delete(obj)
        for item in DBSession.query(TreeItem).all():
            DBSession.delete(item)
        DBSession.query(OGCServer).delete()
        DBSession.query(Interface).filter(Interface.name == "main").delete()
        for name in ("__test_user", "__test_user2"):
            for user in DBSession.query(User).filter(User.username == name).all():
                DBSession.delete(user)
        for name in ("__test_role", "__test_role2"):
            DBSession.query(Role).filter(Role.name == name).delete()

        transaction.commit()

    #
    # viewer view tests
    #

    @staticmethod
    def _create_request_obj(params=None, user=None, **kwargs):
        if params is None:
            params = {}
        request = create_dummy_request(**kwargs)
        request.user = user

        def route_url(name, _query=None, **kwargs):
            del name  # Unused
            del kwargs  # Unused
            if _query is None:
                return "http://localhost/ci/mapserv"
            else:
                return "http://localhost/ci/mapserv?" + "&".join(["=".join(i) for i in _query.items()])

        request.route_url = route_url
        request.params = params

        return request

    def _create_theme_obj(self, **kwargs):
        from c2cgeoportal_geoportal.views.theme import Theme

        return Theme(self._create_request_obj(**kwargs))

    def _only_name(self, item, attribute="name"):
        result = {}

        if attribute in item:
            result[attribute] = item[attribute]

        if "children" in item:
            result["children"] = [self._only_name(i, attribute) for i in item["children"]]

        return result

    @staticmethod
    def _get_filtered_errors(themes):
        return {
            e
            for e in themes["errors"]
            if e != "The layer '' (__test_layer_external_wms) is not defined in WMS capabilities"
            and not e.startswith("Unable to get DescribeFeatureType from URL ")
        }

    def test_public(self):
        theme_view = self._create_theme_obj()
        themes = theme_view.themes()
        self.assertEqual(self._get_filtered_errors(themes), set())
        self.assertEqual(
            [self._only_name(t) for t in themes["themes"]],
            [
                {
                    "name": "__test_theme",
                    "children": [
                        {
                            "name": "__test_layer_group",
                            "children": [{"name": "__test_layer_wms"}, {"name": "__test_layer_wmts"}],
                        }
                    ],
                }
            ],
        )

    def test_private(self):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User

        theme_view = self._create_theme_obj(
            user=DBSession.query(User).filter_by(username="__test_user").one()
        )
        themes = theme_view.themes()
        self.assertEqual(self._get_filtered_errors(themes), set())
        self.assertEqual(
            [self._only_name(t) for t in themes["themes"]],
            [
                {
                    "name": "__test_theme",
                    "children": [
                        {
                            "name": "__test_layer_group",
                            "children": [
                                {"name": "__test_layer_wms"},
                                {"name": "__test_layer_wms_private"},
                                {"name": "__test_layer_wmts"},
                                {"name": "__test_layer_wmts_private"},
                            ],
                        }
                    ],
                }
            ],
        )

    def test_private_multirole(self):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User

        theme_view = self._create_theme_obj(
            user=DBSession.query(User).filter_by(username="__test_user2").one()
        )
        themes = theme_view.themes()
        self.assertEqual(self._get_filtered_errors(themes), set())
        self.assertEqual(
            [self._only_name(t) for t in themes["themes"]],
            [
                {
                    "name": "__test_theme",
                    "children": [
                        {
                            "name": "__test_layer_group",
                            "children": [
                                {"name": "__test_layer_wms"},
                                {"name": "__test_layer_wms_private"},
                                {"name": "__test_layer_wms_private2"},
                                {"name": "__test_layer_wmts"},
                                {"name": "__test_layer_wmts_private"},
                            ],
                        }
                    ],
                }
            ],
        )

    def test_ogc_server_private_layers(self):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User

        theme_view = self._create_theme_obj()
        themes = theme_view.themes()
        assert "testpoint_protected" not in themes["ogcServers"]["__test_ogc_server"]["attributes"]

        theme_view = self._create_theme_obj(
            user=DBSession.query(User).filter_by(username="__test_user").one()
        )
        themes = theme_view.themes()
        assert "testpoint_protected" in themes["ogcServers"]["__test_ogc_server"]["attributes"]
