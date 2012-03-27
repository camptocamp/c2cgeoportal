from nose.plugins.attrib import attr
from pyramid import testing
from unittest import TestCase

from c2cgeoportal.tests.functional import tearDownModule, setUpModule


@attr(functional=True)
class TestLayers(TestCase):

    _table_index = 0

    def setUp(self):
        import sqlahelper
        import transaction
        from c2cgeoportal.models import DBSession, Role, User
        from c2cgeoportal.lib.dbreflection import init

        self.tables = []
        self.layer_ids = []

        self.role = Role(name=u'__test_role')
        self.user = User(username=u'__test_user',
                         password=u'__test_user',
                         role=self.role
                    )

        DBSession.add(self.user)
        transaction.commit()

        engine = sqlahelper.get_engine()
        init(engine)

    def tearDown(self):
        import transaction
        from c2cgeoportal.models import (DBSession, Role, User,
                                         Layer, TreeItem, RestrictionArea)

        transaction.commit()

        for t in self.tables:
            t.drop()

        for i in self.layer_ids:
            treeitem = DBSession.query(TreeItem).get(i)
            DBSession.delete(treeitem)
            layer = DBSession.query(Layer).get(i)
            DBSession.delete(layer)

        DBSession.query(User).filter(
                User.username == '__test_user').delete()
        DBSession.query(Role).filter(
                Role.name == '__test_role').delete()
        DBSession.query(RestrictionArea).filter(
                RestrictionArea.name == '__test_ra').delete()

        transaction.commit()

    def _create_layer(self):
        """ This function is central for this test class. It creates
        a layer with two features, and associates a restriction area
        to it. """
        import transaction
        import sqlahelper
        from sqlalchemy import func
        from sqlalchemy import Column, Table, MetaData, types
        from sqlalchemy.ext.declarative import declarative_base
        from geoalchemy import (GeometryDDL, GeometryExtensionColumn,
                                Point, WKTSpatialElement)
        from c2cgeoportal.models import DBSession, Layer, RestrictionArea

        self.__class__._table_index = self.__class__._table_index + 1
        id = self.__class__._table_index

        engine = sqlahelper.get_engine()
        Base = declarative_base(bind=engine)

        tablename = "table_%d" % id

        table = Table(tablename, Base.metadata,
                Column('id', types.Integer, primary_key=True),
                Column('name', types.Unicode),
                GeometryExtensionColumn('geom', Point(srid=21781)),
                schema='public')
        GeometryDDL(table)
        table.create()
        self.tables.append(table)

        ins = table.insert().values(
                name='foo',
                geom=func.ST_GeomFromText('POINT(5 45)', 21781))
        engine.connect().execute(ins)
        ins = table.insert().values(
                name='bar',
                geom=func.ST_GeomFromText('POINT(6 46)', 21781))
        engine.connect().execute(ins)

        layer = Layer()
        layer.id = id
        layer.geoTable = tablename
        layer.public = False

        ra = RestrictionArea()
        ra.name = u'__test_ra'
        ra.layers = [layer]
        ra.roles = [self.role]
        ra.readwrite = True
        poly = 'POLYGON((4 44, 4 46, 6 46, 6 44, 4 44))'
        ra.area = WKTSpatialElement(poly, srid=21781)

        DBSession.add(ra)

        self.layer_ids.append(self.__class__._table_index)

        transaction.commit()

        return id

    def _get_request(self, layerid, username=None):
        from c2cgeoportal.models import DBSession, User
        request = testing.DummyRequest()
        request.matchdict = {'layer_id': str(layerid)}
        if username is not None:
            request.user = DBSession.query(User).filter_by(
                                username=username).one()
        else:
            request.user = None
        return request

    def test_read_many_no_auth(self):
        from geojson.feature import FeatureCollection
        from c2cgeoportal.views.layers import read_many

        layer_id = self._create_layer()
        request = self._get_request(layer_id)

        collection = read_many(request)
        self.assertTrue(isinstance(collection, FeatureCollection))
        self.assertEquals(len(collection.features), 0)

    def test_read_many(self):
        from geojson.feature import FeatureCollection
        from c2cgeoportal.views.layers import read_many

        layer_id = self._create_layer()
        request = self._get_request(layer_id, username=u'__test_user')

        collection = read_many(request)
        self.assertTrue(isinstance(collection, FeatureCollection))
        self.assertEquals(len(collection.features), 1)

    def test_read_many_layer_not_found(self):
        from pyramid.httpexceptions import HTTPNotFound
        from c2cgeoportal.views.layers import read_many

        self._create_layer()
        request = self._get_request(10000, username=u'__test_user')

        self.assertRaises(HTTPNotFound, read_many, request)

    def test_read_many_multi(self):
        from geojson.feature import FeatureCollection
        from c2cgeoportal.views.layers import read_many

        layer_id1 = self._create_layer()
        layer_id2 = self._create_layer()
        layer_id3 = self._create_layer()

        layer_ids = '%d,%d,%d' % (layer_id1, layer_id2, layer_id3)
        request = self._get_request(layer_ids, username=u'__test_user')

        collection = read_many(request)
        self.assertTrue(isinstance(collection, FeatureCollection))
        self.assertEquals(len(collection.features), 3)
        self.assertEquals(collection.features[0].properties['__layer_id__'], layer_id1)
        self.assertEquals(collection.features[1].properties['__layer_id__'], layer_id2)
        self.assertEquals(collection.features[2].properties['__layer_id__'], layer_id3)

    def test_read_one_no_auth(self):
        from pyramid.httpexceptions import HTTPNotFound
        from c2cgeoportal.views.layers import read_one

        layer_id = self._create_layer()
        request = self._get_request(layer_id)
        request.matchdict['feature_id'] = 1

        self.assertRaises(HTTPNotFound, read_one, request)

    def test_read_one_no_perm(self):
        from pyramid.httpexceptions import HTTPNotFound
        from c2cgeoportal.views.layers import read_one

        layer_id = self._create_layer()
        request = self._get_request(layer_id, username=u'__test_user')
        request.matchdict['feature_id'] = 2

        self.assertRaises(HTTPNotFound, read_one, request)

    def test_read_one(self):
        from geojson.feature import Feature
        from c2cgeoportal.views.layers import read_one

        layer_id = self._create_layer()
        request = self._get_request(layer_id, username=u'__test_user')
        request.matchdict['feature_id'] = 1

        feature = read_one(request)
        self.assertTrue(isinstance(feature, Feature))
        self.assertEquals(feature.id, 1)
        self.assertEquals(feature.properties['name'], 'foo')

    def test_count(self):
        from c2cgeoportal.views.layers import count

        layer_id = self._create_layer()
        request = self._get_request(layer_id)

        response = count(request)
        self.assertEquals(response, 2)

    def test_create_no_auth(self):
        from pyramid.httpexceptions import HTTPForbidden
        from c2cgeoportal.views.layers import create

        layer_id = self._create_layer()
        request = self._get_request(layer_id)
        request.method = 'POST'
        request.body = '{"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"name": "foo"}, "geometry": {"type": "Point", "coordinates": [5, 45]}}, {"type": "Feature", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [5, 45]}}]}'
        self.assertRaises(HTTPForbidden, create, request)

    def test_create_no_perm(self):
        from pyramid.httpexceptions import HTTPForbidden
        from c2cgeoportal.views.layers import create

        layer_id = self._create_layer()
        request = self._get_request(layer_id, username=u'__test_user')
        request.method = 'POST'
        request.body = '{"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"name": "foo"}, "geometry": {"type": "Point", "coordinates": [4, 44]}}, {"type": "Feature", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [5, 45]}}]}'
        self.assertRaises(HTTPForbidden, create, request)

    def test_create(self):
        from geojson.feature import FeatureCollection
        from c2cgeoportal.views.layers import create

        layer_id = self._create_layer()
        request = self._get_request(layer_id, username=u'__test_user')
        request.method = 'POST'
        request.body = '{"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"name": "foo"}, "geometry": {"type": "Point", "coordinates": [5, 45]}}, {"type": "Feature", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [5, 45]}}]}'
        collection = create(request)
        self.assertTrue(isinstance(collection, FeatureCollection))
        self.assertEquals(len(collection.features), 2)

    def test_update_no_auth(self):
        from pyramid.httpexceptions import HTTPForbidden
        from c2cgeoportal.views.layers import update

        layer_id = self._create_layer()
        request = self._get_request(layer_id)
        request.matchdict['feature_id'] = 1
        request.method = 'PUT'
        request.body = '{"type": "Feature", "id": 1, "properties": {"name": "foobar"}, "geometry": {"type": "Point", "coordinates": [5, 45]}}'
        self.assertRaises(HTTPForbidden, update, request)

    def test_update_no_perm(self):
        from pyramid.httpexceptions import HTTPForbidden
        from c2cgeoportal.views.layers import update

        layer_id = self._create_layer()
        request = self._get_request(layer_id, username=u'__test_user')
        request.matchdict['feature_id'] = 1
        request.method = 'PUT'
        request.body = '{"type": "Feature", "id": 1, "properties": {"name": "foobar"}, "geometry": {"type": "Point", "coordinates": [4, 44]}}'
        self.assertRaises(HTTPForbidden, update, request)

    def test_update(self):
        from c2cgeoportal.views.layers import update

        layer_id = self._create_layer()
        request = self._get_request(layer_id, username=u'__test_user')
        request.matchdict['feature_id'] = 1
        request.method = 'PUT'
        request.body = '{"type": "Feature", "id": 1, "properties": {"name": "foobar"}, "geometry": {"type": "Point", "coordinates": [5, 45]}}'
        feature = update(request)
        self.assertEquals(feature.id, 1)
        self.assertEquals(feature.name, 'foobar')

    def test_delete(self):
        from c2cgeoportal.views.layers import delete

        layer_id = self._create_layer()
        request = self._get_request(layer_id)
        request.matchdict['feature_id'] = 1
        request.method = 'DELETE'
        response = delete(request)
        self.assertEquals(response.status_int, 204)

    def test_metadata(self):
        from c2cgeoportal.views.layers import metadata

        layer_id = self._create_layer()
        request = self._get_request(layer_id)

        table = metadata(request)
        self.assertEquals(table.name, 'table_%d' % layer_id)
