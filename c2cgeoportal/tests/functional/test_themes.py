# -*- coding: utf-8 -*-

# Copyright (c) 2013-2016, Camptocamp SA
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
            Theme, LayerGroup, Functionality, Interface, \
            LayerV1, ServerOGC, LayerWMS, LayerWMTS, \
            UIMetadata, WMTSDimension

        main = Interface(name=u"main")
        mobile = Interface(name=u"mobile")
        min_levels = Interface(name=u"min_levels")

        layer_v1 = LayerV1(name=u"__test_layer_v1", public=True)
        layer_v1.interfaces = [main]
        layer_v1.ui_metadatas = [UIMetadata("test", "v1")]

        server_ogc_internal = ServerOGC(name="__test_server_ogc_internal", type="mapserver", image_type="image/jpeg")
        server_ogc_external = ServerOGC(name="__test_server_ogc_external", url="http://wms.geo.admin.ch/", image_type="image/jpeg")

        layer_internal_wms = LayerWMS(name=u"__test_layer_internal_wms", public=True)
        layer_internal_wms.layer = "__test_layer_internal_wms"
        layer_internal_wms.interfaces = [main, min_levels]
        layer_internal_wms.ui_metadatas = [UIMetadata("test", "internal_wms")]
        layer_internal_wms.server_ogc = server_ogc_internal

        layer_external_wms = LayerWMS(name=u"__test_layer_external_wms", layer="ch.swisstopo.dreiecksvermaschung", public=True)
        layer_external_wms.interfaces = [main]
        layer_external_wms.ui_metadatas = [UIMetadata("test", "external_wms")]
        layer_external_wms.server_ogc = server_ogc_external

        layer_wmts = LayerWMTS(name=u"__test_layer_wmts", public=True)
        layer_wmts.interfaces = [main, mobile]
        layer_wmts.ui_metadatas = [UIMetadata("test", "wmts")]
        layer_wmts.dimensions = [WMTSDimension("year", "2015")]

        layer_group_1 = LayerGroup(name=u"__test_layer_group_1")
        layer_group_1.children = [layer_v1, layer_internal_wms, layer_external_wms, layer_wmts]
        layer_group_1.ui_metadatas = [UIMetadata("test", "group_1")]

        layer_group_2 = LayerGroup(name=u"__test_layer_group_2")
        layer_group_2.children = [layer_wmts, layer_internal_wms, layer_external_wms]

        layer_group_3 = LayerGroup(name=u"__test_layer_group_3")
        layer_group_3.children = [layer_wmts, layer_internal_wms, layer_external_wms]

        layer_group_4 = LayerGroup(name=u"__test_layer_group_4")
        layer_group_4.children = [layer_group_2]

        theme = Theme(name=u"__test_theme")
        theme.interfaces = [main, mobile]
        theme.ui_metadatas = [UIMetadata("test", "theme")]
        theme.children = [
            layer_group_1, layer_group_2
        ]
        theme_layer = Theme(name=u"__test_theme_layer")
        theme_layer.interfaces = [min_levels]
        theme_layer.children = [
            layer_internal_wms
        ]

        functionality1 = Functionality(name=u"test_name", value=u"test_value_1")
        functionality2 = Functionality(name=u"test_name", value=u"test_value_2")
        theme.functionalities = [functionality1, functionality2]

        DBSession.add_all([theme, theme_layer])

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

    def _only_name(self, item, attribute="name"):
        result = {}

        if attribute in item:
            result[attribute] = item[attribute]

        if "children" in item:
            result["children"] = [
                self._only_name(i, attribute) for i in item["children"]
            ]

        return result

    def _get_filtered_errors(self, themes):
        prog = re.compile("^The layer '' \(__test_layer_external_wms\) is not defined in WMS capabilities$")
        return set([e for e in themes["errors"] if prog.match(e) is None])

    def test_version(self):
        entry = self._create_entry_obj()
        themes = entry.themes()
        self.assertEquals(
            [self._only_name(t) for t in themes],
            [{
                "name": "__test_theme",
                "children": [{
                    "name": u"__test_layer_group_1",
                    "children": [{
                        "name": u"__test_layer_v1"
                    }]
                }]
            }]
        )

        entry = self._create_entry_obj(params={
            "version": "2",
            "catalogue": "true",
        })
        themes = entry.themes()
        self.assertEquals(self._get_filtered_errors(themes), set())
        self.assertEquals(
            [self._only_name(t) for t in themes["themes"]],
            [{
                "name": u"__test_theme",
                "children": [{
                    "name": u"__test_layer_group_1",
                    # order is important
                    "children": [{
                        "name": u"__test_layer_internal_wms"
                    }, {
                        "name": u"__test_layer_external_wms"
                    }, {
                        "name": u"__test_layer_wmts"
                    }]
                }, {
                    "name": u"__test_layer_group_2",
                    # order is important
                    "children": [{
                        "name": u"__test_layer_wmts"
                    }, {
                        "name": u"__test_layer_internal_wms"
                    }, {
                        "name": u"__test_layer_external_wms"
                    }]
                }]
            }]
        )

    def test_group(self):
        entry = self._create_entry_obj(params={
            "version": "2",
            "group": "__test_layer_group_3",
            "catalogue": "true",
        })
        themes = entry.themes()
        self.assertEquals(self._get_filtered_errors(themes), set())
        self.assertEquals(
            self._only_name(themes["group"]),
            {
                "name": u"__test_layer_group_3",
                # order is important
                "children": [{
                    "name": u"__test_layer_wmts"
                }, {
                    "name": u"__test_layer_internal_wms"
                }, {
                    "name": u"__test_layer_external_wms"
                }]
            }
        )

        entry = self._create_entry_obj(params={
            "version": "2",
            "group": "__test_layer_group_4",
            "catalogue": "true",
        })
        themes = entry.themes()
        self.assertEquals(self._get_filtered_errors(themes), set())
        self.assertEquals(
            self._only_name(themes["group"]),
            {
                "name": u"__test_layer_group_4",
                "children": [{
                    "name": u"__test_layer_group_2",
                    # order is important
                    "children": [{
                        "name": u"__test_layer_wmts"
                    }, {
                        "name": u"__test_layer_internal_wms"
                    }, {
                        "name": u"__test_layer_external_wms"
                    }]
                }]
            }
        )

    def test_group_update(self):
        from c2cgeoportal.models import DBSession, LayerGroup
        layer_group_3 = DBSession.query(LayerGroup).filter(LayerGroup.name == u"__test_layer_group_3").one()
        layer_group_3.children = layer_group_3.children[:-1]
        transaction.commit()

        entry = self._create_entry_obj(params={
            "version": "2",
            "group": "__test_layer_group_3",
            "catalogue": "true",
        })
        themes = entry.themes()
        self.assertEquals(self._get_filtered_errors(themes), set())
        self.assertEquals(
            self._only_name(themes["group"]),
            {
                "name": u"__test_layer_group_3",
                # order is important
                "children": [{
                    "name": u"__test_layer_wmts"
                }, {
                    "name": u"__test_layer_internal_wms"
                }]
            }
        )

    @attr(min_levels=True)
    def test_min_levels(self):
        entry = self._create_entry_obj(params={
            "version": "2",
            "interface": "min_levels",
        })
        themes = entry.themes()
        self.assertEquals(self._get_filtered_errors(themes), set([
            u"The Layer '__test_layer_internal_wms' cannot be directly in the theme '__test_theme_layer' (0/1)."
        ]))

        entry = self._create_entry_obj(params={
            "version": "2",
            "min_levels": "2",
        })
        themes = entry.themes()
        self.assertEquals(self._get_filtered_errors(themes), set([
            u"The Layer '__test_theme/__test_layer_group_1/__test_layer_internal_wms' is under indented (1/2).",
            u"The Layer '__test_theme/__test_layer_group_1/__test_layer_wmts' is under indented (1/2).",
            u"The Layer '__test_theme/__test_layer_group_2/__test_layer_external_wms' is under indented (1/2).",
            u"The Layer '__test_theme/__test_layer_group_2/__test_layer_internal_wms' is under indented (1/2).",
            u"The Layer '__test_theme/__test_layer_group_1/__test_layer_external_wms' is under indented (1/2).",
            u"The Layer '__test_theme/__test_layer_group_2/__test_layer_wmts' is under indented (1/2).",
        ]))

    def test_theme_layer(self):
        entry = self._create_entry_obj(params={
            "version": "2",
            "interface": "min_levels",
            "min_levels": "0",
        })
        themes = entry.themes()
        self.assertEquals(self._get_filtered_errors(themes), set())
        self.assertEquals(
            [self._only_name(t) for t in themes["themes"]],
            [{
                "name": u"__test_theme_layer",
                "children": [{
                    "name": u"__test_layer_internal_wms",
                }]
            }]
        )

    def test_catalogue(self):
        entry = self._create_entry_obj(params={
            "version": "2",
        })
        themes = entry.themes()

        self.assertEquals(self._get_filtered_errors(themes), set([]))

        self.assertEquals(
            [self._only_name(t) for t in themes["themes"]],
            [{
                "name": u"__test_theme",
                "children": [{
                    "name": u"__test_layer_group_1",
                    "children": [{
                        "name": u"__test_layer_internal_wms"
                    }, {
                        "name": u"__test_layer_external_wms"
                    }, {
                        "name": u"__test_layer_wmts"
                    }]
                }, {
                    "name": u"__test_layer_group_2",
                    "children": [{
                        "name": u"__test_layer_wmts"
                    }, {
                        "name": u"__test_layer_internal_wms"
                    }, {
                        "name": u"__test_layer_external_wms"
                    }]
                }]
            }]
        )

        self.assertEquals(
            [self._only_name(t, "mixed") for t in themes["themes"]],
            [{
                "children": [{
                    "children": [{}, {}, {}],
                    "mixed": True
                }, {
                    "children": [{}, {}, {}],
                    "mixed": True}
                ]
            }]
        )

        entry = self._create_entry_obj(params={
            "version": "2",
            "catalogue": "true",
        })
        themes = entry.themes()
        self.assertEquals(self._get_filtered_errors(themes), set())

    def test_interface(self):
        entry = self._create_entry_obj(params={
            "version": "2",
            "interface": "mobile",
            "catalogue": "true",
        })
        themes = entry.themes()
        self.assertEquals(self._get_filtered_errors(themes), set())
        self.assertEquals(
            [self._only_name(t) for t in themes["themes"]],
            [{
                "name": u"__test_theme",
                "children": [{
                    "name": u"__test_layer_group_1",
                    "children": [{
                        "name": u"__test_layer_wmts"
                    }]
                }, {
                    "name": u"__test_layer_group_2",
                    "children": [{
                        "name": u"__test_layer_wmts"
                    }]
                }]
            }]
        )

    def test_metadata(self):
        entry = self._create_entry_obj(params={
            "version": "2",
            "catalogue": "true",
        })
        themes = entry.themes()
        self.assertEquals(self._get_filtered_errors(themes), set())
        self.assertEquals(
            [self._only_name(t, "metadata") for t in themes["themes"]],
            [{
                "metadata": {
                    u"test": u"theme",
                },
                "children": [{
                    "metadata": {
                        u"test": u"group_1",
                    },
                    # order is important
                    "children": [{
                        "metadata": {
                            u"test": u"internal_wms",
                        }
                    }, {
                        "metadata": {
                            u"test": u"external_wms",
                        }
                    }, {
                        "metadata": {
                            u"test": u"wmts",
                        }
                    }]
                }, {
                    "metadata": {},
                    # order is important
                    "children": [{
                        "metadata": {
                            u"test": u"wmts",
                        }
                    }, {
                        "metadata": {
                            u"test": u"internal_wms",
                        }
                    }, {
                        "metadata": {
                            u"test": u"external_wms",
                        }
                    }]
                }]
            }]
        )

    def test_server_ogc(self):
        entry = self._create_entry_obj(params={
            "version": "2",
            "catalogue": "true",
        })
        themes = entry.themes()
        self.assertEquals(self._get_filtered_errors(themes), set())
        print(themes)
        self.assertEquals(
            themes["serversOGC"], {
                "__test_server_ogc_internal": {
                    "wfsSupport": False,
                    "url": "http://localhost/cgi-bin/mapserv?map=/home/travis/build/camptocamp/c2cgeoportal/c2cgeoportal/tests/functional/c2cgeoportal_test.map&",
                    "isSingleTile": False,
                    "auth": None,
                    "urlWfs": "http://localhost/cgi-bin/mapserv?map=/home/travis/build/camptocamp/c2cgeoportal/c2cgeoportal/tests/functional/c2cgeoportal_test.map&",
                    "type": "mapserver",
                    "imageType": "image/jpeg",
                },
                "source for image/jpeg": {
                    "wfsSupport": True,
                    "url": "http://localhost/cgi-bin/mapserv?map=/home/travis/build/camptocamp/c2cgeoportal/c2cgeoportal/tests/functional/c2cgeoportal_test.map&",
                    "isSingleTile": False,
                    "auth": "main",
                    "urlWfs": "http://localhost/cgi-bin/mapserv?map=/home/travis/build/camptocamp/c2cgeoportal/c2cgeoportal/tests/functional/c2cgeoportal_test.map&",
                    "type": "mapserver",
                    "imageType": "image/jpeg",
                },
                "__test_server_ogc_external": {
                    "wfsSupport": False,
                    "url": "http://wms.geo.admin.ch/",
                    "isSingleTile": False,
                    "auth": None,
                    "urlWfs": "http://wms.geo.admin.ch/",
                    "type": "mapserver",
                    "imageType": "image/jpeg",
                },
                "source for image/png": {
                    "wfsSupport": True,
                    "url": "http://localhost/cgi-bin/mapserv?map=/home/travis/build/camptocamp/c2cgeoportal/c2cgeoportal/tests/functional/c2cgeoportal_test.map&",
                    "isSingleTile": False,
                    "auth": "main",
                    "urlWfs": "http://localhost/cgi-bin/mapserv?map=/home/travis/build/camptocamp/c2cgeoportal/c2cgeoportal/tests/functional/c2cgeoportal_test.map&",
                    "type": "mapserver",
                    "imageType": "image/png",
                }
            },
        )
        self.assertEquals(
            [self._only_name(t, "serverOGC") for t in themes["themes"]],
            [{
                "children": [{
                    # order is important
                    "children": [{
                        "serverOGC": "__test_server_ogc_internal",
                    }, {
                        "serverOGC": "__test_server_ogc_external",
                    }, {
                    }]
                }, {
                    # order is important
                    "children": [{
                    }, {
                        "serverOGC": "__test_server_ogc_internal",
                    }, {
                        "serverOGC": "__test_server_ogc_external",
                    }]
                }]
            }]
        )

    def test_dimensions(self):
        entry = self._create_entry_obj(params={
            "version": "2",
            "group": "__test_layer_group_3",
            "catalogue": "true",
        })
        themes = entry.themes()
        self.assertEquals(self._get_filtered_errors(themes), set())
        self.assertEquals(
            self._only_name(themes["group"], "dimensions"),
            {
                # order is important
                "children": [{
                    "dimensions": {u"year": u"2015"}
                }, {
                }, {
                }]
            }
        )

    def test_background(self):
        entry = self._create_entry_obj(params={
            "version": "2",
            "background": "__test_layer_group_3",
            "set": "background",
        })
        themes = entry.themes()
        self.assertEquals(self._get_filtered_errors(themes), set())
        self.assertEquals(
            [self._only_name(e) for e in themes["background_layers"]],
            # order is important
            [{
                "name": u"__test_layer_wmts"
            }, {
                "name": u"__test_layer_internal_wms"
            }, {
                "name": u"__test_layer_external_wms"
            }]
        )
