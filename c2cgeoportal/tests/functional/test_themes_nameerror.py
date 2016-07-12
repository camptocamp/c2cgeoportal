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
class TestThemesNameErrorView(TestCase):

    def setUp(self):  # noqa
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None

        from c2cgeoportal.models import DBSession, \
            Theme, LayerGroup, Interface, OGCServer, LayerWMS

        main = Interface(name=u"main")

        ogc_server = OGCServer(name="__test_ogc_server", type="mapserver", image_type="image/jpeg")

        layer_wms = LayerWMS(name=u"__test_layer_wms", public=True)
        layer_wms.layer = "testpoint_unprotected"
        layer_wms.interfaces = [main]
        layer_wms.ogc_server = ogc_server

        layer_group = LayerGroup(name=u"__test_layer_group")
        layer_group.children = [layer_wms]

        theme = Theme(name=u"__test/theme")
        theme.interfaces = [main]
        theme.children = [
            layer_group
        ]

        DBSession.add(theme)
        transaction.commit()

    def tearDown(self):
        testing.tearDown()

        from c2cgeoportal.models import DBSession, Layer, \
            Theme, LayerGroup, OGCServer, Interface

        for layer in DBSession.query(Layer).all():
            DBSession.delete(layer)
        DBSession.query(LayerGroup).delete()
        for t in DBSession.query(Theme).all():
            DBSession.delete(t)
        DBSession.query(OGCServer).filter(
            OGCServer.name == "__test_ogc_server"
        ).delete()
        DBSession.query(Interface).filter(
            Interface.name == "main"
        ).delete()

        transaction.commit()

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

    def test_error(self):
        from c2cgeoportal.views.entry import Entry

        entry = Entry(self._create_request_obj(params={
            "version": "2",
        }))
        themes = entry.themes()
        self.assertEquals(set(themes["errors"]), set([
            "The theme has an unsupported name '__test/theme'."
        ]))
