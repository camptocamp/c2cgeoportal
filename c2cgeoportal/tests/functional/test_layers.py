from nose.plugins.attrib import attr
from pyramid import testing
from unittest import TestCase

from c2cgeoportal.tests.functional import tearDownModule, setUpModule


@attr(functional=True)
class TestLayers(TestCase):

    def setUp(self):
        import sqlahelper
        from c2cgeoportal.lib.dbreflection import init

        self.table = None

        engine = sqlahelper.get_engine()
        init(engine)

    def tearDown(self):
        import transaction
        from c2cgeoportal.models import DBSession, Layer, TreeItem

        transaction.commit()

        if self.table is not None:
            self.table.drop()

        treeitem = DBSession.query(TreeItem).get(1)
        DBSession.delete(treeitem)

        layer = DBSession.query(Layer).get(1)
        DBSession.delete(layer)

        transaction.commit()

    def _create_layer(self, tablename):
        import transaction
        import sqlahelper
        from sqlalchemy import func
        from sqlalchemy import Column, Table, MetaData, types
        from sqlalchemy.ext.declarative import declarative_base
        from geoalchemy import GeometryDDL, GeometryExtensionColumn
        from geoalchemy import Point

        engine = sqlahelper.get_engine()
        Base = declarative_base(bind=engine)

        table = Table(tablename, Base.metadata,
                Column('id', types.Integer, primary_key=True),
                Column('name', types.Unicode),
                GeometryExtensionColumn('geom', Point),
                schema='public')
        GeometryDDL(table)
        table.create()
        self.table = table

        ins = table.insert().values(
                name='foo',
                geom=func.ST_GeomFromText('POINT(5 45)', 4326))
        engine.connect().execute(ins)
        ins = table.insert().values(
                name='bar',
                geom=func.ST_GeomFromText('POINT(6 46)', 4326))
        engine.connect().execute(ins)

        from c2cgeoportal.models import DBSession, Layer
        layer = Layer()
        layer.id = 1
        layer.geoTable = tablename
        DBSession.add(layer)

        transaction.commit()

    def _get_request(self, layerid):
        request = testing.DummyRequest()
        # FIXME there may be a better way
        request.matchdict = {'layer_id': layerid}
        return request

    def test_read_many(self):
        from geojson.feature import FeatureCollection
        from c2cgeoportal.views.layers import read_many

        self._create_layer('layer_a')
        request = self._get_request(1)

        collection = read_many(request)
        self.assertTrue(isinstance(collection, FeatureCollection))
        self.assertEquals(len(collection.features), 2)

    def test_read_one(self):
        from geojson.feature import Feature
        from c2cgeoportal.views.layers import read_one

        self._create_layer('layer_b')
        request = self._get_request(1)
        request.matchdict['feature_id'] = 2

        feature = read_one(request)
        self.assertTrue(isinstance(feature, Feature))
        self.assertEquals(feature.id, 2)
        self.assertEquals(feature.properties['name'], 'bar')

    def test_count(self):
        from c2cgeoportal.views.layers import count

        self._create_layer('layer_c')
        request = self._get_request(1)

        response = count(request)
        self.assertEquals(response, 2)

    def test_create(self):
        from geojson.feature import FeatureCollection
        from c2cgeoportal.views.layers import create

        self._create_layer('layer_d')
        request = self._get_request(1)
        request.method = 'POST'
        request.body = '{"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"name": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}, {"type": "Feature", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}]}'
        collection = create(request)
        self.assertTrue(isinstance(collection, FeatureCollection))
        self.assertEquals(len(collection.features), 2)

    def test_update(self):
        from c2cgeoportal.views.layers import update

        self._create_layer('layer_e')
        request = self._get_request(1)
        request.matchdict['feature_id'] = 1
        request.method = 'PUT'
        request.body = '{"type": "Feature", "id": 1, "properties": {"name": "foobar"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}'
        feature = update(request)
        self.assertEquals(feature.id, 1)
        self.assertEquals(feature.name, 'foobar')

    def test_delete(self):
        from c2cgeoportal.views.layers import delete

        self._create_layer('layer_f')
        request = self._get_request(1)
        request.matchdict['feature_id'] = 1
        request.method = 'DELETE'
        response = delete(request)
        self.assertEquals(response.status_int, 204)

    def test_metadata(self):
        from c2cgeoportal.views.layers import metadata

        self._create_layer('layer_g')
        request = self._get_request(1)

        table = metadata(request)
        self.assertEquals(table.name, 'layer_g')

    def test_read_many_layer_not_found(self):
        from pyramid.httpexceptions import HTTPNotFound
        from c2cgeoportal.views.layers import read_many

        self._create_layer('layer_h')
        request = self._get_request(2)

        self.assertRaises(HTTPNotFound, read_many, request)
