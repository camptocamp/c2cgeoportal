# -*- coding: utf-8 -*-

# Copyright (c) 2013-2018, Camptocamp SA
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.


import re
from unittest import TestCase

from tests.functional import (  # noqa
    teardown_common as teardown_module,
    setup_common as setup_module)


class TestReflection(TestCase):

    _tables = None

    def setup_method(self, _):
        setup_module()
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None
        self.metadata = None

    def teardown_method(self, _):
        import c2cgeoportal_geoportal.lib.dbreflection

        if self._tables is not None:
            for table in self._tables[::-1]:
                table.drop()
                # table.drop(checkfirst=True)

        # clear the dbreflection class cache
        c2cgeoportal_geoportal.lib.dbreflection._class_cache = {}

    def _create_table(self, tablename):
        """ Test functions use this function to create a table object.
        Each test function should call this function only once. And
        there should not be two test functions that call this function
        with the same ptable_name value.
        """
        from c2cgeoportal_commons.models.main import Base
        from sqlalchemy import Table, Column, ForeignKey, types
        from geoalchemy2 import Geometry

        if self._tables is None:
            self._tables = []

        ctable = Table(
            "{0!s}_child".format(tablename), Base.metadata,
            Column("id", types.Integer, primary_key=True),
            Column("name", types.Unicode),
            schema="public"
        )
        ctable.create(checkfirst=True)
        self._tables.append(ctable)

        ptable = Table(
            tablename, Base.metadata,
            Column("id", types.Integer, primary_key=True),
            Column(
                "child1_id", types.Integer,
                ForeignKey("public.{0!s}_child.id".format(tablename))
            ),
            Column(
                "child2_id", types.Integer,
                ForeignKey("public.{0!s}_child.id".format(tablename)),
                nullable=False
            ),
            Column("point", Geometry("POINT")),
            Column("linestring", Geometry("LINESTRING")),
            Column("polygon", Geometry("POLYGON")),
            Column("multipoint", Geometry("MULTIPOINT")),
            Column("multilinestring", Geometry("MULTILINESTRING")),
            Column("multipolygon", Geometry("MULTIPOLYGON")),
            schema="public"
        )
        ptable.create(checkfirst=True)
        self._tables.append(ptable)

        self.metadata = Base.metadata

    def test_get_class_nonexisting_table(self):
        from sqlalchemy.exc import NoSuchTableError
        import c2cgeoportal_geoportal.lib.dbreflection
        from c2cgeoportal_geoportal.lib.dbreflection import get_class

        self.assertRaises(NoSuchTableError, get_class, "nonexisting")
        self.assertEqual(c2cgeoportal_geoportal.lib.dbreflection._class_cache, {})

    def test_get_class(self):
        from geoalchemy2 import Geometry
        import c2cgeoportal_geoportal.lib.dbreflection
        from c2cgeoportal_geoportal.lib.dbreflection import get_class, _AssociationProxy

        self._create_table("table_a")
        modelclass = get_class("table_a")

        # test the class
        self.assertEqual(modelclass.__name__, "Table_a")
        self.assertEqual(modelclass.__table__.name, "table_a")
        self.assertEqual(modelclass.__table__.schema, "public")

        self.assertTrue(isinstance(modelclass.point.type, Geometry))
        self.assertTrue(isinstance(modelclass.linestring.type, Geometry))
        self.assertTrue(isinstance(modelclass.polygon.type, Geometry))
        self.assertTrue(isinstance(modelclass.multipoint.type, Geometry))
        self.assertTrue(isinstance(modelclass.multilinestring.type, Geometry))
        self.assertTrue(isinstance(modelclass.multipolygon.type, Geometry))

        self.assertTrue(isinstance(modelclass.child1, _AssociationProxy))
        self.assertTrue(modelclass.child1.nullable)
        self.assertTrue(isinstance(modelclass.child2, _AssociationProxy))
        self.assertFalse(modelclass.child2.nullable)

        # test the Table object
        table = modelclass.__table__
        self.assertTrue("id" in table.c)
        self.assertTrue("child1_id" in table.c)
        self.assertTrue("child2_id" in table.c)
        self.assertTrue("point" in table.c)
        self.assertTrue("linestring" in table.c)
        self.assertTrue("polygon" in table.c)
        self.assertTrue("multipoint" in table.c)
        self.assertTrue("multilinestring" in table.c)
        self.assertTrue("multipolygon" in table.c)
        col_child1_id = table.c["child1_id"]
        self.assertEqual(col_child1_id.name, "child1_id")
        col_child2_id = table.c["child2_id"]
        self.assertEqual(col_child2_id.name, "child2_id")
        col_point = table.c["point"]
        self.assertEqual(col_point.name, "point")
        self.assertEqual(col_point.type.geometry_type, "POINT")
        col_linestring = table.c["linestring"]
        self.assertEqual(col_linestring.name, "linestring")
        self.assertEqual(col_linestring.type.geometry_type, "LINESTRING")
        col_polygon = table.c["polygon"]
        self.assertEqual(col_polygon.name, "polygon")
        self.assertEqual(col_polygon.type.geometry_type, "POLYGON")
        col_multipoint = table.c["multipoint"]
        self.assertEqual(col_multipoint.name, "multipoint")
        self.assertEqual(col_multipoint.type.geometry_type, "MULTIPOINT")
        col_multilinestring = table.c["multilinestring"]
        self.assertEqual(col_multilinestring.name, "multilinestring")
        self.assertEqual(col_multilinestring.type.geometry_type, "MULTILINESTRING")
        col_multipolygon = table.c["multipolygon"]
        self.assertEqual(col_multipolygon.name, "multipolygon")
        self.assertEqual(col_multipolygon.type.geometry_type, "MULTIPOLYGON")

        # the class should now be in the cache
        self.assertTrue(
            ("public", "table_a", "", None) in
            c2cgeoportal_geoportal.lib.dbreflection._class_cache
        )
        _modelclass = get_class("table_a")
        self.assertTrue(_modelclass is modelclass)

    def test_get_class_dotted_notation(self):
        from c2cgeoportal_geoportal.lib.dbreflection import get_class

        self._create_table("table_b")
        modelclass = get_class("public.table_b")

        self.assertEqual(modelclass.__name__, "Table_b")
        self.assertEqual(modelclass.__table__.name, "table_b")
        self.assertEqual(modelclass.__table__.schema, "public")

    def test_mixing_get_class_and_queries(self):
        """ This test shows that we can mix the use of DBSession
        and the db reflection API. """
        from c2cgeoportal_geoportal.lib.dbreflection import get_class
        from c2cgeoportal_commons.models import DBSession
        from sqlalchemy import text
        import transaction

        self._create_table("table_c")

        DBSession.execute(text("SELECT id FROM table_c"))

        modelclass = get_class("table_c")
        self.assertEqual(modelclass.__name__, "Table_c")

        # This commits the transaction created by DBSession.execute. This
        # is required here in the test because tearDown does table.drop,
        # which will block forever if the transaction is not committed.
        transaction.commit()

    def test_get_class_exclude_properties(self):
        import c2cgeoportal_geoportal.lib.dbreflection
        from c2cgeoportal_geoportal.lib.dbreflection import get_class

        self._create_table("table_d")
        get_class("table_d", exclude_properties=["foo", "bar"])

        # the class should now be in the cache
        self.assertTrue(
            ("public", "table_d", "foo,bar", None) in
            c2cgeoportal_geoportal.lib.dbreflection._class_cache
        )


class TestXSDSequenceCallback(TestCase):

    _tables = None

    def setup_method(self, _):
        import transaction
        from sqlalchemy import Column, types, ForeignKey
        from sqlalchemy.orm import relationship
        from sqlalchemy.ext.declarative import declarative_base
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_geoportal.lib.dbreflection import _AssociationProxy

        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None

        Base = declarative_base(bind=DBSession.c2c_rw_bind)  # noqa

        class Child(Base):
            __tablename__ = "child"
            id = Column(types.Integer, primary_key=True)
            name = Column(types.Unicode)

            def __init__(self, name):
                self.name = name

        class Parent(Base):
            __tablename__ = "parent"
            id = Column(types.Integer, primary_key=True)
            child1_id = Column(types.Integer, ForeignKey("child.id"))
            child2_id = Column(types.Integer, ForeignKey("child.id"))
            child1_ = relationship(Child, primaryjoin=(child1_id == Child.id))
            child1 = _AssociationProxy("child1_", "name")
            child2_ = relationship(Child, primaryjoin=(child2_id == Child.id))
            child2 = _AssociationProxy("child2_", "name", nullable=False)

        Child.__table__.create()
        Parent.__table__.create()
        self._tables = [Parent.__table__, Child.__table__]

        DBSession.add_all([Child("foo"), Child("bar")])
        transaction.commit()
        self.metadata = Base.metadata
        self.cls = Parent

    def teardown_method(self, _):
        import transaction
        transaction.commit()

        if self._tables is not None:
            for table in self._tables:
                table.drop()

    def test_xsd_sequence_callback(self):
        from xml.etree.ElementTree import TreeBuilder, tostring
        from c2cgeoportal_geoportal.lib.dbreflection import xsd_sequence_callback
        from papyrus.xsd import tag
        tb = TreeBuilder()
        with tag(tb, "xsd:sequence") as tb:
            xsd_sequence_callback(tb, self.cls)
        e = tb.close()
        self.assertIsNotNone(re.search(
            '<xsd:element name="child2">'
            '<xsd:simpleType>'
            '<xsd:restriction base="xsd:string">'
            '<xsd:enumeration value="foo" />'
            '<xsd:enumeration value="bar" />'
            '</xsd:restriction>'
            '</xsd:simpleType>'
            '</xsd:element>',
            tostring(e).decode("utf-8"),
        ))
        self.assertIsNotNone(re.search(
            '<xsd:element minOccurs="0" name="child1" nillable="true">'
            '<xsd:simpleType>'
            '<xsd:restriction base="xsd:string">'
            '<xsd:enumeration value="foo" />'
            '<xsd:enumeration value="bar" />'
            '</xsd:restriction>'
            '</xsd:simpleType>'
            '</xsd:element>',
            tostring(e).decode("utf-8"),
        ))
