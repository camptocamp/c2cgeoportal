from unittest import TestCase

from nose.plugins.attrib import attr

from c2cgeoportal.tests.functional import setUpModule, tearDownModule


#@attr(functional=True)
class TestXSD(TestCase):

    def setUp(self):
        import sqlahelper
        from sqlalchemy import Table, Column, types
        from geoalchemy import GeometryDDL, GeometryExtensionColumn, Point

        Base = sqlahelper.get_base()

        table = Table('spots', Base.metadata,
                      Column('id', types.Integer, primary_key=True),
                      Column('name', types.String),
                      Column('abbreviation', types.String(4)),
                      Column('height', types.Integer),
                      Column('color', types.Enum('red', 'green', 'blue')),
                      Column('balance', types.Numeric(5, 2)),
                      GeometryExtensionColumn('geom', Point))
        GeometryDDL(table)
        self.table = table

    def test_xsd(self):
        from StringIO import StringIO
        from c2cgeoportal.lib.xsd import get_table_xsd
        from xml.etree.ElementTree import XML

        xsd = get_table_xsd(StringIO(), self.table).getvalue()
        xml = XML(xsd)
        self.assertEquals(xml.tag, '{http://www.w3.org/2001/XMLSchema}schema')

        pretty_xsd = get_table_xsd(StringIO(), self.table, pretty=True).getvalue()
        pretty_xml = XML(pretty_xsd)
        self.assertEquals(pretty_xml.tag, '{http://www.w3.org/2001/XMLSchema}schema')

        # FIXME add more tests :-)
