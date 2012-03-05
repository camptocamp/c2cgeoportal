# -*- coding: utf-8 -*-
from unittest import TestCase
from nose.plugins.attrib import attr

from c2cgeoportal.tests.functional import tearDownModule, setUpModule

@attr(functional=True)
class TestReflection(TestCase):

    def setUp(self):
        import sqlahelper
        from sqlalchemy import Table, Column, types
        from sqlalchemy.ext.declarative import declarative_base
        from geoalchemy import (GeometryExtensionColumn, GeometryDDL,
                                Point, Polygon)
        from c2cgeoportal.lib.dbreflection import init

        # get a reference to the engine created by the module-level
        # setUp function
        engine = sqlahelper.get_engine()

        Base = declarative_base(bind=engine)
        table = Table('table', Base.metadata,
                      Column('id', types.Integer, primary_key=True),
                      GeometryExtensionColumn('geom1', Point),
                      GeometryExtensionColumn('geom2', Polygon),
                      )
        GeometryDDL(table)
        table.create()

        self.table = table
        init(engine)

    def tearDown(self):
        self.table.drop()

    def test_get_class_nonexisting_table(self):
        from sqlalchemy.exc import NoSuchTableError
        from c2cgeoportal.lib.dbreflection import get_class

        self.assertRaises(NoSuchTableError, get_class, 'nonexisting')

    def test_get_class(self):
        from geoalchemy import Geometry, SpatialComparator
        from c2cgeoportal.lib.dbreflection import get_class

        modelclass = get_class(self.table.name)

        # test the class
        self.assertEquals(modelclass.__name__, 'Table')
        self.assertEquals(modelclass.__table__.name, self.table.name)
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
        _modelclass = get_class(self.table.name)
        self.assertTrue(_modelclass is modelclass)


