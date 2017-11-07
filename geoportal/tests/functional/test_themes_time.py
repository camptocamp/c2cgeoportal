# -*- coding: utf-8 -*-

# Copyright (c) 2013-2017, Camptocamp SA
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
import typing
import transaction

from unittest import TestCase

from sqlalchemy import Column
import sqlalchemy.ext.declarative
from sqlalchemy.types import Integer, Unicode, DateTime
from geoalchemy2 import Geometry
from pyramid import testing

from tests.functional import (  # noqa
    teardown_common as teardown_module,
    setup_common as setup_module,
    mapserv_url, create_dummy_request, create_default_ogcserver,
)

import logging
log = logging.getLogger(__name__)

Base: typing.Any = sqlalchemy.ext.declarative.declarative_base()


class PointTest(Base):
    __tablename__ = "testpointtime"
    __table_args__ = {"schema": "main"}
    id = Column(Integer, primary_key=True)
    the_geom = Column(Geometry("POINT", srid=21781))
    name = Column(Unicode)
    time = Column(DateTime)


class TestThemesTimeView(TestCase):

    def setup_method(self, _):
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import Theme, LayerGroup, Interface, LayerWMS, LayerWMTS

        PointTest.__table__.create(bind=DBSession.bind, checkfirst=True)

        main = Interface(name="desktop")
        ogc_server, _ = create_default_ogcserver()

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

        layer_wms_group = LayerWMS(name="__test_layer_time_group", public=True)
        layer_wms_group.layer = "test_wmstimegroup"
        layer_wms_group.time_mode = "range"
        layer_wms_group.time_widget = "datepicker"
        layer_wms_group.interfaces = [main]
        layer_wms_group.ogc_server = ogc_server

        layer_group_1 = LayerGroup(name="__test_layer_group_1")
        layer_group_1.children = [layer_wms_1, layer_wms_2]

        layer_group_2 = LayerGroup(name="__test_layer_group_2")
        layer_group_2.children = [layer_wms_1]

        layer_group_3 = LayerGroup(name="__test_layer_group_3")
        layer_group_3.children = [layer_wms_1, layer_wms_2, layer_wms_group]

        layer_group_4 = LayerGroup(name="__test_layer_group_4")
        layer_group_4.children = [layer_wms_group]

        layer_group_5 = LayerGroup(name="__test_layer_group_5")
        layer_group_5.children = [layer_wms_1, layer_wms_2]

        layer_group_6 = LayerGroup(name="__test_layer_group_6")
        layer_group_6.children = [layer_wms_1, layer_wms_2, layer_wmts]

        layer_group_7 = LayerGroup(name="__test_layer_group_7")
        layer_group_7.children = [layer_wms_1]

        theme = Theme(name="__test_theme")
        theme.interfaces = [main]
        theme.children = [
            layer_group_1, layer_group_2, layer_group_3, layer_group_4,
            layer_group_5, layer_group_6, layer_group_7,
        ]

        DBSession.add_all([theme])

        transaction.commit()

    def teardown_method(self, _):
        testing.tearDown()

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import TreeItem, Interface, OGCServer

        for item in DBSession.query(TreeItem).all():
            DBSession.delete(item)
        DBSession.query(Interface).filter(
            Interface.name == "main"
        ).delete()
        DBSession.query(OGCServer).delete()

        transaction.commit()
        PointTest.__table__.drop(bind=DBSession.bind, checkfirst=True)

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

    def _only(self, item, attributes=None):
        if attributes is None:
            attributes = ["name", "time"]
        result = {}

        for attribute in attributes:
            if attribute in item:
                result[attribute] = item[attribute]

        if "children" in item:
            result["children"] = [
                self._only(i, attributes) for i in item["children"]
            ]

        return result

    @staticmethod
    def _get_filtered_errors(themes):
        errors = themes["errors"]
        regex = re.compile(r"The (GeoMapFish|WMS) layer name '[a-z0-9_.]*', cannot be two times in the same block \(first level group\).")
        errors = [e for e in errors if not regex.match(e)]
        return set(errors)

    def test_time(self):
        entry = self._create_entry_obj(params={
            "version": "2",
        })
        themes = entry.themes()
        self.assertEqual(self._get_filtered_errors(themes), set([
            "Error while handling time for layer '__test_layer_time_group': Could not mix time mode 'range' and 'value'"
        ]))
        self.assertEqual(
            [self._only(t) for t in themes["themes"]],
            [{
                "name": "__test_theme",
                "children": [{
                    "name": "__test_layer_group_1",
                    "time": {
                        "maxDefValue": None,
                        "interval": (1, 0, 0, 0),
                        "maxValue": "2020-01-01T00:00:00Z",
                        "minDefValue": "2000-01-01T00:00:00Z",
                        "minValue": "2000-01-01T00:00:00Z",
                        "mode": "value",
                        "resolution": "year",
                        "widget": "slider"
                    },
                    "children": [{
                        "name": "__test_layer_time_1",
                    }, {
                        "name": "__test_layer_time_2",
                    }]
                }, {
                    "name": "__test_layer_group_2",
                    "children": [{
                        "name": "__test_layer_time_1",
                        "time": {
                            "maxDefValue": None,
                            "interval": (1, 0, 0, 0),
                            "maxValue": "2010-01-01T00:00:00Z",
                            "minDefValue": "2000-01-01T00:00:00Z",
                            "minValue": "2000-01-01T00:00:00Z",
                            "mode": "value",
                            "resolution": "year",
                            "widget": "slider"
                        },
                    }]
                }, {
                    "name": "__test_layer_group_3",
                    "time": {
                        "maxDefValue": None,
                        "interval": (1, 0, 0, 0),
                        "maxValue": "2020-01-01T00:00:00Z",
                        "minDefValue": "2000-01-01T00:00:00Z",
                        "minValue": "2000-01-01T00:00:00Z",
                        "mode": "value",
                        "resolution": "year",
                        "widget": "slider"
                    },
                    "children": [{
                        "name": "__test_layer_time_1",
                    }, {
                        "name": "__test_layer_time_2",
                    }, {
                        "name": "__test_layer_time_group",
                    }]
                }, {
                    "name": "__test_layer_group_4",
                    "children": [{
                        "name": "__test_layer_time_group",
                        "time": {
                            "maxDefValue": None,
                            "interval": (1, 0, 0, 0),
                            "maxValue": "2020-01-01T00:00:00Z",
                            "minDefValue": "2000-01-01T00:00:00Z",
                            "minValue": "2000-01-01T00:00:00Z",
                            "mode": "range",
                            "resolution": "year",
                            "widget": "datepicker"
                        },
                    }]
                }, {
                    "name": "__test_layer_group_5",
                    "children": [{
                        "name": "__test_layer_time_1",
                    }, {
                        "name": "__test_layer_time_2",
                    }],
                    "time": {
                        "maxDefValue": None,
                        "interval": (1, 0, 0, 0),
                        "maxValue": "2020-01-01T00:00:00Z",
                        "minDefValue": "2000-01-01T00:00:00Z",
                        "minValue": "2000-01-01T00:00:00Z",
                        "mode": "value",
                        "resolution": "year",
                        "widget": "slider"
                    },
                }, {
                    "name": "__test_layer_group_6",
                    "children": [{
                        "name": "__test_layer_time_1",
                        "time": {
                            "maxDefValue": None,
                            "interval": (1, 0, 0, 0),
                            "maxValue": "2010-01-01T00:00:00Z",
                            "minDefValue": "2000-01-01T00:00:00Z",
                            "minValue": "2000-01-01T00:00:00Z",
                            "mode": "value",
                            "resolution": "year",
                            "widget": "slider"
                        },
                    }, {
                        "name": "__test_layer_time_2",
                        "time": {
                            "maxDefValue": None,
                            "interval": (1, 0, 0, 0),
                            "maxValue": "2020-01-01T00:00:00Z",
                            "minDefValue": "2015-01-01T00:00:00Z",
                            "minValue": "2015-01-01T00:00:00Z",
                            "mode": "value",
                            "resolution": "year",
                            "widget": "slider"
                        },
                    }, {
                        "name": "__test_layer_wmts",
                    }]
                }, {
                    "name": "__test_layer_group_7",
                    "children": [{
                        "name": "__test_layer_time_1",
                        "time": {
                            "maxDefValue": None,
                            "interval": (1, 0, 0, 0),
                            "maxValue": "2010-01-01T00:00:00Z",
                            "minDefValue": "2000-01-01T00:00:00Z",
                            "minValue": "2000-01-01T00:00:00Z",
                            "mode": "value",
                            "resolution": "year",
                            "widget": "slider"
                        },
                    }]
                }]
            }]
        )
