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


class TestThemesView(TestCase):
    def setup_method(self, _):
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import (
            OGCSERVER_AUTH_NOAUTH,
            Dimension,
            Functionality,
            Interface,
            LayerGroup,
            LayerWMS,
            LayerWMTS,
            Metadata,
            OGCServer,
            Theme,
        )

        main = Interface(name="desktop")
        mobile = Interface(name="mobile")
        min_levels = Interface(name="min_levels")

        ogc_server_internal = create_default_ogcserver()
        ogc_server_external = OGCServer(
            name="__test_ogc_server_chtopo",
            url="http://wms.geo.admin.ch/",
            image_type="image/jpeg",
            auth=OGCSERVER_AUTH_NOAUTH,
        )
        ogc_server_external.wfs_support = False

        layer_internal_wms = LayerWMS(name="__test_layer_internal_wms", public=True)
        layer_internal_wms.layer = "__test_layer_internal_wms"
        layer_internal_wms.interfaces = [main, min_levels]
        layer_internal_wms.metadatas = [Metadata("test", "internal_wms")]
        layer_internal_wms.ogc_server = ogc_server_internal

        layer_external_wms = LayerWMS(
            name="__test_layer_external_wms", layer="ch.swisstopo.dreiecksvermaschung", public=True
        )
        layer_external_wms.interfaces = [main]
        layer_external_wms.metadatas = [Metadata("test", "external_wms")]
        layer_external_wms.ogc_server = ogc_server_external

        layer_wmts = LayerWMTS(name="__test_layer_wmts", public=True)
        layer_wmts.url = "http://example.com/1.0.0/WMTSCapabilities.xml"
        layer_wmts.layer = "map"
        layer_wmts.interfaces = [main, mobile]
        layer_wmts.metadatas = [Metadata("test", "wmts")]
        layer_wmts.dimensions = [Dimension("year", "2015")]

        layer_group_1 = LayerGroup(name="__test_layer_group_1")
        layer_group_1.children = [layer_internal_wms, layer_external_wms, layer_wmts]
        layer_group_1.metadatas = [Metadata("test", "group_1")]

        layer_group_2 = LayerGroup(name="__test_layer_group_2")
        layer_group_2.children = [layer_wmts, layer_internal_wms, layer_external_wms]

        layer_group_3 = LayerGroup(name="__test_layer_group_3")
        layer_group_3.children = [layer_wmts, layer_internal_wms, layer_external_wms]

        layer_group_4 = LayerGroup(name="__test_layer_group_4")
        layer_group_4.children = [layer_group_2]

        theme = Theme(name="__test_theme")
        theme.interfaces = [main, mobile]
        theme.metadatas = [Metadata("test", "theme")]
        theme.children = [layer_group_1, layer_group_2]
        theme_layer = Theme(name="__test_theme_layer")
        theme_layer.interfaces = [min_levels]
        theme_layer.children = [layer_internal_wms]

        functionality1 = Functionality(name="test_name", value="test_value_1")
        functionality2 = Functionality(name="test_name", value="test_value_2")
        theme.functionalities = [functionality1, functionality2]

        DBSession.add_all([theme, theme_layer])

        transaction.commit()

    def teardown_method(self, _):
        testing.tearDown()

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import Dimension, Interface, Metadata, OGCServer, TreeItem

        DBSession.query(Metadata).delete()
        DBSession.query(Dimension).delete()
        for item in DBSession.query(TreeItem).all():
            DBSession.delete(item)
        DBSession.query(Interface).filter(Interface.name == "main").delete()
        DBSession.query(OGCServer).delete()

        transaction.commit()

    #
    # viewer view tests
    #

    @staticmethod
    def _create_request_obj(params=None, **kwargs):
        if params is None:
            params = {}
        request = create_dummy_request(**kwargs)

        def route_url(name, _query=None, **kwargs):
            del name  # Unused
            del kwargs  # Unused
            if _query is None:
                return "http://localhost/ci/mapserv"
            else:
                return "http://localhost/ci/mapserv?" + "&".join(["=".join(i) for i in list(_query.items())])

        request.route_url = route_url
        request.params = params

        return request

    def _create_theme_obj(self, **kwargs):
        from c2cgeoportal_geoportal.views.theme import Theme

        kwargs["additional_settings"] = {"admin_interface": {"available_metadata": [{"name": "test"}]}}
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
        print(themes["errors"])
        return {
            e
            for e in themes["errors"]
            if e != "The layer '' (__test_layer_external_wms) is not defined in WMS capabilities"
            and not e.startswith("Unable to get DescribeFeatureType from URL ")
        }

    def test_group(self):
        theme_view = self._create_theme_obj(params={"group": "__test_layer_group_3"})
        themes = theme_view.themes()
        self.assertEqual(self._get_filtered_errors(themes), set())
        self.assertEqual(
            self._only_name(themes["group"]),
            {
                "name": "__test_layer_group_3",
                # order is important
                "children": [
                    {"name": "__test_layer_wmts"},
                    {"name": "__test_layer_internal_wms"},
                    {"name": "__test_layer_external_wms"},
                ],
            },
        )

        theme_view = self._create_theme_obj(params={"group": "__test_layer_group_4"})
        themes = theme_view.themes()
        self.assertEqual(self._get_filtered_errors(themes), set())
        self.assertEqual(
            self._only_name(themes["group"]),
            {
                "name": "__test_layer_group_4",
                "children": [
                    {
                        "name": "__test_layer_group_2",
                        # order is important
                        "children": [
                            {"name": "__test_layer_wmts"},
                            {"name": "__test_layer_internal_wms"},
                            {"name": "__test_layer_external_wms"},
                        ],
                    }
                ],
            },
        )

    def test_group_update(self):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import LayerGroup

        layer_group_3 = DBSession.query(LayerGroup).filter(LayerGroup.name == "__test_layer_group_3").one()
        layer_group_3.children = layer_group_3.children[:-1]
        transaction.commit()

        theme_view = self._create_theme_obj(params={"group": "__test_layer_group_3"})
        themes = theme_view.themes()
        self.assertEqual(self._get_filtered_errors(themes), set())
        self.assertEqual(
            self._only_name(themes["group"]),
            {
                "name": "__test_layer_group_3",
                # order is important
                "children": [{"name": "__test_layer_wmts"}, {"name": "__test_layer_internal_wms"}],
            },
        )

    def test_min_levels(self):
        theme_view = self._create_theme_obj(params={"interface": "min_levels"})
        themes = theme_view.themes()
        self.assertEqual(
            self._get_filtered_errors(themes),
            set(
                [
                    "The Layer '__test_layer_internal_wms' cannot be directly in the theme '__test_theme_layer' (0/1)."
                ]
            ),
        )

        theme_view = self._create_theme_obj(params={"min_levels": "2"})
        themes = theme_view.themes()
        self.assertEqual(
            self._get_filtered_errors(themes),
            set(
                [
                    "The Layer '__test_theme/__test_layer_group_1/__test_layer_internal_wms' is under indented (1/2).",
                    "The Layer '__test_theme/__test_layer_group_1/__test_layer_wmts' is under indented (1/2).",
                    "The Layer '__test_theme/__test_layer_group_2/__test_layer_external_wms' is under indented (1/2).",
                    "The Layer '__test_theme/__test_layer_group_2/__test_layer_internal_wms' is under indented (1/2).",
                    "The Layer '__test_theme/__test_layer_group_1/__test_layer_external_wms' is under indented (1/2).",
                    "The Layer '__test_theme/__test_layer_group_2/__test_layer_wmts' is under indented (1/2).",
                ]
            ),
        )

    def test_theme_layer(self):
        theme_view = self._create_theme_obj(params={"interface": "min_levels", "min_levels": "0"})
        themes = theme_view.themes()
        self.assertEqual(self._get_filtered_errors(themes), set())
        self.assertEqual(
            [self._only_name(t) for t in themes["themes"]],
            [{"name": "__test_theme_layer", "children": [{"name": "__test_layer_internal_wms"}]}],
        )

    def test_interface(self):
        theme_view = self._create_theme_obj(params={"interface": "mobile"})
        themes = theme_view.themes()
        self.assertEqual(self._get_filtered_errors(themes), set())
        self.assertEqual(
            [self._only_name(t) for t in themes["themes"]],
            [
                {
                    "name": "__test_theme",
                    "children": [
                        {"name": "__test_layer_group_1", "children": [{"name": "__test_layer_wmts"}]},
                        {"name": "__test_layer_group_2", "children": [{"name": "__test_layer_wmts"}]},
                    ],
                }
            ],
        )

    def test_metadata(self):
        theme_view = self._create_theme_obj()
        themes = theme_view.themes()
        self.assertEqual(self._get_filtered_errors(themes), set())
        self.assertEqual(
            [self._only_name(t, "metadata") for t in themes["themes"]],
            [
                {
                    "metadata": {"test": "theme"},
                    "children": [
                        {
                            "metadata": {"test": "group_1"},
                            # order is important
                            "children": [
                                {"metadata": {"test": "internal_wms"}},
                                {"metadata": {"test": "external_wms"}},
                                {"metadata": {"test": "wmts"}},
                            ],
                        },
                        {
                            "metadata": {},
                            # order is important
                            "children": [
                                {"metadata": {"test": "wmts"}},
                                {"metadata": {"test": "internal_wms"}},
                                {"metadata": {"test": "external_wms"}},
                            ],
                        },
                    ],
                }
            ],
        )

    def test_ogc_server(self):
        theme_view = self._create_theme_obj()

        themes = theme_view.themes()
        themes["ogcServers"]["__test_ogc_server"]["attributes"] = {}
        themes["ogcServers"]["__test_ogc_server_chtopo"]["attributes"] = {}
        self.assertEqual(self._get_filtered_errors(themes), set())
        self.assertEqual(
            themes["ogcServers"],
            {
                "__test_ogc_server": {
                    "attributes": {},
                    "credential": True,
                    "imageType": "image/png",
                    "isSingleTile": False,
                    "namespace": "http://mapserver.gis.umn.edu/mapserver",
                    "type": "mapserver",
                    "url": "http://localhost/ci/mapserv?ogcserver=__test_ogc_server",
                    "urlWfs": "http://localhost/ci/mapserv?ogcserver=__test_ogc_server",
                    "wfsSupport": True,
                },
                "__test_ogc_server_chtopo": {
                    "attributes": {},
                    "credential": False,
                    "imageType": "image/jpeg",
                    "isSingleTile": False,
                    "namespace": None,
                    "type": "mapserver",
                    "url": "http://wms.geo.admin.ch/",
                    "urlWfs": "http://wms.geo.admin.ch/",
                    "wfsSupport": False,
                },
            },
        )
        self.assertEqual(
            [self._only_name(t, "ogcServer") for t in themes["themes"]],
            [
                {
                    "children": [
                        {
                            # order is important
                            "children": [
                                {"ogcServer": "__test_ogc_server"},
                                {"ogcServer": "__test_ogc_server_chtopo"},
                                {},
                            ]
                        },
                        {
                            # order is important
                            "children": [
                                {},
                                {"ogcServer": "__test_ogc_server"},
                                {"ogcServer": "__test_ogc_server_chtopo"},
                            ]
                        },
                    ]
                }
            ],
        )

    def test_dimensions(self):
        theme_view = self._create_theme_obj(params={"group": "__test_layer_group_3"})
        themes = theme_view.themes()
        self.assertEqual(self._get_filtered_errors(themes), set())
        self.assertEqual(
            self._only_name(themes["group"], "dimensions"),
            {
                # order is important
                "children": [{"dimensions": {"year": "2015"}}, {"dimensions": {}}, {"dimensions": {}}]
            },
        )

    def test_background(self):
        theme_view = self._create_theme_obj(
            params={"background": "__test_layer_group_3", "set": "background"}
        )
        themes = theme_view.themes()
        self.assertEqual(self._get_filtered_errors(themes), set())
        self.assertEqual(
            [self._only_name(e) for e in themes["background_layers"]],
            # order is important
            [
                {"name": "__test_layer_wmts"},
                {"name": "__test_layer_internal_wms"},
                {"name": "__test_layer_external_wms"},
            ],
        )
