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
                RestrictionArea, Functionality, Theme

        role = Role(name=u'__test_role')
        user = User(username=u'__test_user', password=u'__test_user', role=role)

        public_layer = Layer(name=u'__test_public_layer', order=400, public=True)
        private_layer = Layer(name=u'__test_private_layer', order=400, public=False)
        
        theme = Theme(name=u'__test_theme')
        theme.children = [public_layer, private_layer]

        area = "POLYGON((-100 0, -100 20, 100 20, 100 0, -100 0))"
        area = WKTSpatialElement(area, srid=21781)
        ra = RestrictionArea(name=u'__test_ra', description=u'',
                             layers=[public_layer, private_layer],
                             roles=[role], area=area)

        DBSession.add_all([user, public_layer, private_layer])
        transaction.commit()

    def tearDown(self):
        testing.tearDown()

        from c2cgeoportal.models import DBSession, User, Role, Layer, \
                RestrictionArea, Functionality, Theme

        DBSession.query(User).filter(User.username == '__test_user').delete()
        DBSession.query(RestrictionArea).filter(
                RestrictionArea.name == '__test_ra').delete()
        DBSession.query(Role).filter(Role.name == '__test_role').delete()
        for t in DBSession.query(Theme).filter(Theme.name == '__test_theme').all():
            DBSession.delete(t)
        for layer in DBSession.query(Layer).all():
            DBSession.delete(layer)
        transaction.commit()

    def test_login(self):
        from c2cgeoportal.views.entry import Entry
        from pyramid.security import authenticated_userid

        request = testing.DummyRequest()
        request.params['login'] = u'__test_user'
        request.params['password'] = u'__test_user'
        request.params['came_from'] = "/came_from"
        response = Entry(request).login()
        self.assertEquals(response.status_int, 302) 
        self.assertEquals(response.headers['Location'], "/came_from") 

    def test_logout_no_auth(self):
        from c2cgeoportal.views.entry import Entry

        request = testing.DummyRequest(path='/')
        request.params['came_from'] = '/came_from'
        entry = Entry(request)
        response = entry.logout()
        self.assertEquals(response.status_int, 404)

    def test_logout(self):
        from c2cgeoportal.views.entry import Entry

        request = testing.DummyRequest(path='/')
        request.params['came_from'] = '/came_from'
        entry = Entry(request)
        entry.username = u'__test_user'
        response = entry.logout()
        self.assertEquals(response.status_int, 302)
        self.assertEquals(response.headers['Location'], "/came_from") 

    def test_index_no_auth(self):
        from c2cgeoportal.views.entry import Entry
        from mock import patch, Mock, MagicMock
        from contextlib import nested

        request = testing.DummyRequest()
        request.registry.settings = {
                'external_themes_url': '',
                'webclient_string_functionalities': '',
                'webclient_array_functionalities': '',
                }
        request.static_url = lambda url: '/dummy/static/url'
        request.route_url = lambda url: '/dummy/route/url'

        patch1 = patch('c2cgeoportal.views.entry.WebMapService', MagicMock())
        patch2 = patch('c2cgeoportal.views.entry.urllib.urlopen')
        with nested(patch1, patch2) as (_, mock_urlopen):
                m = Mock()
                m.read.return_value = ''
                mock_urlopen.return_value = m
                response = Entry(request).home()

        assert '__test_public_layer' in response['themes']
        assert '__test_private_layer' not in response['themes']

    def test_index_auth(self):
        from c2cgeoportal.views.entry import Entry
        from mock import patch, Mock, MagicMock
        from contextlib import nested

        request = testing.DummyRequest()
        request.registry.settings = {
                'external_themes_url': '',
                'webclient_string_functionalities': '',
                'webclient_array_functionalities': '',
                }
        request.static_url = lambda url: '/dummy/static/url'
        request.route_url = lambda url: '/dummy/route/url'
        entry = Entry(request)
        entry.username = u'__test_user'

        patch1 = patch('c2cgeoportal.views.entry.WebMapService', MagicMock())
        patch2 = patch('c2cgeoportal.views.entry.urllib.urlopen')
        with nested(patch1, patch2) as (_, mock_urlopen):
                m = Mock()
                m.read.return_value = ''
                mock_urlopen.return_value = m
                response = entry.home()

        assert '__test_public_layer' in response['themes']
        assert '__test_private_layer' in response['themes']

    def test_apiloader_no_auth(self):
        from c2cgeoportal.views.entry import Entry
        from mock import patch, Mock, MagicMock
        from contextlib import nested

        request = testing.DummyRequest()
        request.registry.settings = {
                'external_themes_url': '',
                'webclient_string_functionalities': '',
                'webclient_array_functionalities': '',
                }
        request.static_url = lambda url: '/dummy/static/url'
        request.route_url = lambda url: '/dummy/route/url'

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
        from c2cgeoportal.views.entry import Entry
        from mock import patch, Mock, MagicMock
        from contextlib import nested

        request = testing.DummyRequest()
        request.registry.settings = {
                'external_themes_url': '',
                'webclient_string_functionalities': '',
                'webclient_array_functionalities': '',
                }
        request.static_url = lambda url: '/dummy/static/url'
        request.route_url = lambda url: '/dummy/route/url'
        entry = Entry(request)
        entry.username = u'__test_user'

        patch1 = patch('c2cgeoportal.views.entry.WebMapService', MagicMock())
        patch2 = patch('c2cgeoportal.views.entry.urllib.urlopen')
        with nested(patch1, patch2) as (_, mock_urlopen):
                m = Mock()
                m.read.return_value = ''
                mock_urlopen.return_value = m
                response = entry.apiloader()

        assert '__test_public_layer' in response['themes']
        assert '__test_private_layer' in response['themes']

