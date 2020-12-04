# -*- coding: utf-8 -*-

# Copyright (c) 2013-2019, Camptocamp SA
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

# pylint: disable=missing-docstring,attribute-defined-outside-init,protected-access


from unittest import TestCase

from tests.functional import setup_common as setup_module
from tests.functional import teardown_common as teardown_module  # noqa

from c2cgeoportal_geoportal.lib.caching import init_region


class TestReflection(TestCase):

    _tables = None

    def setup_method(self, _):
        setup_module()
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None
        self.metadata = None

    def teardown_method(self, _):
        if self._tables is not None:
            for table in self._tables[::-1]:
                table.drop()

    def _create_table(self, tablename):
        """Test functions use this function to create a table object.
        Each test function should call this function only once. And
        there should not be two test functions that call this function
        with the same ptable_name value.
        """
        from geoalchemy2 import Geometry
        from sqlalchemy import Column, ForeignKey, Table, types

        from c2cgeoportal_commons.models.main import Base

        if self._tables is None:
            self._tables = []

        ctable = Table(
            "{0!s}_child".format(tablename),
            Base.metadata,
            Column("id", types.Integer, primary_key=True),
            Column("name", types.Unicode),
            schema="public",
        )
        ctable.create(checkfirst=True)
        self._tables.append(ctable)

        ptable = Table(
            tablename,
            Base.metadata,
            Column("id", types.Integer, primary_key=True),
            Column("child1_id", types.Integer, ForeignKey("public.{0!s}_child.id".format(tablename))),
            Column(
                "child2_id",
                types.Integer,
                ForeignKey("public.{0!s}_child.id".format(tablename)),
                nullable=False,
            ),
            Column("point", Geometry("POINT")),
            Column("linestring", Geometry("LINESTRING")),
            Column("polygon", Geometry("POLYGON")),
            Column("multipoint", Geometry("MULTIPOINT")),
            Column("multilinestring", Geometry("MULTILINESTRING")),
            Column("multipolygon", Geometry("MULTIPOLYGON")),
            schema="public",
        )
        ptable.create(checkfirst=True)
        self._tables.append(ptable)

        self.metadata = Base.metadata

    def test_get_class_nonexisting_table(self):
        from sqlalchemy.exc import NoSuchTableError

        from c2cgeoportal_geoportal.lib.dbreflection import get_class

        self.assertRaises(NoSuchTableError, get_class, "nonexisting")

    def test_get_class(self):
        from geoalchemy2 import Geometry

        from c2cgeoportal_geoportal.lib.dbreflection import _AssociationProxy, get_class

        init_region({"backend": "dogpile.cache.memory"}, "std")
        init_region({"backend": "dogpile.cache.memory"}, "obj")

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
        self.assertEqual(modelclass.child1_id.info.get("association_proxy"), "child1")
        self.assertTrue(isinstance(modelclass.child2, _AssociationProxy))
        self.assertFalse(modelclass.child2.nullable)
        self.assertEqual(modelclass.child2_id.info.get("association_proxy"), "child2")

        child1_asso_proxy = getattr(modelclass, modelclass.child1_id.info["association_proxy"])
        self.assertEqual("name", child1_asso_proxy.value_attr)
        self.assertEqual("name", child1_asso_proxy.order_by)

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

        assert get_class("table_a") is modelclass

    def test_get_class_dotted_notation(self):
        from c2cgeoportal_geoportal.lib.dbreflection import get_class

        self._create_table("table_b")
        modelclass = get_class("public.table_b")

        self.assertEqual(modelclass.__name__, "Table_b")
        self.assertEqual(modelclass.__table__.name, "table_b")
        self.assertEqual(modelclass.__table__.schema, "public")

    def test_mixing_get_class_and_queries(self):
        """This test shows that we can mix the use of DBSession
        and the db reflection API."""
        import transaction
        from sqlalchemy import text

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_geoportal.lib.dbreflection import get_class

        self._create_table("table_c")

        DBSession.execute(text("SELECT id FROM table_c"))

        modelclass = get_class("table_c")
        self.assertEqual(modelclass.__name__, "Table_c")

        # This commits the transaction created by DBSession.execute. This
        # is required here in the test because tearDown does table.drop,
        # which will block forever if the transaction is not committed.
        transaction.commit()

    def test_get_class_exclude_properties(self):
        from c2cgeoportal_geoportal.lib.dbreflection import get_class

        self._create_table("table_d")
        assert get_class("table_d", exclude_properties=["foo", "bar"]) is not None

    def test_get_class_attributes_order(self):
        from c2cgeoportal_geoportal.lib.dbreflection import get_class

        attributes_order = ["child1_id", "point", "child2_id"]

        self._create_table("table_d")
        cls = get_class("table_d", attributes_order=attributes_order)

        self.assertEqual(attributes_order, cls.__attributes_order__)

    def test_get_class_enumerations_config(self):
        from c2cgeoportal_geoportal.lib.dbreflection import get_class

        enumerations_config = {"child1_id": {"value": "id", "order_by": "name"}}

        self._create_table("table_d")
        cls = get_class("table_d", enumerations_config=enumerations_config)

        self.assertEqual(enumerations_config, cls.__enumerations_config__)
        association_proxy = getattr(cls, cls.child1_id.info["association_proxy"])
        self.assertEqual("id", association_proxy.value_attr.key)
        self.assertEqual("name", association_proxy.order_by.key)

        # Without order_by.
        enumerations_config = {"child1_id": {"value": "id"}}
        cls = get_class("table_d", enumerations_config=enumerations_config)

        association_proxy = getattr(cls, cls.child1_id.info["association_proxy"])
        self.assertEqual("id", association_proxy.value_attr.key)
        self.assertEqual("id", association_proxy.order_by.key)

    def test_get_class_readonly_attributes(self):
        from c2cgeoportal_geoportal.lib.dbreflection import get_class

        readonly_attributes = ["child1_id", "point"]

        self._create_table("table_d")
        cls = get_class("table_d", readonly_attributes=readonly_attributes)

        self.assertEqual(True, cls.child1_id.info.get("readonly"))
        self.assertEqual(True, cls.point.info.get("readonly"))
