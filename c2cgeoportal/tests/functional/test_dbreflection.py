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
        from geoalchemy import (GeometryExtensionColumn, GeometryDDL,
                                Point, Polygon)

        engine = sqlahelper.get_engine()
        Base = declarative_base(bind=engine)
        table = Table(tablename, Base.metadata,
                      Column('id', types.Integer, primary_key=True),
                      GeometryExtensionColumn('geom1', Point),
                      GeometryExtensionColumn('geom2', Polygon),
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
        from geoalchemy import Geometry, SpatialComparator
        import c2cgeoportal.lib.dbreflection
        from c2cgeoportal.lib.dbreflection import get_class

        self._create_table('table_a')
        modelclass = get_class('table_a')

        # test the class
        self.assertEquals(modelclass.__name__, 'Table_a')
        self.assertEquals(modelclass.__table__.name, 'table_a')
        self.assertEquals(modelclass.__table__.schema, 'public')
        self.assertTrue(isinstance(modelclass.geom1.comparator, SpatialComparator))
        self.assertTrue(isinstance(modelclass.geom2.comparator, SpatialComparator))

        # test the Table object
        table = modelclass.__table__
        self.assertTrue('id' in table.c)
        self.assertTrue('geom1' in table.c)
        self.assertTrue('geom2' in table.c)
        geom_col_1 = table.c['geom1']
        self.assertEqual(geom_col_1.name, 'geom1')
        self.assertTrue(isinstance(geom_col_1.type, Geometry))
        geom_col_2 = table.c['geom2']
        self.assertEqual(geom_col_2.name, 'geom2')
        self.assertTrue(isinstance(geom_col_2.type, Geometry))

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
