from nose.plugins.attrib import attr
from pyramid import testing
from unittest import TestCase

from c2cgeoportal.tests.functional import tearDownModule, setUpModule


@attr(functional=True)
class TestLayers(TestCase):

    def setUp(self):
        import sqlahelper
        from c2cgeoportal.lib.dbreflection import init

        self.tables = []
        self.layer_ids = []

        engine = sqlahelper.get_engine()
        init(engine)

    def tearDown(self):
        import transaction
        from c2cgeoportal.models import DBSession, Layer, TreeItem

        transaction.commit()

        for t in self.tables:
            t.drop()

        for i in self.layer_ids:
            treeitem = DBSession.query(TreeItem).get(i)
            DBSession.delete(treeitem)
            layer = DBSession.query(Layer).get(i)
            DBSession.delete(layer)

        transaction.commit()

    def _create_layer(self, id):
        import transaction
        import sqlahelper
        from sqlalchemy import func
        from sqlalchemy import Column, Table, MetaData, types
        from sqlalchemy.ext.declarative import declarative_base
        from geoalchemy import GeometryDDL, GeometryExtensionColumn, Point
        from c2cgeoportal.models import DBSession, Layer

        engine = sqlahelper.get_engine()
        Base = declarative_base(bind=engine)

        tablename = "table_%d" % id

        table = Table(tablename, Base.metadata,
                Column('id', types.Integer, primary_key=True),
                Column('name', types.Unicode),
                GeometryExtensionColumn('geom', Point),
                schema='public')
        GeometryDDL(table)
        table.create()
        self.tables.append(table)

        ins = table.insert().values(
                name='foo',
                geom=func.ST_GeomFromText('POINT(5 45)', 4326))
        engine.connect().execute(ins)
        ins = table.insert().values(
                name='bar',
                geom=func.ST_GeomFromText('POINT(6 46)', 4326))
        engine.connect().execute(ins)

        layer = Layer()
        layer.id = id
        layer.geoTable = tablename
        DBSession.add(layer)
        self.layer_ids.append(id)

        transaction.commit()

    def _get_request(self, layerid):
        request = testing.DummyRequest()
        request.matchdict = {'layer_id': str(layerid)}
        return request

    def test_read_many(self):
        from geojson.feature import FeatureCollection
        from c2cgeoportal.views.layers import read_many

        layer_id = 1
        self._create_layer(layer_id)
        request = self._get_request(layer_id)

        collection = read_many(request)
        self.assertTrue(isinstance(collection, FeatureCollection))
        self.assertEquals(len(collection.features), 2)

    def test_read_one(self):
        from geojson.feature import Feature
        from c2cgeoportal.views.layers import read_one

        layer_id = 2
        self._create_layer(layer_id)
        request = self._get_request(layer_id)
        request.matchdict['feature_id'] = 2

        feature = read_one(request)
        self.assertTrue(isinstance(feature, Feature))
        self.assertEquals(feature.id, 2)
        self.assertEquals(feature.properties['name'], 'bar')

    def test_count(self):
        from c2cgeoportal.views.layers import count

        layer_id = 3
        self._create_layer(layer_id)
        request = self._get_request(layer_id)

        response = count(request)
        self.assertEquals(response, 2)

    def test_create(self):
        from geojson.feature import FeatureCollection
        from c2cgeoportal.views.layers import create

        layer_id = 4
        self._create_layer(layer_id)
        request = self._get_request(layer_id)
        request.method = 'POST'
        request.body = '{"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"name": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}, {"type": "Feature", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}]}'
        collection = create(request)
        self.assertTrue(isinstance(collection, FeatureCollection))
        self.assertEquals(len(collection.features), 2)

    def test_update(self):
        from c2cgeoportal.views.layers import update

        layer_id = 5
        self._create_layer(layer_id)
        request = self._get_request(layer_id)
        request.matchdict['feature_id'] = 1
        request.method = 'PUT'
        request.body = '{"type": "Feature", "id": 1, "properties": {"name": "foobar"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}'
        feature = update(request)
        self.assertEquals(feature.id, 1)
        self.assertEquals(feature.name, 'foobar')

    def test_delete(self):
        from c2cgeoportal.views.layers import delete

        layer_id = 6
        self._create_layer(layer_id)
        request = self._get_request(layer_id)
        request.matchdict['feature_id'] = 1
        request.method = 'DELETE'
        response = delete(request)
        self.assertEquals(response.status_int, 204)

    def test_metadata(self):
        from c2cgeoportal.views.layers import metadata

        layer_id = 7
        self._create_layer(layer_id)
        request = self._get_request(layer_id)

        table = metadata(request)
        self.assertEquals(table.name, 'table_7')

    def test_read_many_layer_not_found(self):
        from pyramid.httpexceptions import HTTPNotFound
        from c2cgeoportal.views.layers import read_many

        self._create_layer(8)
        request = self._get_request(9)

        self.assertRaises(HTTPNotFound, read_many, request)

    def test_read_many_multi(self):
        from geojson.feature import FeatureCollection
        from c2cgeoportal.views.layers import read_many

        self._create_layer(9)
        self._create_layer(10)
        self._create_layer(11)

        self.assertTrue(True)
        request = self._get_request('9,10,11')

        collection = read_many(request)
        self.assertTrue(isinstance(collection, FeatureCollection))
        self.assertEquals(len(collection.features), 6)
        self.assertEquals(collection.features[0].properties['__layer_id__'], 9)
        self.assertEquals(collection.features[1].properties['__layer_id__'], 9)
        self.assertEquals(collection.features[2].properties['__layer_id__'], 10)
        self.assertEquals(collection.features[3].properties['__layer_id__'], 10)
        self.assertEquals(collection.features[4].properties['__layer_id__'], 11)
        self.assertEquals(collection.features[5].properties['__layer_id__'], 11)
