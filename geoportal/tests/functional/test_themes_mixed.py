# -*- coding: utf-8 -*-

# Copyright (c) 2016-2021, Camptocamp SA
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


import re
from unittest import TestCase

import transaction
from pyramid import testing
from tests.functional import create_default_ogcserver, create_dummy_request, mapserv_url
from tests.functional import setup_common as setup_module  # noqa
from tests.functional import teardown_common as teardown_module  # noqa


class TestThemesView(TestCase):
    def setup_method(self, _):
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import (
            Interface,
            LayerGroup,
            LayerWMS,
            LayerWMTS,
            OGCServer,
            Theme,
        )

        main = Interface(name="main")

        ogc_server_internal = create_default_ogcserver()
        ogc_server_external = OGCServer(
            name="__test_ogc_server_external", url="http://wms.geo.admin.ch/", image_type="image/jpeg"
        )
        ogc_server_valid_wms_version = OGCServer(
            name="__test_ogc_server_valid_wms_version",
            url=mapserv_url + "?VERSION=1.3.0",
            image_type="image/jpeg",
            wfs_support=False,
        )
        ogc_server_invalid_wms_version = OGCServer(
            name="__test_ogc_server_invalid_wms_version",
            url=mapserv_url + "?VERSION=1.0.0",
            image_type="image/jpeg",
            wfs_support=False,
        )

        layer_internal_wms = LayerWMS(name="__test_layer_internal_wms", public=True)
        layer_internal_wms.layer = "__test_layer_internal_wms"
        layer_internal_wms.interfaces = [main]
        layer_internal_wms.ogc_server = ogc_server_internal

        layer_external_wms = LayerWMS(
            name="__test_layer_external_wms", layer="ch.swisstopo.dreiecksvermaschung", public=True
        )
        layer_external_wms.interfaces = [main]
        layer_external_wms.ogc_server = ogc_server_external

        layer_valid_wms_version = LayerWMS(
            name="__test_valid_wms_version", layer="testpoint_unprotected", public=True
        )
        layer_valid_wms_version.interfaces = [main]
        layer_valid_wms_version.ogc_server = ogc_server_valid_wms_version

        layer_invalid_wms_version = LayerWMS(
            name="__test_invalid_wms_version", layer="testpoint_unprotected", public=True
        )
        layer_invalid_wms_version.interfaces = [main]
        layer_invalid_wms_version.ogc_server = ogc_server_invalid_wms_version

        layer_wmts = LayerWMTS(name="__test_layer_wmts", public=True)
        layer_wmts.url = "http://example.com/1.0.0/WMTSCapabilities.xml"
        layer_wmts.layer = "map"
        layer_wmts.interfaces = [main]

        layer_group_1 = LayerGroup(name="__test_layer_group_1")
        layer_group_1.children = [layer_internal_wms]

        layer_group_2 = LayerGroup(name="__test_layer_group_2")
        layer_group_2.children = [layer_external_wms]

        layer_group_3 = LayerGroup(name="__test_layer_group_3")
        layer_group_3.children = [layer_wmts]

        layer_group_4 = LayerGroup(name="__test_layer_group_4")
        layer_group_4.children = [layer_group_1, layer_group_2]

        layer_group_5 = LayerGroup(name="__test_layer_group_5")
        layer_group_5.children = [layer_group_1, layer_group_3]

        layer_group_6 = LayerGroup(name="__test_layer_group_6")
        layer_group_6.children = [layer_internal_wms]

        layer_group_7 = LayerGroup(name="__test_layer_group_7")
        layer_group_7.children = [layer_group_1, layer_group_6]

        layer_group_8 = LayerGroup(name="__test_layer_group_8")
        layer_group_8.children = [layer_group_2, layer_group_6]

        layer_group_9 = LayerGroup(name="__test_layer_group_9")
        layer_group_9.children = [layer_valid_wms_version, layer_invalid_wms_version]

        theme = Theme(name="__test_theme")
        theme.interfaces = [main]
        theme.children = [
            layer_group_1,
            layer_group_2,
            layer_group_3,
            layer_group_4,
            layer_group_5,
            layer_group_7,
            layer_group_8,
            layer_group_9,
        ]

        DBSession.add(theme)

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
        request.route_url = lambda url, **kwargs: mapserv_url
        request.params = params

        return request

    def _create_theme_obj(self, **kwargs):
        from c2cgeoportal_geoportal.views.theme import Theme

        return Theme(self._create_request_obj(**kwargs))

    def _only_name(self, item, attributes=None):
        if attributes is None:
            attributes = ["name"]
        result = {}

        for attribute in attributes:
            if attribute in item:
                result[attribute] = item[attribute]

        if "children" in item:
            result["children"] = [self._only_name(i, attributes) for i in item["children"]]

        return result

    @staticmethod
    def _get_filtered_errors(themes):
        errors = themes["errors"]

        regex = re.compile(
            r"The (GeoMapFish|WMS) layer name '[a-z0-9_]*', cannot be two times in the same block \(first level group\)."
        )
        errors = [e for e in errors if not regex.match(e)]

        errors = [e[:100] for e in errors]

        return set(errors)

    def test_theme_mixed(self):
        theme_view = self._create_theme_obj(params={"interface": "main"})
        themes = theme_view.themes()
        self.assertEqual(
            self._get_filtered_errors(themes),
            {
                "WARNING! an error 'The WMS version (1.0.0) you requested is not implemented. Please use 1.1.1 or 1.3"
            },
        )
        self.assertEqual(
            [self._only_name(t, ["name", "mixed"]) for t in themes["themes"]],
            [
                {
                    "children": [
                        {
                            "children": [{"name": "__test_layer_internal_wms"}],
                            "mixed": False,
                            "name": "__test_layer_group_1",
                        },
                        {
                            "children": [{"name": "__test_layer_external_wms"}],
                            "mixed": False,
                            "name": "__test_layer_group_2",
                        },
                        {
                            "children": [{"name": "__test_layer_wmts"}],
                            "mixed": True,
                            "name": "__test_layer_group_3",
                        },
                        {
                            "children": [
                                {
                                    "children": [{"name": "__test_layer_internal_wms"}],
                                    "mixed": True,
                                    "name": "__test_layer_group_1",
                                },
                                {
                                    "children": [{"name": "__test_layer_external_wms"}],
                                    "mixed": True,
                                    "name": "__test_layer_group_2",
                                },
                            ],
                            "mixed": True,
                            "name": "__test_layer_group_4",
                        },
                        {
                            "children": [
                                {
                                    "children": [{"name": "__test_layer_internal_wms"}],
                                    "mixed": True,
                                    "name": "__test_layer_group_1",
                                },
                                {
                                    "children": [{"name": "__test_layer_wmts"}],
                                    "mixed": True,
                                    "name": "__test_layer_group_3",
                                },
                            ],
                            "mixed": True,
                            "name": "__test_layer_group_5",
                        },
                        {
                            "children": [
                                {
                                    "children": [{"name": "__test_layer_internal_wms"}],
                                    "mixed": False,
                                    "name": "__test_layer_group_1",
                                },
                                {
                                    "children": [{"name": "__test_layer_internal_wms"}],
                                    "mixed": False,
                                    "name": "__test_layer_group_6",
                                },
                            ],
                            "mixed": False,
                            "name": "__test_layer_group_7",
                        },
                        {
                            "children": [
                                {
                                    "children": [{"name": "__test_layer_external_wms"}],
                                    "mixed": True,
                                    "name": "__test_layer_group_2",
                                },
                                {
                                    "children": [{"name": "__test_layer_internal_wms"}],
                                    "mixed": True,
                                    "name": "__test_layer_group_6",
                                },
                            ],
                            "mixed": True,
                            "name": "__test_layer_group_8",
                        },
                        {
                            "children": [{"name": "__test_valid_wms_version"}],
                            "mixed": True,
                            "name": "__test_layer_group_9",
                        },
                    ],
                    "name": "__test_theme",
                }
            ],
        )
