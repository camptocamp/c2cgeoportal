# -*- coding: utf-8 -*-

# Copyright (c) 2012-2013 by Camptocamp SA


from unittest import TestCase
from nose.plugins.attrib import attr

import transaction
import os
from pyramid import testing

from c2cgeoportal.tests.functional import (  # NOQA
        tearDownCommon as tearDownModule,
        setUpCommon as setUpModule,
        mapserv_url)

@attr(functional=True)
class TestLoopTheme(TestCase):

    def setUp(self):
        self.config = testing.setUp()

        from c2cgeoportal.models import DBSession, Layer, \
                Theme, LayerGroup

        layer = Layer(name=u'__test_layer', public=True)
        layer_group = LayerGroup(name=u'__test_layer_group')
        layer_group.children = [layer, layer_group]

        theme = Theme(name=u'__test_theme')
        theme.children = [layer, layer_group]

        DBSession.add_all([layer, layer_group, theme])
        transaction.commit()



    def tearDown(self):
        testing.tearDown()

        from c2cgeoportal.models import DBSession, Layer, \
                Theme, LayerGroup, Role

        for t in DBSession.query(Theme).filter(Theme.name == '__test_theme').all():
            DBSession.delete(t)
        for layergroup in DBSession.query(LayerGroup).all():
            DBSession.delete(layergroup)  # pragma: nocover
        for layer in DBSession.query(Layer).all():
            DBSession.delete(layer)  # pragma: nocover

        transaction.commit()

    def test_theme(self):
        from c2cgeoportal.models import DBSession, Theme
        from c2cgeoportal.views.entry import Entry, cache_region

        request = testing.DummyRequest()
        request.static_url = lambda url: 'http://example.com/dummy/static/url'
        request.route_url = lambda url: mapserv_url
        curdir = os.path.dirname(os.path.abspath(__file__))
        mapfile = os.path.join(curdir, 'c2cgeoportal_test.map')
        ms_url = "%s?map=%s&" % (mapserv_url, mapfile)
        request.registry.settings = {
            'mapserv_url': ms_url,
        }
        request.user = None
        entry = Entry(request)

        cache_region.invalidate()
        themes = entry.themes()
        self.assertEquals(len(themes), 0)

        cache_region.invalidate()
        themes, errors = entry._themes(None)
        self.assertEquals(len(errors), 11)
        self.assertEquals(errors[0], 'Too many recursions with group "__test_layer_group"')
