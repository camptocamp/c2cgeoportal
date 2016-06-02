# -*- coding: utf-8 -*-

# Copyright (c) 2016, Camptocamp SA
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

from unittest2 import TestCase
from nose.plugins.attrib import attr

from pyramid import testing

from c2cgeoportal.tests.functional import (  # noqa
    tear_down_common as tearDownModule,
    set_up_common as setUpModule,
    mapserv_url, host, create_dummy_request)

import logging
log = logging.getLogger(__name__)


@attr(functional=True)
class TestThemesView(TestCase):

    def setUp(self):  # noqa
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None

        from c2cgeoportal.models import DBSession, \
            Theme, LayerGroup, Interface, ServerOGC, LayerWMS, LayerWMTS

        main = Interface(name=u"main")

        server_ogc_internal = ServerOGC(name="__test_server_ogc_internal", type="mapserver", image_type="image/jpeg")
        server_ogc_external = ServerOGC(name="__test_server_ogc_external", url="http://wms.geo.admin.ch/", image_type="image/jpeg")

        layer_internal_wms = LayerWMS(name=u"__test_layer_internal_wms", public=True)
        layer_internal_wms.layer = "__test_layer_internal_wms"
        layer_internal_wms.interfaces = [main]
        layer_internal_wms.server_ogc = server_ogc_internal

        layer_external_wms = LayerWMS(name=u"__test_layer_external_wms", layer="ch.swisstopo.dreiecksvermaschung", public=True)
        layer_external_wms.interfaces = [main]
        layer_external_wms.server_ogc = server_ogc_external

        layer_wmts = LayerWMTS(name=u"__test_layer_wmts", public=True)
        layer_wmts.interfaces = [main]

        layer_group_1 = LayerGroup(name=u"__test_layer_group_1")
        layer_group_1.children = [layer_internal_wms]

        layer_group_2 = LayerGroup(name=u"__test_layer_group_2")
        layer_group_2.children = [layer_external_wms]

        layer_group_3 = LayerGroup(name=u"__test_layer_group_3")
        layer_group_3.children = [layer_wmts]

        layer_group_4 = LayerGroup(name=u"__test_layer_group_4")
        layer_group_4.children = [layer_group_1, layer_group_2]

        layer_group_5 = LayerGroup(name=u"__test_layer_group_5")
        layer_group_5.children = [layer_group_1, layer_group_3]

        layer_group_6 = LayerGroup(name=u"__test_layer_group_6")
        layer_group_6.children = [layer_internal_wms]

        layer_group_7 = LayerGroup(name=u"__test_layer_group_7")
        layer_group_7.children = [layer_group_1, layer_group_6]

        layer_group_8 = LayerGroup(name=u"__test_layer_group_8")
        layer_group_8.children = [layer_group_2, layer_group_6]

        theme = Theme(name=u"__test_theme")
        theme.interfaces = [main]
        theme.children = [
            layer_group_1, layer_group_2, layer_group_3,
            layer_group_4, layer_group_5,
            layer_group_7, layer_group_8,
        ]

        DBSession.add(theme)

        transaction.commit()

    def tearDown(self):  # noqa
        testing.tearDown()

        from c2cgeoportal.models import DBSession, Layer, \
            Theme, LayerGroup, Interface, UIMetadata, WMTSDimension

        for t in DBSession.query(UIMetadata).all():
            DBSession.delete(t)
        for t in DBSession.query(WMTSDimension).all():
            DBSession.delete(t)
        for layer in DBSession.query(Layer).all():
            DBSession.delete(layer)
        for layergroup in DBSession.query(LayerGroup).all():
            DBSession.delete(layergroup)
        for t in DBSession.query(Theme).all():
            DBSession.delete(t)
        DBSession.query(Interface).filter(
            Interface.name == "main"
        ).delete()

        transaction.commit()

    #
    # viewer view tests
    #

    def _create_request_obj(self, params={}, **kwargs):
        request = create_dummy_request(**kwargs)
        request.static_url = lambda url: "/dummy/static/url"
        request.route_url = lambda url, **kwargs: \
            request.registry.settings["mapserverproxy"]["mapserv_url"]
        request.params = params

        return request

    def _create_entry_obj(self, **kwargs):
        from c2cgeoportal.views.entry import Entry

        return Entry(self._create_request_obj(**kwargs))

    def _only_name(self, item, attributes=["name"]):
        result = {}

        for attribute in attributes:
            if attribute in item:
                result[attribute] = item[attribute]

        if "children" in item:
            result["children"] = [
                self._only_name(i, attributes) for i in item["children"]
            ]

        return result

    def _get_filtered_errors(self, themes):
        prog = re.compile("^The layer '' \(__test_layer_external_wms\) is not defined in WMS capabilities$")
        return set([e for e in themes["errors"] if prog.match(e) is None])

    def test_theme_mixed(self):
        entry = self._create_entry_obj(params={
            "version": "2",
            "interface": "main",
        })
        themes = entry.themes()
        self.assertEquals(self._get_filtered_errors(themes), set())
        self.assertEquals(
            [self._only_name(t, ["name", "mixed"]) for t in themes["themes"]],
            [{
                "children": [{
                    "children": [{
                        "name": "__test_layer_internal_wms"
                    }],
                    "mixed": False,
                    "name": "__test_layer_group_1"
                }, {
                    "children": [{
                        "name": "__test_layer_external_wms"
                    }],
                    "mixed": False,
                    "name": "__test_layer_group_2"
                }, {
                    "children": [{
                        "name": "__test_layer_wmts"
                    }],
                    "mixed": True,
                    "name": "__test_layer_group_3"
                }, {
                    "children": [{
                        "children": [{
                            "name": "__test_layer_internal_wms"
                        }],
                        "mixed": True,
                        "name": "__test_layer_group_1"
                    }, {
                        "children": [{
                            "name": "__test_layer_external_wms"
                        }],
                        "mixed": True,
                        "name": "__test_layer_group_2"
                    }],
                    "mixed": True,
                    "name": "__test_layer_group_4"
                }, {
                    "children": [{
                        "children": [{
                            "name": "__test_layer_internal_wms"
                        }],
                        "mixed": True,
                        "name": "__test_layer_group_1"
                    }, {
                        "children": [{
                            "name": "__test_layer_wmts"
                        }],
                        "mixed": True,
                        "name": "__test_layer_group_3"
                    }],
                    "mixed": True,
                    "name": "__test_layer_group_5"
                }, {
                    "children": [{
                        "children": [{
                            "name": "__test_layer_internal_wms"
                        }],
                        "mixed": False,
                        "name": "__test_layer_group_1"
                    }, {
                        "children": [{
                            "name": "__test_layer_internal_wms"
                        }],
                        "mixed": False,
                        "name": "__test_layer_group_6"
                    }],
                    "mixed": False,
                    "name": "__test_layer_group_7"
                }, {
                    "children": [{
                        "children": [{
                            "name": "__test_layer_external_wms"
                        }],
                        "mixed": True,
                        "name": "__test_layer_group_2"
                    }, {
                        "children": [{
                            "name": "__test_layer_internal_wms"
                        }],
                        "mixed": True,
                        "name": "__test_layer_group_6"
                    }],
                    "mixed": True,
                    "name": "__test_layer_group_8"
                }],
                "name": "__test_theme"
            }]
        )
