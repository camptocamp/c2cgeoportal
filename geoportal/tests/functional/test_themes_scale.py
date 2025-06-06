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

from unittest import TestCase

import transaction
from pyramid import testing

from tests.functional import create_default_ogcserver, create_dummy_request, mapserv_url
from tests.functional import setup_common as setup_module  # noqa
from tests.functional import teardown_common as teardown_module  # noqa


class TestThemesScale(TestCase):
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

        main = Interface(name="desktop")

        ogc_server = create_default_ogcserver(DBSession)

        layer_noscale = LayerWMS(name="__test_layer_noscale", public=True)
        layer_noscale.layer = "test_noscale"
        layer_noscale.interfaces = [main]
        layer_noscale.ogc_server = ogc_server

        layer_minscale = LayerWMS(name="__test_layer_minscale", public=True)
        layer_minscale.layer = "test_minscale"
        layer_minscale.interfaces = [main]
        layer_minscale.ogc_server = ogc_server

        layer_maxscale = LayerWMS(name="__test_layer_maxscale", public=True)
        layer_maxscale.layer = "test_maxscale"
        layer_maxscale.interfaces = [main]
        layer_maxscale.ogc_server = ogc_server

        layer_boothscale = LayerWMS(name="__test_layer_boothscale", public=True)
        layer_boothscale.layer = "test_boothscale"
        layer_boothscale.interfaces = [main]
        layer_boothscale.ogc_server = ogc_server

        layer_metadatascale = LayerWMS(name="__test_layer_metadatascale", public=True)
        layer_metadatascale.layer = "test_boothscale"
        layer_metadatascale.interfaces = [main]
        layer_metadatascale.ogc_server = ogc_server
        layer_metadatascale.metadatas = [Metadata("minResolution", "100"), Metadata("maxResolution", "1000")]

        layer_group = LayerGroup(name="__test_layer_group")
        layer_group.children = [
            layer_noscale,
            layer_minscale,
            layer_maxscale,
            layer_boothscale,
            layer_metadatascale,
        ]

        theme = Theme(name="__test_theme")
        theme.interfaces = [main]
        theme.children = [layer_group]

        DBSession.add_all([theme])

        transaction.commit()

    def teardown_method(self, _) -> None:
        testing.tearDown()

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import (
            Interface,
            Layer,
            LayerGroup,
            OGCServer,
            Theme,
        )

        for layer in DBSession.query(Layer).all():
            DBSession.delete(layer)
        for g in DBSession.query(LayerGroup).all():
            DBSession.delete(g)
        for t in DBSession.query(Theme).all():
            DBSession.delete(t)
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
        request = create_dummy_request(
            additional_settings={
                "admin_interface": {
                    "available_metadata": [
                        {"name": "minResolution", "type": "float"},
                        {"name": "maxResolution", "type": "float"},
                    ],
                },
            },
            **kwargs,
        )
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

    def test_scale(self) -> None:
        theme_view = self._create_theme_obj()
        themes = theme_view.themes()
        assert set(themes["errors"]) == set()
        assert [
            self._only_name(t, ["name", "childLayers", "minResolutionHint", "maxResolutionHint"])
            for t in themes["themes"]
        ] == [
            {
                "name": "__test_theme",
                "children": [
                    {
                        "name": "__test_layer_group",
                        "children": [
                            {
                                "childLayers": [
                                    {
                                        "minResolutionHint": 0.0,
                                        "name": "test_noscale",
                                        "maxResolutionHint": 999999999.0,
                                        "queryable": True,
                                    },
                                ],
                                "maxResolutionHint": 999999999.0,
                                "minResolutionHint": 0.0,
                                "name": "__test_layer_noscale",
                            },
                            {
                                "childLayers": [
                                    {
                                        "minResolutionHint": 1.76,
                                        "name": "test_minscale",
                                        "maxResolutionHint": 999999999.0,
                                        "queryable": True,
                                    },
                                ],
                                "maxResolutionHint": 999999999.0,
                                "minResolutionHint": 1.76,
                                "name": "__test_layer_minscale",
                            },
                            {
                                "childLayers": [
                                    {
                                        "minResolutionHint": 0.0,
                                        "name": "test_maxscale",
                                        "maxResolutionHint": 8.82,
                                        "queryable": True,
                                    },
                                ],
                                "maxResolutionHint": 8.82,
                                "minResolutionHint": 0.0,
                                "name": "__test_layer_maxscale",
                            },
                            {
                                "childLayers": [
                                    {
                                        "minResolutionHint": 1.76,
                                        "name": "test_boothscale",
                                        "maxResolutionHint": 8.82,
                                        "queryable": True,
                                    },
                                ],
                                "maxResolutionHint": 8.82,
                                "minResolutionHint": 1.76,
                                "name": "__test_layer_boothscale",
                            },
                            {
                                "childLayers": [
                                    {
                                        "minResolutionHint": 1.76,
                                        "name": "test_boothscale",
                                        "maxResolutionHint": 8.82,
                                        "queryable": True,
                                    },
                                ],
                                "maxResolutionHint": 1000.0,
                                "minResolutionHint": 100.0,
                                "name": "__test_layer_metadatascale",
                            },
                        ],
                    },
                ],
            },
        ]
