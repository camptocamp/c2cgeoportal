# -*- coding: utf-8 -*-
from unittest import TestCase
from nose.plugins.attrib import attr

from c2cgeoportal.tests.functional import tearDownModule, setUpModule

@attr(functional=True)
class TestReflection(TestCase):

    def setUp(self):
        import sqlahelper
        from sqlalchemy import Table, Column, types
        from geoalchemy import GeometryExtensionColumn, GeometryDDL, Polygon

        Base = sqlahelper.get_base()

        table = Table('table', Base.metadata,
                      Column('id', types.Integer, primary_key=True),
                      GeometryExtensionColumn('geom', Polygon)
                      )
        GeometryDDL(table)
        table.create()

        self.table = table
        self.engine = sqlahelper.get_engine()

    def tearDown(self):
        self.table.drop()

    def test_reflection(self):
        from sqlalchemy.ext.declarative import declarative_base
        from geoalchemy import Geometry
        from c2cgeoportal.lib.dbreflection import reflecttable

        Base = declarative_base(bind=self.engine)

        modelclass = reflecttable(self.table.name, Base)

        self.assertEquals(modelclass.__name__, 'Table')
        self.assertEquals(modelclass.__table__.name, self.table.name)

        table = modelclass.__table__

        self.assertTrue('id' in table.c)
        self.assertTrue('geom' in table.c)

        geom_col = table.c['geom']
        self.assertEqual(geom_col.name, 'geom')
        self.assertTrue(isinstance(geom_col.type, Geometry))
