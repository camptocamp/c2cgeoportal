# -*- coding: utf-8 -*-
from unittest import TestCase

import transaction
from geoalchemy import WKTSpatialElement
from pyramid import testing

from c2cgeoportal.tests import tearDownModule, setUpModule

class TestEntryView(TestCase):

    def setUp(self):
        self.config = testing.setUp()

        from c2cgeoportal.models import DBSession, User, Role, Layer, \
                RestrictionArea, Functionality, Theme

        user = User(u'__test_user', u'__test_user')
        pt1 = Functionality(name=u'print_template', value=u'1 Wohlen A4 portrait')
        pt2 = Functionality(name=u'print_template', value=u'2 Wohlen A3 landscape')
        extent = "POLYGON((663173.125 245090, 663291 245090, 663291 245153.2, 663173.125 245153.2, 663173.125 245090))"
        extent = WKTSpatialElement(extent, srid=21781)
        role = Role(name=u'__test_role', extent=extent, functionalities=[pt1, pt2])
        user.role = role

        user.email = u'Tarenpion'

        pub_layer = Layer(name=u'u__test_public_layer', order=400, public=True)
        priv_layer = Layer(name=u'u__test_private_layer', order=400, public=False)
        
        theme = Theme(name=u'__test')
        theme.children = [pub_layer, priv_layer]

        area = "POLYGON((-100 0, -100 20, 100 20, 100 0, -100 0))"
        area = WKTSpatialElement(area, srid=21781)
        restricted_area2 = RestrictionArea(u'__test_ra', u'', [pub_layer, priv_layer], [role], area)

        DBSession.add_all([user, pub_layer, priv_layer, theme])
        transaction.commit()

    def tearDown(self):
        testing.tearDown()

        from c2cgeoportal.models import DBSession, User, Role, Layer, \
                RestrictionArea, Functionality, Theme

        DBSession.query(User).filter(User.username == '__test_user').delete()
        for f in DBSession.query(Functionality).filter(Functionality.value == u'1 Wohlen A4 portrait').all():
            DBSession.delete(f)
        for f in DBSession.query(Functionality).filter(Functionality.value == u'2 Wohlen A3 landscape').all():
            DBSession.delete(f)
        DBSession.query(RestrictionArea).filter(
                RestrictionArea.name == '__test_ra').delete()
        DBSession.query(Role).filter(Role.name == '__test_role').delete()
        for t in DBSession.query(Theme).filter(Theme.name == '__test').all():
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

    def test_logout(self):
        from c2cgeoportal.views.entry import Entry

        request = testing.DummyRequest(path='/')
        request.params['came_from'] = '/came_from'
        response = Entry(request).logout()
        self.assertEquals(response.status_int, 302)
        self.assertEquals(response.headers['Location'], "/came_from") 

    def test_index_no_auth(self):
        from c2cgeoportal.views.entry import Entry
        from mock import patch, MagicMock

        request = testing.DummyRequest()
        request.registry.settings = {
                'external_themes_url': '',
                'webclient_string_functionalities': '',
                'webclient_array_functionalities': '',
                }
        request.static_url = lambda url: '/dummy/static/url'
        request.route_url = lambda url: '/dummy/route/url'
        with patch('c2cgeoportal.views.entry.WebMapService', MagicMock()):
            response = Entry(request).home()
        assert '__test_public_layer' in response['themes']
        assert '__test_private_layer' not in response['themes']

    def test_index_auth(self):
        from c2cgeoportal.views.entry import Entry
        from mock import patch, MagicMock

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
        with patch('c2cgeoportal.views.entry.WebMapService', MagicMock()):
            response = entry.home()
        assert '__test_public_layer' in response['themes']
        assert '__test_private_layer' in response['themes']

    def test_apiloader_no_auth(self):
        from c2cgeoportal.views.entry import Entry
        from mock import patch, MagicMock

        request = testing.DummyRequest()
        request.registry.settings = {
                'external_themes_url': '',
                'webclient_string_functionalities': '',
                'webclient_array_functionalities': '',
                }
        request.static_url = lambda url: '/dummy/static/url'
        request.route_url = lambda url: '/dummy/route/url'
        with patch('c2cgeoportal.views.entry.WebMapService', MagicMock()):
            response = Entry(request).apiloader()
        assert '__test_public_layer' in response['themes']
        assert '__test_private_layer' not in response['themes']

    def test_apiloader_auth(self):
        from c2cgeoportal.views.entry import Entry
        from mock import patch, MagicMock

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
        with patch('c2cgeoportal.views.entry.WebMapService', MagicMock()):
            response = entry.apiloader()
        assert '__test_public_layer' in response['themes']
        assert '__test_private_layer' in response['themes']

