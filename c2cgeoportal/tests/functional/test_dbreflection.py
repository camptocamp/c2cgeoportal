# -*- coding: utf-8 -*-
from unittest import TestCase
from nose.plugins.attrib import attr

from c2cgeoportal.tests.functional import tearDownModule, setUpModule

@attr(functional=True)
class TestReflection(TestCase):

    def setUp(self):
        import sqlahelper
        from sqlalchemy import Table, Column, types
        from geoalchemy import (GeometryExtensionColumn, GeometryDDL,
                                Point, Polygon)

        Base = sqlahelper.get_base()

        table = Table('table', Base.metadata,
                      Column('id', types.Integer, primary_key=True),
                      GeometryExtensionColumn('geom1', Point),
                      GeometryExtensionColumn('geom2', Polygon),
                      )
        GeometryDDL(table)
        table.create()

        self.table = table
        self.engine = sqlahelper.get_engine()

    def tearDown(self):
        self.table.drop()

    def test_reflection(self):
        from sqlalchemy.ext.declarative import declarative_base
        from geoalchemy import Geometry, SpatialComparator
        from c2cgeoportal.lib.dbreflection import get_class

        Base = declarative_base(bind=self.engine)

        modelclass = get_class(self.table.name, Base)

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
        _modelclass = get_class(self.table.name, Base)
        self.assertTrue(_modelclass is modelclass)


