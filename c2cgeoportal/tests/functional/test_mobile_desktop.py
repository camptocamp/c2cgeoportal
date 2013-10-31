# -*- coding: utf-8 -*-

# Copyright (c) 2013, Camptocamp SA
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

from c2cgeoportal.tests.functional import (  # NOQA
    tearDownCommon as tearDownModule,
    setUpCommon as setUpModule,
    mapserv_url, host)


@attr(functional=True)
class TestMobileDesktop(TestCase):

    def setUp(self):
        self.config = testing.setUp()

        from c2cgeoportal.models import DBSession, Layer, Theme

        layer = Layer(name=u'__test_layer')

        mobile_only_layer = Layer(name=u'__test_mobile_only_layer')
        mobile_only_layer.inDesktopViewer = False

        desktop_only_layer = Layer(name=u'__test_desktop_only_layer')
        desktop_only_layer.inMobileViewer = False

        theme = Theme(name=u'__test_theme')
        theme.children = [layer, mobile_only_layer, desktop_only_layer]
        theme.inMobileViewer = True

        mobile_only_theme = Theme(name=u'__test_mobile_only_theme')
        mobile_only_theme.children = [layer]
        mobile_only_theme.inDesktopViewer = False
        mobile_only_theme.inMobileViewer = True

        desktop_only_theme = Theme(name=u'__test_desktop_only_theme')
        desktop_only_theme.children = [layer]
        desktop_only_theme.inMobileViewer = False

        # the following theme should not appear in the list of themes on desktop
        # nor on mobile
        # It should be accessible by explicitely loading it in mobile though
        mobile_private_theme = Theme(name=u'__test_mobile_private_theme')
        mobile_private_theme.children = [layer]
        mobile_private_theme.inDesktopViewer = False
        mobile_private_theme.inMobileViewer = False

        DBSession.add_all([
            layer, mobile_only_layer, desktop_only_layer, theme,
            mobile_only_theme, desktop_only_theme, mobile_private_theme
        ])
        transaction.commit()

    def tearDown(self):
        testing.tearDown()

        from c2cgeoportal.models import DBSession, Layer, \
            Theme, LayerGroup

        for t in DBSession.query(Theme).all():
            DBSession.delete(t)
        for layergroup in DBSession.query(LayerGroup).all():
            DBSession.delete(layergroup)  # pragma: nocover
        for layer in DBSession.query(Layer).all():
            DBSession.delete(layer)  # pragma: nocover

        transaction.commit()

    def _create_entry_obj(self, username=None, params={}):
        from c2cgeoportal.views.entry import Entry

        mapfile = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'c2cgeoportal_test.map'
        )
        mapserv = "%s?map=%s&" % (mapserv_url, mapfile)
        request = testing.DummyRequest()
        request.headers['Host'] = host
        request.registry.settings = {
            'mapserv_url': mapserv,
        }
        mapserv = "%s?map=%s&" % (mapserv_url, mapfile)
        request.static_url = lambda url: '/dummy/static/url'
        request.route_url = lambda url: mapserv
        request.params = params

        request.user = None

        return Entry(request)

    def test_mobile_themes(self):
        entry = self._create_entry_obj()
        response = entry.mobileconfig()

        import json
        themes = json.loads(response['themes'])
        self.assertEqual(len(themes), 2)
        self.assertEqual(
            themes,
            [{
                "name": "__test_theme",
                "icon": "/dummy/static/url"
            }, {
                "name": "__test_mobile_only_theme",
                "icon": "/dummy/static/url"
            }]
        )

    def test_mobile_private_theme(self):
        entry = self._create_entry_obj()
        response = entry.mobileconfig()
        entry.request.registry.settings['functionalities'] = {
            'anonymous': {
                'mobile_default_theme': u'__test_mobile_private_theme'
            }
        }
        response = entry.mobileconfig()

        import json
        layers = json.loads(response['layers'])
        self.assertEqual(len(layers), 1)
        self.assertEqual(layers[0]['name'], u'__test_layer')

    def test_desktop_themes(self):
        entry = self._create_entry_obj()
        response = entry.mobileconfig()

        import json
        themes = json.loads(response['themes'])
        self.assertEqual(len(themes), 2)
        self.assertEqual(
            themes,
            [{
                "name": "__test_theme",
                "icon": "/dummy/static/url"
            }, {
                "name": "__test_mobile_only_theme",
                "icon": "/dummy/static/url"
            }]
        )

    def test_mobile_layers(self):
        entry = self._create_entry_obj()
        entry.request.registry.settings['functionalities'] = {
            'anonymous': {
                'mobile_default_theme': u'__test_theme'
            }
        }
        response = entry.mobileconfig()

        layers = response['layers'].split(',')
        self.assertEqual(len(layers), 2)

    def test_desktop_layers(self):
        entry = self._create_entry_obj()
        response = entry.viewer()

        import json
        themes = json.loads(response['themes'])
        theme = themes[0]

        layers = theme['children']
        self.assertEqual(len(layers), 2)
        self.assertEqual(
            layers,
            [{
                u'name': u'__test_layer',
                u'isLegendExpanded': False,
                u'legend': True,
                u'public': True,
                u'isChecked': True,
                u'type': u'internal WMS',
                u'id': 1,
                u'imageType': None
            }, {
                u'name': u'__test_desktop_only_layer',
                u'isLegendExpanded': False,
                u'legend': True,
                u'public': True,
                u'isChecked': True,
                u'type': u'internal WMS',
                u'id': 4,
                u'imageType': None
            }]
        )
