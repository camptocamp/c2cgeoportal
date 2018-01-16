# -*- coding: utf-8 -*-

# Copyright (c) 2016-2018, Camptocamp SA
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


import re
import transaction

from unittest import TestCase

from pyramid import testing

from tests.functional import (  # noqa
    teardown_common as teardown_module,
    setup_common as setup_module,
    mapserv_url, create_dummy_request, create_default_ogcserver,
)

import logging
log = logging.getLogger(__name__)


class TestThemesView(TestCase):

    def setup_method(self, _):
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import \
            Theme, LayerGroup, Interface, LayerWMS, LayerWMTS, Dimension

        ogc_server, _ = create_default_ogcserver()
        main = Interface(name="main")

        layer_wms_1 = LayerWMS(name="__test_layer_wms_1", public=True)
        layer_wms_1.layer = "__test_layer_wms_1"
        layer_wms_1.interfaces = [main]
        layer_wms_1.ogc_server = ogc_server
        Dimension("A", "a", layer_wms_1)

        layer_wms_2 = LayerWMS(name="__test_layer_wms_2", public=True)
        layer_wms_2.layer = "__test_layer_wms_2"
        layer_wms_2.interfaces = [main]
        layer_wms_2.ogc_server = ogc_server
        Dimension("A", "b", layer_wms_2)

        layer_wms_3 = LayerWMS(name="__test_layer_wms_3", public=True)
        layer_wms_3.layer = "__test_layer_wms_3"
        layer_wms_3.interfaces = [main]
        layer_wms_3.ogc_server = ogc_server
        Dimension("A", None, layer_wms_3)

        layer_wms_4 = LayerWMS(name="__test_layer_wms_4", public=True)
        layer_wms_4.layer = "__test_layer_wms_4"
        layer_wms_4.interfaces = [main]
        layer_wms_4.ogc_server = ogc_server
        Dimension("A", "a", layer_wms_4)

        layer_wms_5 = LayerWMS(name="__test_layer_wms_5", public=True)
        layer_wms_5.layer = "__test_layer_wms_5"
        layer_wms_5.interfaces = [main]
        layer_wms_5.ogc_server = ogc_server
        Dimension("B", "b", layer_wms_5)

        layer_wms_6 = LayerWMS(name="__test_layer_wms_6", public=True)
        layer_wms_6.layer = "__test_layer_wms_6"
        layer_wms_6.interfaces = [main]
        layer_wms_6.ogc_server = ogc_server
        Dimension("FILTER", "countries:\"name\" IN ( 'Germany' , 'Italy' )", layer_wms_6)

        layer_wmts = LayerWMTS(name="__test_layer_wmts", public=True)
        layer_wmts.url = "http://example.com/1.0.0/WMTSCapabilities.xml"
        layer_wmts.layer = "map"
        layer_wmts.interfaces = [main]
        Dimension("B", "b", layer_wmts)

        layer_wmts_2 = LayerWMTS(name="__test_layer_wmts_2", public=True)
        layer_wmts_2.url = "http://example.com/1.0.0/WMTSCapabilities.xml"
        layer_wmts_2.layer = "map"
        layer_wmts_2.interfaces = [main]
        Dimension("FILTER", "countries:\"name\" IN ( 'Germany' , 'Italy' )", layer_wmts_2)

        layer_group_1 = LayerGroup(name="__test_layer_group_1")
        layer_group_1.children = [layer_wms_1, layer_wmts, layer_wmts_2]

        layer_group_2 = LayerGroup(name="__test_layer_group_2")
        layer_group_2.children = [layer_wms_1, layer_wms_2]

        layer_group_3 = LayerGroup(name="__test_layer_group_3")
        layer_group_3.children = [layer_wms_1, layer_wms_3]

        layer_group_4 = LayerGroup(name="__test_layer_group_4")
        layer_group_4.children = [layer_wms_1, layer_wms_4]

        layer_group_5 = LayerGroup(name="__test_layer_group_5")
        layer_group_5.children = [layer_wms_1, layer_wms_5, layer_wms_6]

        layer_group_6 = LayerGroup(name="__test_layer_group_6")
        layer_group_6.children = [layer_wms_3]

        theme = Theme(name="__test_theme")
        theme.interfaces = [main]
        theme.children = [
            layer_group_1, layer_group_2, layer_group_3,
            layer_group_4, layer_group_5, layer_group_6,
        ]

        DBSession.add(theme)

        transaction.commit()

    def teardown_method(self, _):
        testing.tearDown()

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import TreeItem, Interface, Dimension, OGCServer

        DBSession.query(Dimension).delete()
        for item in DBSession.query(TreeItem).all():
            DBSession.delete(item)
        DBSession.query(Interface).filter(
            Interface.name == "main"
        ).delete()
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
        request.static_url = lambda url: "/dummy/static/url"
        request.route_url = lambda url, **kwargs: mapserv_url
        request.params = params

        return request

    def _create_entry_obj(self, **kwargs):
        from c2cgeoportal_geoportal.views.entry import Entry

        return Entry(self._create_request_obj(**kwargs))

    def _only_name(self, item, attributes=None):
        if attributes is None:
            attributes = ["name"]
        result = {}

        for attribute in attributes:
            if attribute in item:
                result[attribute] = item[attribute]

        if "children" in item:
            result["children"] = [
                self._only_name(i, attributes) for i in item["children"]
            ]

        return result

    @staticmethod
    def _get_filtered_errors(themes):
        regex = re.compile(r"^The layer '__[a-z0-9_]+' \(__[a-z0-9_]+\) is not defined in WMS capabilities from '__test_ogc_server'$")
        return {e for e in themes["errors"] if regex.search(e) is None}

    def test_theme_dimensions(self):
        entry = self._create_entry_obj(params={
            "version": "2",
            "interface": "main",
        })
        themes = entry.themes()
        self.assertEqual(self._get_filtered_errors(themes), set([
            "The layer '__test_layer_wms_2' has a wrong dimension value 'b' for 'A', expected 'a' or empty.",
            "The layer '__test_layer_wmts_2' has an unsupported dimension value 'countries:\"name\" IN ( 'Germany' , 'Italy' )' ('FILTER')."
        ]))
        self.assertEqual(
            [self._only_name(t, ["name", "dimensions"]) for t in themes["themes"]],
            [{
                "children": [{
                    "name": "__test_layer_group_1",
                    "children": [{
                        "dimensions": {"A": "a"},
                        "name": "__test_layer_wms_1"
                    }, {
                        "dimensions": {"B": "b"},
                        "name": "__test_layer_wmts"
                    }, {
                        "dimensions": {},
                        "name": "__test_layer_wmts_2"
                    }],
                }, {
                    "name": "__test_layer_group_2",
                    "children": [{
                        "name": "__test_layer_wms_1",
                    }, {
                        "name": "__test_layer_wms_2",
                    }],
                    "dimensions": {"A": "a"},
                }, {
                    "name": "__test_layer_group_3",
                    "children": [{
                        "name": "__test_layer_wms_1",
                    }, {
                        "name": "__test_layer_wms_3",
                    }],
                    "dimensions": {"A": "a"},
                }, {
                    "name": "__test_layer_group_4",
                    "children": [{
                        "name": "__test_layer_wms_1",
                    }, {
                        "name": "__test_layer_wms_4",
                    }],
                    "dimensions": {"A": "a"},
                }, {
                    "name": "__test_layer_group_5",
                    "children": [{
                        "name": "__test_layer_wms_1",
                    }, {
                        "name": "__test_layer_wms_5",
                    }, {
                        "name": "__test_layer_wms_6",
                    }],
                    "dimensions": {
                        "A": "a",
                        "B": "b",
                        "FILTER": "countries:\"name\" IN ( 'Germany' , 'Italy' )"
                    },
                }, {
                    "name": "__test_layer_group_6",
                    "children": [{
                        "name": "__test_layer_wms_3",
                    }],
                    "dimensions": {"A": None},
                }],
                "name": "__test_theme",
            }]
        )
