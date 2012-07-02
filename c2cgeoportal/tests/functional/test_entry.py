# -*- coding: utf-8 -*-

from unittest import TestCase
from nose.plugins.attrib import attr

import transaction
import os
from geoalchemy import WKTSpatialElement
from pyramid import testing
from owslib.wms import WebMapService

from c2cgeoportal.tests.functional import tearDownModule, setUpModule, mapserv_url

@attr(functional=True)
class TestEntryView(TestCase):

    def setUp(self):
        self.config = testing.setUp()

        from c2cgeoportal.models import DBSession, User, Role, Layer, \
                RestrictionArea, Theme

        role1 = Role(name=u'__test_role1')
        user1 = User(username=u'__test_user1', password=u'__test_user1', role=role1)

        role2 = Role(name=u'__test_role2')
        user2 = User(username=u'__test_user2', password=u'__test_user2', role=role2)

        public_layer = Layer(name=u'__test_public_layer', order=400, public=True)

        private_layer = Layer(name=u'__test_private_layer', order=400, public=False)
        private_layer.geoTable = 'a_schema.a_geo_table'
        
        theme = Theme(name=u'__test_theme')
        theme.children = [public_layer, private_layer]

        poly = "POLYGON((-100 0, -100 20, 100 20, 100 0, -100 0))"

        area = WKTSpatialElement(poly, srid=21781)
        ra = RestrictionArea(name=u'__test_ra1', description=u'',
                             layers=[private_layer],
                             roles=[role1], area=area)

        area = WKTSpatialElement(poly, srid=21781)
        ra = RestrictionArea(name=u'__test_ra2', description=u'',
                             layers=[private_layer],
                             roles=[role2], area=area, readwrite=True)

        DBSession.add_all([user1, user2, public_layer, private_layer])

        transaction.commit()

    def tearDown(self):
        testing.tearDown()

        from c2cgeoportal.models import DBSession, User, Role, Layer, \
                RestrictionArea, Theme

        DBSession.query(User).filter(User.username == '__test_user1').delete()
        DBSession.query(User).filter(User.username == '__test_user2').delete()
        DBSession.query(RestrictionArea).filter(
                RestrictionArea.name == '__test_ra1').delete()
        DBSession.query(RestrictionArea).filter(
                RestrictionArea.name == '__test_ra2').delete()
        DBSession.query(Role).filter(Role.name == '__test_role1').delete()
        DBSession.query(Role).filter(Role.name == '__test_role2').delete()
        for t in DBSession.query(Theme).filter(Theme.name == '__test_theme').all():
            DBSession.delete(t)
        for layer in DBSession.query(Layer).all():
            DBSession.delete(layer)
        transaction.commit()

    #
    # login/logout tests
    #

    def test_login(self):
        from c2cgeoportal import default_user_validator
        from c2cgeoportal.views.entry import Entry
        from pyramid.security import authenticated_userid

        request = testing.DummyRequest()
        request.params['login'] = u'__test_user1'
        request.params['password'] = u'__test_user1'
        request.params['came_from'] = "/came_from"
        request.registry.validate_user = default_user_validator
        request.user = None
        response = Entry(request).login()
        self.assertEquals(response.status_int, 302) 
        self.assertEquals(response.headers['Location'], "/came_from") 

    def test_logout_no_auth(self):
        from c2cgeoportal.views.entry import Entry

        request = testing.DummyRequest(path='/')
        request.params['came_from'] = '/came_from'
        request.user = None
        entry = Entry(request)
        response = entry.logout()
        self.assertEquals(response.status_int, 404)

    def test_logout(self):
        from c2cgeoportal.models import DBSession, User
        from c2cgeoportal.views.entry import Entry

        request = testing.DummyRequest(path='/')
        request.params['came_from'] = '/came_from'
        request.user = DBSession.query(User) \
                                .filter_by(username=u'__test_user1').one()
        entry = Entry(request)
        response = entry.logout()
        self.assertEquals(response.status_int, 302)
        self.assertEquals(response.headers['Location'], "/came_from") 

    #
    # viewer view tests
    #

    def _create_entry_obj(self, username=None):
        from c2cgeoportal.models import DBSession, User
        from c2cgeoportal.views.entry import Entry

        request = testing.DummyRequest()
        request.registry.settings = {
                'mapserv.url': mapserv_url,
                'external_themes_url': '',
                'webclient_string_functionalities': '',
                'webclient_array_functionalities': '',
                }
        request.static_url = lambda url: '/dummy/static/url'
        request.route_url = lambda url: '/dummy/route/url'

        if username:
            request.user = DBSession.query(User) \
                                    .filter_by(username=username).one()
        else:
            request.user = None

        return Entry(request)

    def test_index_no_auth(self):
        from mock import patch, Mock, MagicMock
        from contextlib import nested

        entry = self._create_entry_obj()

        patch1 = patch('c2cgeoportal.views.entry.WebMapService', MagicMock())
        patch2 = patch('c2cgeoportal.views.entry.urllib.urlopen')
        with nested(patch1, patch2) as (_, mock_urlopen):
                m = Mock()
                m.read.return_value = ''
                mock_urlopen.return_value = m
                response = entry.viewer()

        assert '__test_public_layer' in response['themes']
        assert '__test_private_layer' not in response['themes']

    def test_index_auth_no_edit_permission(self):
        import json
        from mock import patch, Mock, MagicMock
        from contextlib import nested

        entry = self._create_entry_obj(username=u'__test_user1')

        patch1 = patch('c2cgeoportal.views.entry.WebMapService', MagicMock())
        patch2 = patch('c2cgeoportal.views.entry.urllib.urlopen')
        with nested(patch1, patch2) as (_, mock_urlopen):
                m = Mock()
                m.read.return_value = ''
                mock_urlopen.return_value = m
                response = entry.viewer()

        themes = json.loads(response['themes'])
        self.assertEqual(len(themes), 1)

        theme = themes[0]

        layers = theme['children']
        self.assertEqual(len(layers), 2)

        layer = layers[0]
        self.assertEqual(layer['name'], '__test_private_layer')
        self.assertFalse('editable' in layer)

        layer = layers[1]
        self.assertEqual(layer['name'], '__test_public_layer')
        self.assertFalse('editable' in layer)


    def test_index_auth_edit_permission(self):
        import json
        from mock import patch, Mock, MagicMock
        from contextlib import nested

        entry = self._create_entry_obj(username=u'__test_user2')

        patch1 = patch('c2cgeoportal.views.entry.WebMapService', MagicMock())
        patch2 = patch('c2cgeoportal.views.entry.urllib.urlopen')
        with nested(patch1, patch2) as (_, mock_urlopen):
                m = Mock()
                m.read.return_value = ''
                mock_urlopen.return_value = m
                response = entry.viewer()

        themes = json.loads(response['themes'])
        self.assertEqual(len(themes), 1)

        theme = themes[0]

        layers = theme['children']
        self.assertEqual(len(layers), 2)

        layer = layers[0]
        self.assertEqual(layer['name'], '__test_private_layer')
        self.assertTrue('editable' in layer)

        layer = layers[1]
        self.assertEqual(layer['name'], '__test_public_layer')
        self.assertFalse('editable' in layer)

    #
    # apiloader view tests
    #

    def test_apiloader_no_auth(self):
        from mock import patch, Mock, MagicMock
        from contextlib import nested
        from c2cgeoportal.views.entry import Entry

        request = testing.DummyRequest()
        request.registry.settings = {
                'mapserv.url': mapserv_url,
                'external_themes_url': '',
                'webclient_string_functionalities': '',
                'webclient_array_functionalities': '',
                }
        request.static_url = lambda url: '/dummy/static/url'
        request.route_url = lambda url: '/dummy/route/url'
        request.user = None

        patch1 = patch('c2cgeoportal.views.entry.WebMapService', MagicMock())
        patch2 = patch('c2cgeoportal.views.entry.urllib.urlopen')
        with nested(patch1, patch2) as (_, mock_urlopen):
                m = Mock()
                m.read.return_value = ''
                mock_urlopen.return_value = m
                response = Entry(request).apiloader()

        assert '__test_public_layer' in response['themes']
        assert '__test_private_layer' not in response['themes']

    def test_apiloader_auth(self):
        from mock import patch, Mock, MagicMock
        from contextlib import nested
        from c2cgeoportal.models import DBSession, User
        from c2cgeoportal.views.entry import Entry

        request = testing.DummyRequest()
        request.registry.settings = {
                'mapserv.url': mapserv_url,
                'external_themes_url': '',
                'webclient_string_functionalities': '',
                'webclient_array_functionalities': '',
                }
        request.static_url = lambda url: '/dummy/static/url'
        request.route_url = lambda url: '/dummy/route/url'
        request.user = DBSession.query(User) \
                                .filter_by(username=u'__test_user1').one()
        entry = Entry(request)

        patch1 = patch('c2cgeoportal.views.entry.WebMapService', MagicMock())
        patch2 = patch('c2cgeoportal.views.entry.urllib.urlopen')
        with nested(patch1, patch2) as (_, mock_urlopen):
                m = Mock()
                m.read.return_value = ''
                mock_urlopen.return_value = m
                response = entry.apiloader()

        assert '__test_public_layer' in response['themes']
        assert '__test_private_layer' in response['themes']

    def test_layer(self):
        from c2cgeoportal.views.entry import Entry
        from c2cgeoportal.models import Layer, LayerGroup, Theme

        request = testing.DummyRequest()
        request.static_url = lambda url: '/dummy/static/' + url
        request.route_url = lambda url: '/dummy/route/' + url
        request.registry.settings = {
            'project': 'test_layer',
        }
        entry = Entry(request)
        entry.errors = "";

        self.assertEqual(entry._group(LayerGroup(), [], [], None), None)

        layer = Layer()
        layer.id = 20
        layer.name = 'test internal WMS'
        layer.metadataURL = "http://example.com/tiwms"
        layer.isChecked = True
        layer.layerType = "internal WMS"
        layer.imageType = "image/png"
        layer.style = "my-style"
        layer.kml = "tiwms.kml"
        layer.legend = True
        layer.legendRule = "rule"
        layer.legendImage = "legend:static/tiwms-legend.png"
        layer.minResolution = 10
        layer.maxResolution = 1000
        layer.disclaimer = "Camptocamp"
        layer.identifierAttributeField = "name"
        layer.geoTable = "tiwms"
        self.assertEqual(entry._layer(layer, [], None), {
            'id': 20,
            'name': 'test internal WMS', 
            'metadataURL': 'http://example.com/tiwms', 
            'isChecked': True, 
            'icon': '/dummy/route/mapserverproxy?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetLegendGraphic&LAYER=test internal WMS&FORMAT=image/png&TRANSPARENT=TRUE&RULE=rule',
            'type': u'internal WMS', 
            'imageType': 'image/png', 
            'style': 'my-style', 
            'kml': '/dummy/static/test_layer:static/tiwms.kml', 
            'legend': True, 
            'legendImage': '/dummy/static/legend:static/tiwms-legend.png',
            'minResolutionHint': 10, 
            'maxResolutionHint': 1000, 
            'disclaimer': 'Camptocamp',
            'identifierAttribute': 'name', 
            'editable': True, 
        })
        self.assertEqual(entry.errors, '')

        layer = Layer()
        layer.id = 20
        layer.name = 'test external WMS'
        layer.isChecked = False
        layer.icon = "tewms.png"
        layer.layerType = "external WMS"
        layer.url = "http://example.com"
        layer.imageType = "image/jpeg"
        layer.isSingleTile = True
        layer.legend = False
        layer.minResolution = 10
        layer.maxResolution = 1000
        self.assertEqual(entry._layer(layer, [], None), {
            'id': 20,
            'name': 'test external WMS', 
            'icon': '/dummy/static/test_layer:static/tewms.png',
            'isChecked': False, 
            'type': u'external WMS', 
            'url': 'http://example.com',
            'imageType': 'image/jpeg', 
            'isSingleTile': True,
            'legend': False, 
            'minResolutionHint': 10, 
            'maxResolutionHint': 1000, 
        })
        self.assertEqual(entry.errors, '')

        layer = Layer()
        layer.id = 20
        layer.name = 'test WMTS'
        layer.isChecked = False
        layer.layerType = "WMTS"
        layer.url = "http://example.com/WMTS-Capabilities.xml"
        layer.style = 'wmts-style'
        layer.dimensions = '{"DATE": "1012"}'
        layer.matrixSet = "swissgrid"
        layer.wmsUrl = 'http://example.com/'
        layer.wmsLayers = 'test'
        layer.legend = False
        layer.minResolution = 10
        layer.maxResolution = 1000
        self.assertEqual(entry._layer(layer, [], None), {
            'id': 20,
            'name': 'test WMTS', 
            'isChecked': False, 
            'type': 'WMTS', 
            'url': 'http://example.com/WMTS-Capabilities.xml',
            'style': 'wmts-style',
            'dimensions': {u'DATE': u'1012'},
            'matrixSet': 'swissgrid',
            'wmsUrl': 'http://example.com/',
            'wmsLayers': 'test',
            'legend': False, 
            'minResolutionHint': 10, 
            'maxResolutionHint': 1000, 
        })
        self.assertEqual(entry.errors, '')

        layer = Layer()
        layer.id = 20
        layer.name = 'test WMTS'
        layer.isChecked = False
        layer.layerType = "WMTS"
        layer.url = "http://example.com/WMTS-Capabilities.xml"
        layer.wmsUrl = 'http://example.com/'
        layer.legend = False
        layer.minResolution = 10
        layer.maxResolution = 1000
        self.assertEqual(entry._layer(layer, [], None), {
            'id': 20,
            'name': 'test WMTS', 
            'isChecked': False, 
            'type': 'WMTS', 
            'url': 'http://example.com/WMTS-Capabilities.xml',
            'wmsUrl': 'http://example.com/',
            'wmsLayers': 'test WMTS',
            'legend': False, 
            'minResolutionHint': 10, 
            'maxResolutionHint': 1000, 
        })
        self.assertEqual(entry.errors, '')

        layer = Layer()
        layer.id = 20
        layer.name = 'test WMTS'
        layer.isChecked = False
        layer.layerType = "WMTS"
        layer.url = "http://example.com/WMTS-Capabilities.xml"
        layer.wmsLayers = 'test'
        layer.legend = False
        layer.minResolution = 10
        layer.maxResolution = 1000
        self.assertEqual(entry._layer(layer, [], None), {
            'id': 20,
            'name': 'test WMTS', 
            'isChecked': False, 
            'type': 'WMTS', 
            'url': 'http://example.com/WMTS-Capabilities.xml',
            'wmsUrl': '/dummy/route/mapserverproxy',
            'wmsLayers': 'test',
            'legend': False, 
            'minResolutionHint': 10, 
            'maxResolutionHint': 1000, 
        })
        self.assertEqual(entry.errors, '')

        layer = Layer()
        layer.id = 20
        layer.name = 'test no 2D'
        layer.isChecked = False
        layer.layerType = "no 2D"
        layer.legend = False
        layer.metadataURL = 'http://example.com/wmsfeatures.metadata'
        self.assertEqual(entry._layer(layer, [], None), {
            'id': 20,
            'name': u'test no 2D', 
            'isChecked': False, 
            'type': u'no 2D', 
            'legend': False, 
            'metadataURL': u'http://example.com/wmsfeatures.metadata'
        })
        self.assertEqual(entry.errors, '')

        curdir = os.path.dirname(os.path.abspath(__file__))
        map = os.path.join(curdir, 'c2cgeoportal_test.map')
        print "%s?map=%s" % (mapserv_url, map)
        wms = WebMapService("%s?map=%s" % (mapserv_url, map), version='1.1.1')
        wms_layers = list(wms.contents)
        layer = Layer()
        layer.id = 20
        layer.name = 'test_wmsfeaturesgroup'
        layer.layerType = "internal WMS"
        layer.imageType = "image/png"
        layer.isChecked = False
        layer.legend = False
        self.assertEqual(entry._layer(layer, wms_layers, wms), {
            'id': 20,
            'name': u'test_wmsfeaturesgroup',
            'isChecked': False,
            'type': u'internal WMS',
            'legend': False,
            'imageType': u'image/png',
            'minResolutionHint': 1.76,
            'maxResolutionHint': 8.8200000000000003,
            'metadataUrls': [{
                'url': 'http://example.com/wmsfeatures.metadata',
                'type': 'TC211',
                'format': 'text/plain',
            }],
            'childLayers': [{
                'name': u'test_wmsfeatures',
                'minResolutionHint': 1.76,
                'maxResolutionHint': 8.8200000000000003,
            }],
        })
        self.assertEqual(entry.errors, '')

        group1 = LayerGroup()
        group1.name = 'block'
        group2 = LayerGroup()
        group2.name = 'node'
        group2.metadataURL = 'http://example.com/group.metadata'
        layer = Layer()
        layer.id = 20
        layer.name = 'test layer in group'
        layer.isChecked = False 
        layer.layerType = "internal WMS"
        layer.imageType = "image/png"
        layer.legend = False
        group1.children = [group2]
        group2.children = [layer]
        self.assertEqual(entry._group(group1, [layer], [], None), {
            'isExpanded': False,
            'isInternalWMS': True,
            'name': u'block',
            'isBaseLayer': False,
            'children': [{
                'isExpanded': False,
                'isInternalWMS': True,
                'name': u'node',
                'isBaseLayer': False,
                'metadataURL': 'http://example.com/group.metadata',
                'children': [{
                    'name': u'test layer in group',
                    'id': 20,
                    'isChecked': False,
                    'type': u'internal WMS',
                    'legend': False,
                    'imageType': u'image/png'
                }]
            }]
        })
        self.assertEqual(entry.errors, '')

        group1 = LayerGroup()
        group1.isInternalWMS = True
        group2 = LayerGroup()
        group2.isInternalWMS = False
        group1.children = [group2]
        entry._group(group1, [], [], None)
        self.assertNotEqual(entry.errors, '')
        
        entry.errors = ''
        self.assertEqual(entry.errors, '')

        group1 = LayerGroup()
        group1.isInternalWMS = False
        group2 = LayerGroup()
        group2.isInternalWMS = True
        group1.children = [group2]
        entry._group(group1, [], [], None)
        self.assertNotEqual(entry.errors, '')

        entry.errors = ''
        self.assertEqual(entry.errors, '')

        group = LayerGroup()
        group.isInternalWMS = True
        layer = Layer()
        layer.layerType = 'internal WMS'
        group.children = [layer]
        entry._group(group, [layer], [], None)
        self.assertEqual(entry.errors, '')

        group = LayerGroup()
        group.isInternalWMS = True
        layer = Layer()
        layer.layerType = 'external WMS'
        group.children = [layer]
        entry._group(group, [layer], [], None)
        self.assertNotEqual(entry.errors, '')

        entry.errors = ''
        self.assertEqual(entry.errors, '')

        group = LayerGroup()
        group.isInternalWMS = True
        layer = Layer()
        layer.layerType = 'WMTS'
        group.children = [layer]
        entry._group(group, [layer], [], None)
        self.assertNotEqual(entry.errors, '')

        entry.errors = ''
        self.assertEqual(entry.errors, '')

        group = LayerGroup()
        group.isInternalWMS = True
        layer = Layer()
        layer.layerType = 'no 2D'
        group.children = [layer]
        entry._group(group, [layer], [], None)
        self.assertNotEqual(entry.errors, '')

        entry.errors = ''
        self.assertEqual(entry.errors, '')

        group = LayerGroup()
        group.isInternalWMS = False
        layer = Layer()
        layer.layerType = 'internal WMS'
        group.children = [layer]
        entry._group(group, [layer], [], None)
        self.assertNotEqual(entry.errors, '')

        entry.errors = ''
        self.assertEqual(entry.errors, '')

        group = LayerGroup()
        group.isInternalWMS = False
        layer = Layer()
        layer.layerType = 'external WMS'
        group.children = [layer]
        entry._group(group, [layer], [], None)
        self.assertEqual(entry.errors, '')

        group = LayerGroup()
        group.isInternalWMS = False
        layer = Layer()
        layer.layerType = 'WMTS'
        group.children = [layer]
        entry._group(group, [layer], [], None)
        self.assertEqual(entry.errors, '')

        group = LayerGroup()
        group.isInternalWMS = False
        layer = Layer()
        layer.layerType = 'no 2D'
        group.children = [layer]
        entry._group(group, [layer], [], None)
        self.assertEqual(entry.errors, '')

