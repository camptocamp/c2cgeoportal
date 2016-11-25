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
    mapserv_url, host, create_dummy_request, create_default_ogcserver,
)

import logging
log = logging.getLogger(__name__)


@attr(functional=True)
class TestThemesViewMetadata(TestCase):

    def setUp(self):  # noqa
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None

        from c2cgeoportal.models import DBSession, \
            Theme, LayerGroup, Interface, LayerWMS, Metadata

        desktop = Interface(name=u"desktop")

        ogc_server_internal, _ = create_default_ogcserver()

        layer_wms = LayerWMS(name=u"__test_layer_internal_wms", public=True)
        layer_wms.layer = "__test_layer_internal_wms"
        layer_wms.ogc_server = ogc_server_internal
        layer_wms.interfaces = [desktop]
        layer_wms.metadatas = [
            Metadata("string", "string"),
            Metadata("list", "1, 2, a"),
            Metadata("boolean", "y"),
            Metadata("boolean2", "no"),
            Metadata("boolean3", "Hello"),
            Metadata("integer", "1"),
            Metadata("float", "5.5"),
            Metadata("json", '{"test": 123}'),
            Metadata("json_wrong", '{"test": 123'),
            Metadata("date", "Sep 25 2003"),
            Metadata("time", "10:36:28"),
            Metadata("datetime", "Sep 25 10:36:28 BRST 2003"),
            Metadata("date2", "Sep 25 10:36:28 BRST 2003"),
            Metadata("time2", "Sep 25 10:36:28 BRST 2003"),
            Metadata("datetime2", "Hello"),
            Metadata("url1", "http://example.com/hi?a=b#c"),
            Metadata("url2", "static:///path/icon.png"),
            Metadata("url3", "static://static/path/icon.png"),
            Metadata("url4", "static://cgxp/path/icon.png"),
            Metadata("url5", "static://project:static/path/icon.png"),
            Metadata("url6", "static://project:cgxp/path/icon.png"),
            Metadata("url7", "config://server"),
            Metadata("url8", "config://server/index.html"),
            Metadata("url9", "/dummy/static/icon.png"),
            Metadata("url10", "dummy/static/icon.png"),
            Metadata("url11", "https:///static/icon.png"),
            Metadata("url12", "static://test"),
            Metadata("url13", "static://test/"),
            Metadata("url14", "config:///static/icon.png"),
            Metadata("url15", "config://unknown_server"),
            Metadata("url16", "https://"),
            Metadata("url17", "https:///"),
            Metadata("url18", "https:///static"),
            Metadata("url19", ""),
            Metadata("url20", "/"),
            Metadata("unknown", "Hello"),
        ]

        layer_group = LayerGroup(name=u"__test_layer_group")
        layer_group.children = [layer_wms]

        theme = Theme(name=u"__test_theme")
        theme.interfaces = [desktop]
        theme.children = [layer_group]

        DBSession.add(theme)

        transaction.commit()

    @staticmethod
    def tearDown():  # noqa
        testing.tearDown()

        from c2cgeoportal.models import DBSession, Layer, \
            Theme, LayerGroup, Interface, Metadata

        for t in DBSession.query(Metadata).all():
            DBSession.delete(t)
        for layer in DBSession.query(Layer).all():
            DBSession.delete(layer)
        for layergroup in DBSession.query(LayerGroup).all():
            DBSession.delete(layergroup)
        for t in DBSession.query(Theme).all():
            DBSession.delete(t)
        DBSession.query(Interface).filter(
            Interface.name == "desktop"
        ).delete()

        transaction.commit()

    def _only_name(self, item, attribute="name"):
        result = {}

        if attribute in item:
            result[attribute] = item[attribute]

        if "children" in item:
            result["children"] = [
                self._only_name(i, attribute) for i in item["children"]
            ]

        return result

    @staticmethod
    def _get_filtered_errors(themes):
        errors = themes["errors"]
        regex = re.compile(r"The (GeoMapFish|WMS) layer name '[a-z0-9_.]*', can't be two times in the same block \(first level group\).")
        errors = [e for e in errors if not regex.match(e)]
        return set(errors)

    def test_metadata(self):
        from c2cgeoportal.views.entry import Entry

        types = [
            {"name": "string", "type": "string"},
            {"name": "list", "type": "list"},
            {"name": "boolean", "type": "boolean"},
            {"name": "boolean2", "type": "boolean"},
            {"name": "boolean3", "type": "boolean"},
            {"name": "integer", "type": "integer"},
            {"name": "float", "type": "float"},
            {"name": "json", "type": "json"},
            {"name": "json_wrong", "type": "json"},
            {"name": "date", "type": "date"},
            {"name": "time", "type": "time"},
            {"name": "datetime", "type": "datetime"},
            {"name": "date2", "type": "date"},
            {"name": "time2", "type": "time"},
            {"name": "datetime2", "type": "datetime"},
            {"name": "unknown", "type": "unknown"},
        ]
        types += [{"name": "url{}".format(n), "type": "url"} for n in range(1, 21)]

        request = create_dummy_request(additional_settings={
            "package": "tests",
            "servers": {
                "server": "http://example.com/test"
            },
            "admin_interface": {"available_metadata": types}
        })

        def route_url(url, **kargs):
            return "http://mapserver.org/"
        request.route_url = route_url

        def static_url(url, **kargs):
            return "http://dummy.org/{}".format(url)
        request.static_url = static_url
        request.params = {
            "version": "2",
            "interface": "desktop",
        }
        entry = Entry(request)

        themes = entry.themes()
        self.assertEquals(self._get_filtered_errors(themes), set([
            "The boolean attribute 'boolean3'='hello' is not in [yes, y, on, 1, true, no, n, off, 0, false].",
            "Unable to parse the attribute 'json_wrong'='{\"test\": 123' with the type 'json', error:\n'set' object has no attribute 'append'",
            "The date attribute 'date2'='Sep 25 10:36:28 BRST 2003' shouldn't have any time",
            "The time attribute 'time2'='Sep 25 10:36:28 BRST 2003' shouldn't have any date",
            "Unable to parse the attribute 'datetime2'='Hello' with the type 'datetime', error:\nUnknown string format",
            "The attribute 'url11'='https:///static/icon.png' isn't a valid URL.",
            "The attribute 'url12'='static://test' can't have an empty path.",
            "The attribute 'url13'='static://test/' can't have an empty path.",
            "The attribute 'url14'='config:///static/icon.png' can't have an empty netloc.",
            "The server 'unknown_server' isn't found in the config",
            "The attribute 'url16'='https://' isn't a valid URL.",
            "The attribute 'url17'='https:///' isn't a valid URL.",
            "The attribute 'url18'='https:///static' isn't a valid URL.",
            "The attribute 'url19'='' isn't an URL.",
            "The attribute 'url20'='/' isn't an URL.",
            "Unknown type 'unknown'.",
        ]))
        self.assertEquals(
            [self._only_name(t, "metadata") for t in themes["themes"]],
            [{
                "metadata": {},
                "children": [{
                    "metadata": {},
                    "children": [{
                        "metadata": {
                            u"string": u"string",
                            u"list": [u"1", u"2", u"a"],
                            u"boolean": True,
                            u"boolean2": False,
                            u"integer": 1,
                            u"float": 5.5,
                            u"json": {u"test": 123},
                            u"date": "2003-09-25",
                            u"time": "10:36:28",
                            u"datetime": "2003-09-25T10:36:28",
                            u"url1": u"http://example.com/hi?a=b#c",
                            u"url2": "http://dummy.org/tests:static/path/icon.png",
                            u"url3": "http://dummy.org/tests:static/path/icon.png",
                            u"url4": "http://dummy.org/tests:cgxp/path/icon.png",
                            u"url5": "http://dummy.org/project:static/path/icon.png",
                            u"url6": "http://dummy.org/project:cgxp/path/icon.png",
                            u"url7": "http://example.com/test/",
                            u"url8": u"http://example.com/test/index.html",
                            u"url9": u"/dummy/static/icon.png",
                            u"url10": u"dummy/static/icon.png",
                        }
                    }]
                }]
            }]
        )
