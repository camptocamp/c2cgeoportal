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

from tests.functional import (  # noqa
    teardown_common as teardown_module,
    setup_common as setup_module,
    mapserv_url, create_default_ogcserver,
)


class TestLoopTheme(TestCase):

    def setup_method(self, _):
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import LayerWMS, \
            Theme, LayerGroup, Interface

        ogc_server, _ = create_default_ogcserver()
        main = Interface(name="desktop2")

        layer = LayerWMS(name="__test_layer", public=True)
        layer.layers = "__test_layer"
        layer.interfaces = [main]
        layer.ogc_server = ogc_server

        layer_group = LayerGroup(name="__test_layer_group")
        layer_group.children = [layer, layer_group]

        theme = Theme(name="__test_theme")
        theme.children = [layer_group]
        theme.interfaces = [main]

        DBSession.add_all([layer, layer_group, theme])
        transaction.commit()

    def teardown_method(self, _):
        testing.tearDown()

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import LayerWMS, \
            Theme, LayerGroup, OGCServer

        for t in DBSession.query(Theme).filter(Theme.name == "__test_theme").all():
            DBSession.delete(t)
        for g in DBSession.query(LayerGroup).all():
            DBSession.delete(g)
        for layer in DBSession.query(LayerWMS).all():
            DBSession.delete(layer)  # pragma: no cover
        DBSession.query(OGCServer).delete()

        transaction.commit()

    def test_theme(self):
        from c2cgeoportal_geoportal.views.entry import Entry

        request = testing.DummyRequest({
            "version": "2",
        })
        request.static_url = lambda url: "http://example.com/dummy/static/url"
        request.route_url = lambda url, _query={}: mapserv_url
        request.client_addr = None
        request.user = None
        entry = Entry(request)
        _, errors = entry._themes(None, "desktop2", True, 2)
        self.assertEqual(len([e for e in errors if e == "Too many recursions with group '__test_layer_group'"]), 1)
