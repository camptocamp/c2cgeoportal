# -*- coding: utf-8 -*-

import transaction
import sqlahelper
from sqlalchemy import create_engine
from geoalchemy import WKTSpatialElement
from pyramid import testing
from pyramid.configuration import Configurator

import c2cgeoportal
from c2cgeoportal.tests import TestView, DummyRequest, sqlalchemy_url
from c2cgeoportal.models import DBSession, User, Role, Layer, RestrictionArea, \
        Functionality, Theme
from c2cgeoportal.views.entry import Entry

class TestEntryView(TestView):

    def setUp(self):
        self.config = Configurator(package=c2cgeoportal)
        self.config.begin()

        engine = create_engine(sqlalchemy_url)
        sqlahelper.add_engine(engine)

        self.tearDown()

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

    def log_in(self):
        request = testing.DummyRequest()
        request.params['login'] = u'__test_user'
        request.params['password'] = u'__test_user'
        request.params['came_from'] = "/came_from"
        response = Entry(request).login()
        self.assertEquals(response.status_int, 302) 
        self.assertEquals(response.headers['Location'], "/came_from") 
        self.config.testing_securitypolicy(userid=u'__test_user')

    def log_out(self):
        request = testing.DummyRequest(path='/')
        request.params['came_from'] = '/came_from'
        response = Entry(request).logout()
        self.assertEquals(response.status_int, 302)
        self.assertEquals(response.headers['Location'], "/came_from") 
        self.config.testing_securitypolicy(userid=None)

    def test_index_no_auth(self):
        request = DummyRequest()
        response = Entry(request).home()
        assert '__test_public_layer' in response['themes']
        assert '__test_private_layer' not in response['themes']

    def test_index_auth(self):
        self.log_in()
        request = DummyRequest()
        response = Entry(request).home()
        self.log_out()
        assert '__test_public_layer' in response['themes']
        assert '__test_private_layer' in response['themes']

    def test_apiloader_no_auth(self):
        request = DummyRequest()
        response = Entry(request).apiloader()
        assert '__test_public_layer' in response['themes']
        assert '__test_private_layer' not in response['themes']

    def test_apiloader_auth(self):
        self.log_in()
        request = DummyRequest()
        response = Entry(request).apiloader()
        self.log_out()
        assert '__test_public_layer' in response['themes']
        assert '__test_private_layer' in response['themes']

