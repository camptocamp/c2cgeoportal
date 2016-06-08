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
import os
from pyramid import testing

from c2cgeoportal.tests.functional import (  # noqa
    tear_down_common as tearDownModule,
    set_up_common as setUpModule,
    mapserv_url, host)


@attr(functional=True)
class TestLoopTheme(TestCase):

    def setUp(self):  # noqa
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None

        from c2cgeoportal.models import DBSession, LayerV1, \
            Theme, LayerGroup, Interface

        main = Interface(name=u"main")

        layer = LayerV1(name=u"__test_layer", public=True)
        layer.interfaces = [main]

        layer_group = LayerGroup(name=u"__test_layer_group")
        layer_group.children = [layer, layer_group]

        theme = Theme(name=u"__test_theme")
        theme.children = [layer, layer_group]
        theme.interfaces = [main]

        DBSession.add_all([layer, layer_group, theme])
        transaction.commit()

    def tearDown(self):  # noqa
        testing.tearDown()

        from c2cgeoportal.models import DBSession, LayerV1, \
            Theme, LayerGroup

        for t in DBSession.query(Theme).filter(Theme.name == "__test_theme").all():
            DBSession.delete(t)
        DBSession.query(LayerGroup).delete()
        for layer in DBSession.query(LayerV1).all():
            DBSession.delete(layer)  # pragma: no cover

        transaction.commit()

    def test_theme(self):
        from c2cgeoportal.views.entry import Entry, cache_region

        request = testing.DummyRequest()
        request.headers["Host"] = host
        request.static_url = lambda url: "http://example.com/dummy/static/url"
        request.route_url = lambda url: mapserv_url
        request.client_addr = None
        curdir = os.path.dirname(os.path.abspath(__file__))
        mapfile = os.path.join(curdir, "c2cgeoportal_test.map")
        ms_url = "%s?map=%s&" % (mapserv_url, mapfile)
        request.registry.settings["mapserverproxy"]["mapserv_url"] = ms_url
        request.user = None
        entry = Entry(request)

        cache_region.invalidate()
        themes = entry.themes()
        self.assertEquals([t["name"] for t in themes], [u"__test_theme"])

        cache_region.invalidate()
        themes, errors = entry._themes(None, u"main")
        self.assertEquals(len([e for e in errors if e == "Too many recursions with group '__test_layer_group'"]), 1)
