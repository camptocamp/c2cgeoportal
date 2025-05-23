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
import typing
from unittest import TestCase

import sqlalchemy.ext.declarative
import transaction
from geoalchemy2 import Geometry
from pyramid import testing
from sqlalchemy import Column
from sqlalchemy.types import DateTime, Integer, Unicode

from tests.functional import create_default_ogcserver, create_dummy_request, mapserv_url
from tests.functional import setup_common as setup_module  # noqa
from tests.functional import teardown_common as teardown_module  # noqa

Base: typing.Any = sqlalchemy.ext.declarative.declarative_base()


class PointTest(Base):  # type: ignore
    __tablename__ = "testpointtime"
    __table_args__ = {"schema": "geodata"}
    id = Column(Integer, primary_key=True)
    geom = Column(Geometry("POINT", srid=21781))
    name = Column(Unicode)
    time = Column(DateTime)


class TestThemesTimeView(TestCase):
    def setup_method(self, _) -> None:
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import (
            Interface,
            LayerGroup,
            LayerWMS,
            LayerWMTS,
            Theme,
        )

        DBSession.query(PointTest).delete()

        main = Interface(name="desktop")
        ogc_server = create_default_ogcserver(DBSession)

        layer_wms_1 = LayerWMS(name="__test_layer_time_1", public=True)
        layer_wms_1.layer = "test_wmstime"
        layer_wms_1.time_mode = "value"
        layer_wms_1.interfaces = [main]
        layer_wms_1.ogc_server = ogc_server

        layer_wms_2 = LayerWMS(name="__test_layer_time_2", public=True)
        layer_wms_2.layer = "test_wmstime2"
        layer_wms_2.time_mode = "value"
        layer_wms_2.interfaces = [main]
        layer_wms_2.ogc_server = ogc_server

        layer_wmts = LayerWMTS(name="__test_layer_wmts", public=True)
        layer_wmts.url = "http://example.com/1.0.0/WMTSCapabilities.xml"
        layer_wmts.layer = "map"
        layer_wmts.interfaces = [main]

        layer_wms_group_1 = LayerWMS(name="__test_layer_time_group_1", public=True)
        layer_wms_group_1.layer = "test_wmstimegroup"
        layer_wms_group_1.time_mode = "range"
        layer_wms_group_1.time_widget = "datepicker"
        layer_wms_group_1.interfaces = [main]
        layer_wms_group_1.ogc_server = ogc_server

        layer_wms_group_2 = LayerWMS(name="__test_layer_time_group_2", public=True)
        layer_wms_group_2.layer = "test_wmstimegroup"
        layer_wms_group_2.time_mode = "value"
        layer_wms_group_2.interfaces = [main]
        layer_wms_group_2.ogc_server = ogc_server

        layer_wms_no_time = LayerWMS(name="__test_layer_without_time_info", public=True)
        layer_wms_no_time.layer = "test_wmsfeatures"
        layer_wms_no_time.time_mode = "value"
        layer_wms_no_time.interfaces = [main]
        layer_wms_no_time.ogc_server = ogc_server

        # Expect merge of times
        layer_group_1 = LayerGroup(name="__test_layer_group_1")
        layer_group_1.children = [layer_wms_1, layer_wms_2]

        # Expect time from layer.
        layer_group_2 = LayerGroup(name="__test_layer_group_2")
        layer_group_2.children = [layer_wms_1]

        # Expect merge of wms 1 and 2, layer_wms_group_1 excluded and in errors as its mode don't match.
        layer_group_3 = LayerGroup(name="__test_layer_group_3")
        layer_group_3.children = [layer_wms_1, layer_wms_2, layer_wms_group_1]

        # Expect time from layers in wms layer group
        layer_group_4 = LayerGroup(name="__test_layer_group_4")
        layer_group_4.children = [layer_wms_group_1]

        # Expect merge of wms 1 and 2 and group.
        layer_group_5 = LayerGroup(name="__test_layer_group_5")
        layer_group_5.children = [layer_wms_1, layer_wms_2, layer_wms_group_2]

        # Expect individual layers
        layer_group_6 = LayerGroup(name="__test_layer_group_6")
        layer_group_6.children = [layer_wms_1, layer_wms_2, layer_wmts]

        # Expect layer_wms_no_time excluded and in errors as it has no time info
        layer_group_7 = LayerGroup(name="__test_layer_group_7")
        layer_group_7.children = [layer_wms_1, layer_wms_no_time]

        theme = Theme(name="__test_theme")
        theme.interfaces = [main]
        theme.children = [
            layer_group_1,
            layer_group_2,
            layer_group_3,
            layer_group_4,
            layer_group_5,
            layer_group_6,
            layer_group_7,
        ]

        DBSession.add_all([theme])

        transaction.commit()

    def teardown_method(self, _) -> None:
        testing.tearDown()

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import Interface, OGCServer, TreeItem

        for item in DBSession.query(TreeItem).all():
            DBSession.delete(item)
        DBSession.query(Interface).filter(Interface.name == "main").delete()
        DBSession.query(OGCServer).delete()

        transaction.commit()
        DBSession.query(PointTest).delete()

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

    def _only(self, item, attributes=None):
        if attributes is None:
            attributes = ["name", "time"]
        result = {}

        for attribute in attributes:
            if attribute in item:
                result[attribute] = item[attribute]

        if "children" in item:
            result["children"] = [self._only(i, attributes) for i in item["children"]]

        return result

    @staticmethod
    def _get_filtered_errors(themes):
        errors = themes["errors"]
        regex = re.compile(
            r"The (GeoMapFish|WMS) layer name '[a-z0-9_.]*', cannot be two times in the same block \(first level group\).",
        )
        errors = [e for e in errors if not regex.match(e)]
        return set(errors)

    def test_time(self) -> None:
        theme_view = self._create_theme_obj()
        themes = theme_view.themes()
        assert set(themes["errors"]) == {
            "Error while handling time for layer '__test_layer_time_group_1': Could not mix time mode 'range' and 'value'",
            "Error: time layer '__test_layer_without_time_info' has no time information in capabilities",
        }
        assert [self._only(t) for t in themes["themes"]] == [
            {
                "name": "__test_theme",
                "children": [
                    {
                        "name": "__test_layer_group_1",
                        "time": {
                            "maxDefValue": None,
                            "interval": (1, 0, 0, 0),
                            "maxValue": "2020-01-01T00:00:00Z",
                            "minDefValue": "2000-01-01T00:00:00Z",
                            "minValue": "2000-01-01T00:00:00Z",
                            "mode": "value",
                            "resolution": "year",
                            "widget": "slider",
                        },
                        "children": [{"name": "__test_layer_time_1"}, {"name": "__test_layer_time_2"}],
                    },
                    {
                        "name": "__test_layer_group_2",
                        "children": [
                            {
                                "name": "__test_layer_time_1",
                                "time": {
                                    "maxDefValue": None,
                                    "interval": (1, 0, 0, 0),
                                    "maxValue": "2010-01-01T00:00:00Z",
                                    "minDefValue": "2000-01-01T00:00:00Z",
                                    "minValue": "2000-01-01T00:00:00Z",
                                    "mode": "value",
                                    "resolution": "year",
                                    "widget": "slider",
                                },
                            },
                        ],
                    },
                    {
                        "name": "__test_layer_group_3",
                        "time": {
                            "maxDefValue": None,
                            "interval": (1, 0, 0, 0),
                            "maxValue": "2020-01-01T00:00:00Z",
                            "minDefValue": "2000-01-01T00:00:00Z",
                            "minValue": "2000-01-01T00:00:00Z",
                            "mode": "value",
                            "resolution": "year",
                            "widget": "slider",
                        },
                        "children": [{"name": "__test_layer_time_1"}, {"name": "__test_layer_time_2"}],
                    },
                    {
                        "name": "__test_layer_group_4",
                        "children": [
                            {
                                "name": "__test_layer_time_group_1",
                                "time": {
                                    "maxDefValue": None,
                                    "interval": (1, 0, 0, 0),
                                    "maxValue": "2020-01-01T00:00:00Z",
                                    "minDefValue": "2000-01-01T00:00:00Z",
                                    "minValue": "2000-01-01T00:00:00Z",
                                    "mode": "range",
                                    "resolution": "year",
                                    "widget": "datepicker",
                                },
                            },
                        ],
                    },
                    {
                        "name": "__test_layer_group_5",
                        "time": {
                            "maxDefValue": None,
                            "interval": (1, 0, 0, 0),
                            "maxValue": "2020-01-01T00:00:00Z",
                            "minDefValue": "2000-01-01T00:00:00Z",
                            "minValue": "2000-01-01T00:00:00Z",
                            "mode": "value",
                            "resolution": "year",
                            "widget": "slider",
                        },
                        "children": [
                            {"name": "__test_layer_time_1"},
                            {"name": "__test_layer_time_2"},
                            {"name": "__test_layer_time_group_2"},
                        ],
                    },
                    {
                        "name": "__test_layer_group_6",
                        "children": [
                            {
                                "name": "__test_layer_time_1",
                                "time": {
                                    "maxDefValue": None,
                                    "interval": (1, 0, 0, 0),
                                    "maxValue": "2010-01-01T00:00:00Z",
                                    "minDefValue": "2000-01-01T00:00:00Z",
                                    "minValue": "2000-01-01T00:00:00Z",
                                    "mode": "value",
                                    "resolution": "year",
                                    "widget": "slider",
                                },
                            },
                            {
                                "name": "__test_layer_time_2",
                                "time": {
                                    "maxDefValue": None,
                                    "interval": (1, 0, 0, 0),
                                    "maxValue": "2020-01-01T00:00:00Z",
                                    "minDefValue": "2015-01-01T00:00:00Z",
                                    "minValue": "2015-01-01T00:00:00Z",
                                    "mode": "value",
                                    "resolution": "year",
                                    "widget": "slider",
                                },
                            },
                            {"name": "__test_layer_wmts"},
                        ],
                    },
                    {
                        "name": "__test_layer_group_7",
                        "children": [
                            {
                                "name": "__test_layer_time_1",
                                "time": {
                                    "maxDefValue": None,
                                    "interval": (1, 0, 0, 0),
                                    "maxValue": "2010-01-01T00:00:00Z",
                                    "minDefValue": "2000-01-01T00:00:00Z",
                                    "minValue": "2000-01-01T00:00:00Z",
                                    "mode": "value",
                                    "resolution": "year",
                                    "widget": "slider",
                                },
                            },
                        ],
                    },
                ],
            },
        ]
