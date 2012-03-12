# -*- coding: utf-8 -*-
from unittest import TestCase
from nose.plugins.attrib import attr

from c2cgeoportal.tests.functional import tearDownModule, setUpModule

@attr(functional=True)
class TestReflection(TestCase):

    def setUp(self):
        import sqlahelper
        from c2cgeoportal.lib.dbreflection import init

        self.table = None

        engine = sqlahelper.get_engine()
        init(engine)

    def tearDown(self):
        import c2cgeoportal.lib.dbreflection

        # drop any table created by the test function with _create_table
        if self.table is not None:
            self.table.drop()

        # clear the dbreflection class cache
        c2cgeoportal.lib.dbreflection._class_cache = {}

    def _create_table(self, tablename):
        """ Test functions use this function to create a table object.
        Each test function should call this function only once. And
        there should not be two test functions that call this function
        with the same tablename value.
        """
        import sqlahelper
        from sqlalchemy import Table, Column, types
        from sqlalchemy.ext.declarative import declarative_base
        from geoalchemy import GeometryExtensionColumn, GeometryDDL
        from geoalchemy import (Point, LineString, Polygon,
                                MultiPoint, MultiLineString, MultiPolygon)

        engine = sqlahelper.get_engine()
        Base = declarative_base(bind=engine)
        table = Table(tablename, Base.metadata,
                      Column('id', types.Integer, primary_key=True),
                      GeometryExtensionColumn('point', Point),
                      GeometryExtensionColumn('linestring', LineString),
                      GeometryExtensionColumn('polygon', Polygon),
                      GeometryExtensionColumn('multipoint', MultiPoint),
                      GeometryExtensionColumn('multilinestring', MultiLineString),
                      GeometryExtensionColumn('multipolygon', MultiPolygon),
                      schema='public'
                      )
        GeometryDDL(table)
        table.create()
        self.table = table

    def test_get_class_nonexisting_table(self):
        from sqlalchemy.exc import NoSuchTableError
        import c2cgeoportal.lib.dbreflection
        from c2cgeoportal.lib.dbreflection import get_class

        self.assertRaises(NoSuchTableError, get_class, 'nonexisting')
        self.assertEquals(c2cgeoportal.lib.dbreflection._class_cache, {})

    def test_get_class(self):
        from geoalchemy import SpatialComparator
        from geoalchemy import (Point, LineString, Polygon,
                                MultiPoint, MultiLineString, MultiPolygon)
        import c2cgeoportal.lib.dbreflection
        from c2cgeoportal.lib.dbreflection import get_class

        self._create_table('table_a')
        modelclass = get_class('table_a')

        # test the class
        self.assertEquals(modelclass.__name__, 'Table_a')
        self.assertEquals(modelclass.__table__.name, 'table_a')
        self.assertEquals(modelclass.__table__.schema, 'public')
        self.assertTrue(isinstance(modelclass.point.comparator, SpatialComparator))
        self.assertTrue(isinstance(modelclass.linestring.comparator, SpatialComparator))
        self.assertTrue(isinstance(modelclass.polygon.comparator, SpatialComparator))
        self.assertTrue(isinstance(modelclass.multipoint.comparator, SpatialComparator))
        self.assertTrue(isinstance(modelclass.multilinestring.comparator, SpatialComparator))
        self.assertTrue(isinstance(modelclass.multipolygon.comparator, SpatialComparator))

        # test the Table object
        table = modelclass.__table__
        self.assertTrue('id' in table.c)
        self.assertTrue('point' in table.c)
        self.assertTrue('linestring' in table.c)
        self.assertTrue('polygon' in table.c)
        self.assertTrue('multipoint' in table.c)
        self.assertTrue('multilinestring' in table.c)
        self.assertTrue('multipolygon' in table.c)
        col_point = table.c['point']
        self.assertEqual(col_point.name, 'point')
        self.assertTrue(isinstance(col_point.type, Point))
        col_linestring = table.c['linestring']
        self.assertEqual(col_linestring.name, 'linestring')
        self.assertTrue(isinstance(col_linestring.type, LineString))
        col_polygon = table.c['polygon']
        self.assertEqual(col_polygon.name, 'polygon')
        self.assertTrue(isinstance(col_polygon.type, Polygon))
        col_multipoint = table.c['multipoint']
        self.assertEqual(col_multipoint.name, 'multipoint')
        self.assertTrue(isinstance(col_multipoint.type, MultiPoint))
        col_multilinestring = table.c['multilinestring']
        self.assertEqual(col_multilinestring.name, 'multilinestring')
        self.assertTrue(isinstance(col_multilinestring.type, MultiLineString))
        col_multipolygon = table.c['multipolygon']
        self.assertEqual(col_multipolygon.name, 'multipolygon')
        self.assertTrue(isinstance(col_multipolygon.type, MultiPolygon))

        # the class should now be in the cache
        self.assertTrue(('public', self.table.name) in \
                            c2cgeoportal.lib.dbreflection._class_cache)
        _modelclass = get_class(self.table.name)
        self.assertTrue(_modelclass is modelclass)

    def test_get_class_dotted_notation(self):
        from c2cgeoportal.lib.dbreflection import get_class

        self._create_table('table_b')
        modelclass = get_class('public.table_b')

        self.assertEquals(modelclass.__name__, 'Table_b')
        self.assertEquals(modelclass.__table__.name, 'table_b')
        self.assertEquals(modelclass.__table__.schema, 'public')

    def test_mixing_get_class_and_queries(self):
        """ This test shows that we can mix the use of DBSession
        and the db reflection API. """
        from c2cgeoportal.lib.dbreflection import get_class
        from c2cgeoportal.models import DBSession
        from sqlalchemy import text
        import transaction

        self._create_table('table_c')

        DBSession.execute(text('SELECT id FROM table_c'))

        modelclass = get_class('table_c')
        self.assertEquals(modelclass.__name__, 'Table_c')

        # This commits the transaction created by DBSession.execute. This
        # is required here in the test because tearDown does table.drop,
        # which will block forever if the transaction is not committed.
        transaction.commit()
