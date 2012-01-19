# -*- coding: utf-8 -*-
#
# GetMap
# ======
#
# md5sum with 4 squares: 61cbb0a6d18b72e4a28c1087019de245
# md5sum with the 2 top squares: 0a4fac2209d06c6fa36048c125b1679a
# md5sum with no squares: ef33223235b26c782736c88933b35331
#
#

import os
import hashlib
from unittest import TestCase
from nose.plugins.attrib import attr

from sqlalchemy import Column, types
from geoalchemy import GeometryColumn, Point, GeometryDDL, WKTSpatialElement
import transaction
from pyramid import testing
import sqlahelper

from c2cgeoportal.tests.functional import setUpModule, tearDownModule, mapserv_url

Base = sqlahelper.get_base()

class TestPoint(Base):
    __tablename__ = 'testpoint'
    __table_args__ = {'schema': 'main'}
    id = Column(types.Integer, primary_key=True)
    the_geom = GeometryColumn(Point(srid=21781))
GeometryDDL(TestPoint.__table__)

@attr(functional=True)
class TestMapserverproxyView(TestCase):


    def setUp(self):
        self.config = testing.setUp()

        from c2cgeoportal.models import User, Role, Layer, RestrictionArea, \
                Functionality, DBSession

        TestPoint.__table__.create(bind=DBSession.bind, checkfirst=True)

        geom = WKTSpatialElement("POINT(-90 -45)", srid=21781)
        p1 = TestPoint(the_geom=geom)
        geom = WKTSpatialElement("POINT(-90 45)", srid=21781)
        p2 = TestPoint(the_geom=geom)
        geom = WKTSpatialElement("POINT(90 45)", srid=21781)
        p3 = TestPoint(the_geom=geom)
        geom = WKTSpatialElement("POINT(90 -45)", srid=21781)
        p4 = TestPoint(the_geom=geom)

        pt1 = Functionality(name=u'print_template', value=u'1 Wohlen A4 portrait')
        pt2 = Functionality(name=u'print_template', value=u'2 Wohlen A3 landscape')
        user1 = User(username=u'__test_user1', password=u'__test_user1')
        role1 = Role(name=u'__test_role1', description=u'__test_role1', functionalities=[pt1, pt2])
        user1.role = role1
        user1.email = u'Tarenpion'

        user2 = User(username=u'__test_user2', password=u'__test_user2')
        role2 = Role(name=u'__test_role2', description=u'__test_role2', functionalities=[pt1, pt2])
        user2.role = role2
        user2.email = u'Tarenpion'

        layer1 = Layer(u'testpoint_unprotected', 300, public=True)
        layer2 = Layer(u'testpoint_protected', 400, public=False)

        area = "POLYGON((-100 30, -100 50, 100 50, 100 30, -100 30))"
        area = WKTSpatialElement(area, srid=21781)
        restricted_area1 = RestrictionArea(u'__test_ra1', u'', [layer2], [role1], area)

        area = "POLYGON((-100 0, -100 20, 100 20, 100 0, -100 0))"
        area = WKTSpatialElement(area, srid=21781)
        restricted_area2 = RestrictionArea(u'__test_ra2', u'', [layer2], [role2], area)

        DBSession.add_all([p1, p2, p3, p4, user1, user2,
                         restricted_area1, restricted_area2])
        transaction.commit()

    def tearDown(self):
        testing.tearDown()

        from c2cgeoportal.models import User, Role, Layer, RestrictionArea, \
                Functionality, DBSession
        
        DBSession.query(User).filter(User.username == '__test_user1').delete()
        DBSession.query(User).filter(User.username == '__test_user2').delete()
        DBSession.query(RestrictionArea).filter(
                RestrictionArea.name == '__test_ra1').delete()
        DBSession.query(RestrictionArea).filter(
                RestrictionArea.name == '__test_ra2').delete()
        DBSession.query(Role).filter(Role.name == '__test_role1').delete()
        DBSession.query(Role).filter(Role.name == '__test_role2').delete()
        for f in DBSession.query(Functionality).filter(Functionality.value == u'1 Wohlen A4 portrait').all():
            DBSession.delete(f)
        for f in DBSession.query(Functionality).filter(Functionality.value == u'2 Wohlen A3 landscape').all():
            DBSession.delete(f)
        for layer in DBSession.query(Layer).filter(Layer.name == 'testpoint_unprotected').all():
            DBSession.delete(layer)
        for layer in DBSession.query(Layer).filter(Layer.name == 'testpoint_protected').all():
            DBSession.delete(layer)

        transaction.commit()
        TestPoint.__table__.drop(bind=DBSession.bind, checkfirst=True)


    def _get_mapfile_path(self):
        curdir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(curdir, 'c2cgeoportal_test.map')

    def _get_auth_header(self, user):
        userpass = '%s:%s' % (user, user)
        return {'Authorization': 'Basic %s' % userpass.encode('base64')}

    def test_GetMap_unprotected_layer_anonymous(self):
        from c2cgeoportal.views import mapserverproxy

        map = self._get_mapfile_path()
        request = testing.DummyRequest()
        request.registry.settings = {
                'mapserv.url': mapserv_url,
                }
        request.params = dict(map=map, service='wms', version='1.1.1', request='getmap',
                      bbox='-180,-90,180,90', layers='testpoint_unprotected',
                      width='600', height='400', srs='EPSG:21781', format='image/png')
        response = mapserverproxy.proxy(request)

        md5sum = hashlib.md5(response.body).hexdigest()
        # 4 square
        self.assertEquals(response.status_int, 200) 
        assert md5sum == '61cbb0a6d18b72e4a28c1087019de245'

    def test_GetMap_unprotected_layer_user1(self):
        from c2cgeoportal.views import mapserverproxy

        map = self._get_mapfile_path()
        self.config.testing_securitypolicy('__test_user1')
        request = testing.DummyRequest()
        request.registry.settings = {
                'mapserv.url': mapserv_url,
                }
        request.params = dict(map=map, service='wms', version='1.1.1', request='getmap',
                      bbox='-180,-90,180,90', layers='testpoint_unprotected',
                      width='600', height='400', srs='EPSG:21781', format='image/png')
        response = mapserverproxy.proxy(request)

        md5sum = hashlib.md5(response.body).hexdigest()
        # 4 square
        self.assertEquals(response.status_int, 200) 
        assert md5sum == '61cbb0a6d18b72e4a28c1087019de245'

    def test_GetMap_unprotected_layer_user2(self):
        from c2cgeoportal.views import mapserverproxy

        map = self._get_mapfile_path()
        self.config.testing_securitypolicy('__test_user2')
        request = testing.DummyRequest()
        request.registry.settings = {
                'mapserv.url': mapserv_url,
                }
        request.params = dict(map=map, service='wms', version='1.1.1', request='getmap',
                      bbox='-180,-90,180,90', layers='testpoint_unprotected',
                      width='600', height='400', srs='EPSG:21781', format='image/png')
        response = mapserverproxy.proxy(request)

        md5sum = hashlib.md5(response.body).hexdigest()
        # 4 square
        self.assertEquals(response.status_int, 200) 
        assert md5sum == '61cbb0a6d18b72e4a28c1087019de245'

    def test_GetMap_protected_layer_anonymous(self):
        from c2cgeoportal.views import mapserverproxy

        map = self._get_mapfile_path()
        request = testing.DummyRequest()
        request.registry.settings = {
                'mapserv.url': mapserv_url,
                }
        request.params = dict(map=map, service='wms', version='1.1.1', request='getmap',
                      bbox='-180,-90,180,90', layers='testpoint_protected',
                      width='600', height='400', srs='EPSG:21781', format='image/png')
        response = mapserverproxy.proxy(request)

        md5sum = hashlib.md5(response.body).hexdigest()
        # empty
        self.assertEquals(response.status_int, 200) 
        assert md5sum == 'ef33223235b26c782736c88933b35331'

    def test_GetMap_protected_layer_user1(self):
        from c2cgeoportal.views import mapserverproxy

        map = self._get_mapfile_path()
        self.config.testing_securitypolicy('__test_user1')
        request = testing.DummyRequest()
        request.registry.settings = {
                'mapserv.url': mapserv_url,
                }
        request.params = dict(map=map, service='wms', version='1.1.1', request='getmap',
                      bbox='-180,-90,180,90', layers='testpoint_protected',
                      width='600', height='400', srs='EPSG:21781', format='image/png')
        response = mapserverproxy.proxy(request)
        
        md5sum = hashlib.md5(response.body).hexdigest()
        # two squares
        self.assertEquals(response.status_int, 200) 
        assert md5sum == '0a4fac2209d06c6fa36048c125b1679a'

    def test_GetMap_protected_layer_user2(self):
        from c2cgeoportal.views import mapserverproxy

        map = self._get_mapfile_path()
        self.config.testing_securitypolicy('__test_user2')
        request = testing.DummyRequest()
        request.registry.settings = {
                'mapserv.url': mapserv_url,
                }
        request.params = dict(map=map, service='wms', version='1.1.1', request='getmap',
                      bbox='-180,-90,180,90', layers='testpoint_protected',
                      width='600', height='400', srs='EPSG:21781', format='image/png')
        response = mapserverproxy.proxy(request)

        md5sum = hashlib.md5(response.body).hexdigest()
        # empty
        self.assertEquals(response.status_int, 200) 
        assert md5sum == 'ef33223235b26c782736c88933b35331'
