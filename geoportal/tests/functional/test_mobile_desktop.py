# -*- coding: utf-8 -*-

# Copyright (c) 2013-2018, Camptocamp SA
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

import transaction
from pyramid import testing

from c2cgeoportal_geoportal.lib import functionality
from tests.functional import (  # noqa
    teardown_common as teardown_module,
    setup_common as setup_module,
    mapserv_url, create_dummy_request, create_default_ogcserver,
)


class TestMobileDesktop(TestCase):

    def setup_method(self, _):
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import LayerV1, Theme, Interface, LayerGroup

        create_default_ogcserver()
        main = Interface(name="main")
        mobile = Interface(name="mobile")

        layer = LayerV1(name="__test_layer")
        layer.interfaces = [main, mobile]

        mobile_only_layer = LayerV1(name="__test_mobile_only_layer")
        mobile_only_layer.interfaces = [mobile]

        desktop_only_layer = LayerV1(name="__test_desktop_only_layer")
        desktop_only_layer.interfaces = [main]

        group = LayerGroup(name="__test_layer_group")
        group.children = [layer, mobile_only_layer, desktop_only_layer]
        theme = Theme(name="__test_theme")
        theme.children = [group]
        theme.interfaces = [main, mobile]

        mobile_only_group = LayerGroup(name="__test_mobile_only_layer_group")
        mobile_only_group.children = [layer]
        mobile_only_theme = Theme(name="__test_mobile_only_theme")
        mobile_only_theme.children = [mobile_only_group]
        mobile_only_theme.interfaces = [mobile]

        desktop_only_group = LayerGroup(name="__test_desktop_only_layer_group")
        desktop_only_group.children = [layer]
        desktop_only_theme = Theme(name="__test_desktop_only_theme")
        desktop_only_theme.children = [desktop_only_group]
        desktop_only_theme.interfaces = [main]

        # the following theme should not appear in the list of themes on desktop
        # nor on mobile
        # It should be accessible by explicitely loading it in mobile though
        mobile_private_group = LayerGroup(name="__test_mobile_private_layer_group")
        mobile_private_group.children = [layer]
        mobile_private_theme = Theme(name="__test_mobile_private_theme")
        mobile_private_theme.children = [mobile_private_group]

        DBSession.add_all([
            layer, mobile_only_layer, desktop_only_layer, theme,
            mobile_only_theme, desktop_only_theme, mobile_private_theme
        ])
        transaction.commit()

    def teardown_method(self, _):
        testing.tearDown()

        functionality.FUNCTIONALITIES_TYPES = None

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import LayerV1, \
            Theme, LayerGroup, Interface, OGCServer

        for t in DBSession.query(Theme).all():
            DBSession.delete(t)
        for g in DBSession.query(LayerGroup).all():
            DBSession.delete(g)
        for layer in DBSession.query(LayerV1).all():
            DBSession.delete(layer)  # pragma: no cover
        DBSession.query(Interface).filter(
            Interface.name == "main"
        ).delete()
        DBSession.query(OGCServer).delete()

        transaction.commit()

    @staticmethod
    def _create_entry_obj(username=None, params=None, **kargs):
        if params is None:
            params = {}
        from c2cgeoportal_geoportal.views.entry import Entry

        request = create_dummy_request(**kargs)
        request.static_url = lambda url: "/dummy/static/url"
        request.route_url = lambda url, **kwargs: mapserv_url
        request.params = params

        return Entry(request)

    def test_desktop_layers(self):
        entry = self._create_entry_obj()
        response_vars = entry.get_cgxp_viewer_vars()

        import json
        themes = json.loads(response_vars["themes"])
        self.assertEqual(
            {t["name"] for t in themes},
            set(["__test_desktop_only_theme", "__test_theme"]),
        )
        theme = [t for t in themes if t["name"] == "__test_theme"]
        layers = theme[0]["children"][0]["children"]
        self.assertEqual(
            {l["name"] for l in layers},
            set(["__test_layer", "__test_desktop_only_layer"]),
        )
