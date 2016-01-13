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


from unittest import TestCase
from nose.plugins.attrib import attr

import transaction
from pyramid import testing

from c2cgeoportal.tests.functional import (  # noqa
    tear_down_common as tearDownModule,
    set_up_common as setUpModule,
    mapserv_url, host, create_dummy_request)


@attr(functional=True)
class TestMobileDesktop(TestCase):

    def setUp(self):  # noqa
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None

        from c2cgeoportal.models import DBSession, LayerV1, Theme, Interface, LayerGroup

        main = Interface(name=u"main")
        mobile = Interface(name=u"mobile")

        layer = LayerV1(name=u"__test_layer")
        layer.interfaces = [main, mobile]

        mobile_only_layer = LayerV1(name=u"__test_mobile_only_layer")
        mobile_only_layer.interfaces = [mobile]

        desktop_only_layer = LayerV1(name=u"__test_desktop_only_layer")
        desktop_only_layer.interfaces = [main]

        group = LayerGroup(name=u"__test_layer_group")
        group.children = [layer, mobile_only_layer, desktop_only_layer]
        theme = Theme(name=u"__test_theme")
        theme.children = [group]
        theme.interfaces = [main, mobile]

        mobile_only_group = LayerGroup(name=u"__test_mobile_only_layer_group")
        mobile_only_group.children = [layer]
        mobile_only_theme = Theme(name=u"__test_mobile_only_theme")
        mobile_only_theme.children = [mobile_only_group]
        mobile_only_theme.interfaces = [mobile]

        desktop_only_group = LayerGroup(name=u"__test_desktop_only_layer_group")
        desktop_only_group.children = [layer]
        desktop_only_theme = Theme(name=u"__test_desktop_only_theme")
        desktop_only_theme.children = [desktop_only_group]
        desktop_only_theme.interfaces = [main]

        # the following theme should not appear in the list of themes on desktop
        # nor on mobile
        # It should be accessible by explicitely loading it in mobile though
        mobile_private_group = LayerGroup(name=u"__test_mobile_private_layer_group")
        mobile_private_group.children = [layer]
        mobile_private_theme = Theme(name=u"__test_mobile_private_theme")
        mobile_private_theme.children = [mobile_private_group]

        DBSession.add_all([
            layer, mobile_only_layer, desktop_only_layer, theme,
            mobile_only_theme, desktop_only_theme, mobile_private_theme
        ])
        transaction.commit()

    def tearDown(self):  # noqa
        testing.tearDown()

        from c2cgeoportal.models import DBSession, LayerV1, \
            Theme, LayerGroup, Interface

        for t in DBSession.query(Theme).all():
            DBSession.delete(t)
        for layergroup in DBSession.query(LayerGroup).all():
            DBSession.delete(layergroup)  # pragma: nocover
        for layer in DBSession.query(LayerV1).all():
            DBSession.delete(layer)  # pragma: nocover
        DBSession.query(Interface).filter(
            Interface.name == "main"
        ).delete()

        transaction.commit()

    def _create_entry_obj(self, username=None, params={}):
        from c2cgeoportal.views.entry import Entry

        request = create_dummy_request()
        request.static_url = lambda url: "/dummy/static/url"
        request.route_url = lambda url, **kwargs: \
            request.registry.settings["mapserverproxy"]["mapserv_url"]
        request.params = params

        return Entry(request)

    def test_mobile_themes(self):
        entry = self._create_entry_obj()
        entry.request.interface_name = "mobile"
        response_vars = entry.mobileconfig()

        self.assertEqual(
            [t["name"] for t in response_vars["themes"]],
            [u"__test_theme", u"__test_mobile_only_theme"]
        )
        self.assertEqual(
            response_vars["themes"],
            [{
                "name": u"__test_theme",
                "icon": u"",
                "layers": [u"__test_mobile_only_layer", "__test_layer"],
                "allLayers": [
                    {"name": u"__test_mobile_only_layer"},
                    {"name": u"__test_layer"}
                ]
            }, {
                "name": u"__test_mobile_only_theme",
                "icon": u"",
                "layers": [u"__test_layer"],
                "allLayers": [
                    {"name": u"__test_layer"}
                ]
            }]
        )

    def test_mobile_private_theme(self):
        entry = self._create_entry_obj()
        entry.request.interface_name = "mobile"
        response_vars = entry.mobileconfig()
        entry.request.registry.settings["functionalities"] = {
            "anonymous": {
                "mobile_default_theme": u"__test_mobile_private_theme"
            }
        }
        response_vars = entry.mobileconfig()

        self.assertEqual(
            response_vars["themes"],
            [{
                "name": u"__test_theme",
                "icon": u"",
                "layers": [u"__test_mobile_only_layer", u"__test_layer"],
                "allLayers": [
                    {"name": u"__test_mobile_only_layer"},
                    {"name": u"__test_layer"}
                ]
            }, {
                "name": u"__test_mobile_only_theme",
                "icon": u"",
                "layers": [u"__test_layer"],
                "allLayers": [
                    {"name": u"__test_layer"}
                ]
            }, {
                "name": u"__test_mobile_private_theme",
                "icon": u"",
                "layers": [u"__test_layer"],
                "allLayers": [
                    {"name": u"__test_layer"}
                ]
            }]
        )

    def test_desktop_layers(self):
        entry = self._create_entry_obj()
        response_vars = entry.get_cgxp_viewer_vars()

        import json
        themes = json.loads(response_vars["themes"])
        self.assertEqual(
            set([t["name"] for t in themes]),
            set([u"__test_desktop_only_theme", u"__test_theme"]),
        )
        theme = [t for t in themes if t["name"] == u"__test_theme"]
        layers = theme[0]["children"][0]["children"]
        self.assertEqual(
            set([l["name"] for l in layers]),
            set([u"__test_layer", u"__test_desktop_only_layer"]),
        )
