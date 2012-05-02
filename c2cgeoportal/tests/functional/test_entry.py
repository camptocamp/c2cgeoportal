# -*- coding: utf-8 -*-
from unittest import TestCase
from nose.plugins.attrib import attr

import transaction
from geoalchemy import WKTSpatialElement
from pyramid import testing

from c2cgeoportal.tests.functional import tearDownModule, setUpModule

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
        from c2cgeoportal.views.entry import Entry
        from pyramid.security import authenticated_userid

        request = testing.DummyRequest()
        request.params['login'] = u'__test_user1'
        request.params['password'] = u'__test_user1'
        request.params['came_from'] = "/came_from"
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

