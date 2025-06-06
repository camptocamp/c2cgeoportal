# Copyright (c) 2013-2025, Camptocamp SA
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

from tests.functional import create_default_ogcserver, create_dummy_request
from tests.functional import setup_common as setup_module  # noqa
from tests.functional import teardown_common as teardown_module  # noqa


class TestThemesViewMetadata(TestCase):
    def setup_method(self, _) -> None:
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import (
            Interface,
            LayerGroup,
            LayerWMS,
            Metadata,
            Theme,
        )

        desktop = Interface(name="desktop")

        ogc_server_internal = create_default_ogcserver(DBSession)

        layer_wms = LayerWMS(name="__test_layer_internal_wms", public=True)
        layer_wms.layer = "testpoint_unprotected"
        layer_wms.ogc_server = ogc_server_internal
        layer_wms.interfaces = [desktop]
        layer_wms.metadatas = [
            Metadata("string", "string"),
            Metadata("list", "1, 2, a"),
            Metadata("boolean", "y"),
            Metadata("boolean2", "no"),
            Metadata("integer", "1"),
            Metadata("float", "5.5"),
            Metadata("json", '{"test": 123}'),
            Metadata("date", "Sep 25 2003"),
            Metadata("time", "10:36:28"),
            Metadata("datetime", "Sep 25 10:36:28 BRST 2003"),
            Metadata("regex", "valid"),
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
        ]

        layer_wms_errors = LayerWMS(name="__test_layer_internal_wms_errors", public=True)
        layer_wms_errors.layer = "testpoint_unprotected"
        layer_wms_errors.ogc_server = ogc_server_internal
        layer_wms_errors.interfaces = [desktop]
        layer_wms_errors.metadatas = [
            Metadata("boolean3", "Hello"),
            Metadata("json_wrong", '{"test": 123'),
            Metadata("date2", "Sep 25 10:36:28 BRST 2003"),
            Metadata("time2", "Sep 25 10:36:28 BRST 2003"),
            Metadata("datetime2", "Hello"),
            Metadata("regex", "invalid"),
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

        layer_group = LayerGroup(name="__test_layer_group")
        layer_group.children = [layer_wms, layer_wms_errors]

        theme = Theme(name="__test_theme")
        theme.interfaces = [desktop]
        theme.children = [layer_group]

        DBSession.add(theme)

        transaction.commit()

    def teardown_method(self, _) -> None:
        testing.tearDown()

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import Interface, Metadata, TreeItem

        for t in DBSession.query(Metadata).all():
            DBSession.delete(t)
        for item in DBSession.query(TreeItem).all():
            DBSession.delete(item)
        DBSession.query(Interface).filter(Interface.name == "desktop").delete()

        transaction.commit()

    def _only_name(self, item, attribute="name"):
        result = {}

        if attribute in item:
            result[attribute] = item[attribute]

        if "children" in item:
            result["children"] = [self._only_name(i, attribute) for i in item["children"]]

        return result

    @staticmethod
    def _get_filtered_errors(themes):
        errors = themes["errors"]
        regex1 = re.compile(
            r"The (GeoMapFish|WMS) layer name '[a-z0-9_.]*', cannot be two times in the same block \(first level group\).",
        )
        regex2 = re.compile(r"Error \'.*\' on reading DescribeFeatureType from URL .*")
        errors = [
            e
            for e in errors
            if not regex1.match(e)
            and not regex2.match(e)
            and not e.startswith("Unable to get DescribeFeatureType from URL ")
        ]
        return set(errors)

    def test_metadata(self) -> None:
        from c2cgeoportal_geoportal.views.theme import Theme

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
            {"name": "regex", "type": "regex", "regex": "^valid$"},
            {"name": "unknown", "type": "unknown"},
        ]
        types += [{"name": f"url{n}", "type": "url"} for n in range(1, 21)]

        request = create_dummy_request(
            additional_settings={
                "package": "tests",
                "servers": {"server": "http://example.com/test"},
                "admin_interface": {"available_metadata": types},
            },
        )

        def route_url(url, **kwargs):
            del url
            del kwargs
            return "http://mapserver.org/"

        request.route_url = route_url

        def static_url(url, **kwargs):
            del kwargs
            return f"http://dummy.org/{url}"

        request.static_url = static_url
        request.params = {"interface": "desktop"}
        theme_view = Theme(request)

        themes = theme_view.themes()
        assert set(themes["errors"]) == {
            "The boolean attribute 'boolean3'='hello' is not in [yes, y, on, 1, true, no, n, off, 0, false].",
            "The attribute 'json_wrong'='{\"test\": 123' has an error: Expecting ',' delimiter: line 1 column 13 (char 12)",
            "The date attribute 'date2'='Sep 25 10:36:28 BRST 2003' should not have any time",
            "The time attribute 'time2'='Sep 25 10:36:28 BRST 2003' should not have any date",
            "Unable to parse the attribute 'datetime2'='Hello' with the type 'datetime', error:\nUnknown string format: Hello",
            "The regex attribute 'regex'='invalid' does not match expected pattern '^valid$'.",
            "The attribute 'url11'='https:///static/icon.png' is not a valid URL.",
            "The attribute 'url12'='static://test' cannot have an empty path.",
            "The attribute 'url13'='static://test/' cannot have an empty path.",
            "The attribute 'url14'='config:///static/icon.png' cannot have an empty netloc.",
            "The attribute 'url15': The server 'unknown_server' (config://unknown_server) is not found in the config: [server]",
            "The attribute 'url16'='https://' is not a valid URL.",
            "The attribute 'url17'='https:///' is not a valid URL.",
            "The attribute 'url18'='https:///static' is not a valid URL.",
            "The attribute 'url19'='' is not an URL.",
            "The attribute 'url20'='/' is not an URL.",
            "Unknown type 'unknown'.",
        }
        assert [self._only_name(t, "metadata") for t in themes["themes"]] == [
            {
                "metadata": {},
                "children": [
                    {
                        "metadata": {},
                        "children": [
                            {
                                "metadata": {
                                    "string": "string",
                                    "list": ["1", "2", "a"],
                                    "boolean": True,
                                    "boolean2": False,
                                    "integer": 1,
                                    "float": 5.5,
                                    "json": {"test": 123},
                                    "date": "2003-09-25",
                                    "time": "10:36:28",
                                    "datetime": "2003-09-25T10:36:28",
                                    "regex": "valid",
                                    "url1": "http://example.com/hi?a=b#c",
                                    "url2": "http://dummy.org//etc/geomapfish/static/path/icon.png",
                                    "url3": "http://dummy.org//etc/geomapfish/static/path/icon.png",
                                    "url4": "http://dummy.org/tests_geoportal:cgxp/path/icon.png",
                                    "url5": "http://dummy.org/project:static/path/icon.png",
                                    "url6": "http://dummy.org/project:cgxp/path/icon.png",
                                    "url7": "http://example.com/test",
                                    "url8": "http://example.com/test/index.html",
                                    "url9": "/dummy/static/icon.png",
                                    "url10": "dummy/static/icon.png",
                                },
                            },
                        ],
                    },
                ],
            },
        ]
