# Copyright (c) 2013-2025, Camptocamp SA
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

from c2cgeoportal_geoportal.lib.caching import init_region

from tests.functional import setup_common as setup_module
from tests.functional import teardown_common as teardown_module  # noqa


class TestReflection(TestCase):
    _tables = None

    def setup_method(self, _) -> None:
        setup_module()
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None
        self.metadata = None

    def teardown_method(self, _) -> None:
        from c2cgeoportal_commons.models import DBSession

        if self._tables is not None:
            for table in self._tables[::-1]:
                table.drop(bind=DBSession.c2c_rw_bind)

    def _create_table(self, tablename):
        """
        Test functions use this function to create a table object.

        Each test function should call this function only once. And there should not be two test functions
        that call this function with the same ptable_name value.
        """
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import Base
        from geoalchemy2 import Geometry
        from sqlalchemy import Column, ForeignKey, Table, types

        if self._tables is None:
            self._tables = []

        ctable = Table(
            f"{tablename!s}_child",
            Base.metadata,
            Column("id", types.Integer, primary_key=True),
            Column("name", types.Unicode),
            schema="public",
        )
        ctable.create(checkfirst=True, bind=DBSession.c2c_rw_bind)
        self._tables.append(ctable)

        ptable = Table(
            tablename,
            Base.metadata,
            Column("id", types.Integer, primary_key=True),
            Column("child1_id", types.Integer, ForeignKey(f"public.{tablename!s}_child.id")),
            Column(
                "child2_id",
                types.Integer,
                ForeignKey(f"public.{tablename!s}_child.id"),
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
        ptable.create(checkfirst=True, bind=DBSession.c2c_rw_bind)
        self._tables.append(ptable)

        self.metadata = Base.metadata

    def test_get_class_nonexisting_table(self) -> None:
        from c2cgeoportal_geoportal.lib.dbreflection import get_class
        from sqlalchemy.exc import NoSuchTableError

        self.assertRaises(NoSuchTableError, get_class, "nonexisting")

    def test_get_class(self) -> None:
        from c2cgeoportal_geoportal.lib.dbreflection import _AssociationProxy, get_class
        from geoalchemy2 import Geometry

        init_region({"backend": "dogpile.cache.memory"}, "std")
        init_region({"backend": "dogpile.cache.memory"}, "obj")
        init_region({"backend": "dogpile.cache.memory"}, "ogc-server")

        self._create_table("table_a")
        modelclass = get_class("table_a")

        # test the class
        assert modelclass.__name__.startswith("Table_a_")
        assert modelclass.__table__.name == "table_a"
        assert modelclass.__table__.schema == "public"

        assert isinstance(modelclass.point.type, Geometry)
        assert isinstance(modelclass.linestring.type, Geometry)
        assert isinstance(modelclass.polygon.type, Geometry)
        assert isinstance(modelclass.multipoint.type, Geometry)
        assert isinstance(modelclass.multilinestring.type, Geometry)
        assert isinstance(modelclass.multipolygon.type, Geometry)

        assert isinstance(modelclass.child1, _AssociationProxy)
        assert modelclass.child1.nullable
        assert modelclass.child1_id.info.get("association_proxy") == "child1"
        assert isinstance(modelclass.child2, _AssociationProxy)
        assert not modelclass.child2.nullable
        assert modelclass.child2_id.info.get("association_proxy") == "child2"

        child1_asso_proxy = getattr(modelclass, modelclass.child1_id.info["association_proxy"])
        assert child1_asso_proxy.value_attr == "name"
        assert child1_asso_proxy.order_by == "name"

        # test the Table object
        table = modelclass.__table__
        assert "id" in table.c
        assert "child1_id" in table.c
        assert "child2_id" in table.c
        assert "point" in table.c
        assert "linestring" in table.c
        assert "polygon" in table.c
        assert "multipoint" in table.c
        assert "multilinestring" in table.c
        assert "multipolygon" in table.c
        col_child1_id = table.c["child1_id"]
        assert col_child1_id.name == "child1_id"
        col_child2_id = table.c["child2_id"]
        assert col_child2_id.name == "child2_id"
        col_point = table.c["point"]
        assert col_point.name == "point"
        assert col_point.type.geometry_type == "POINT"
        col_linestring = table.c["linestring"]
        assert col_linestring.name == "linestring"
        assert col_linestring.type.geometry_type == "LINESTRING"
        col_polygon = table.c["polygon"]
        assert col_polygon.name == "polygon"
        assert col_polygon.type.geometry_type == "POLYGON"
        col_multipoint = table.c["multipoint"]
        assert col_multipoint.name == "multipoint"
        assert col_multipoint.type.geometry_type == "MULTIPOINT"
        col_multilinestring = table.c["multilinestring"]
        assert col_multilinestring.name == "multilinestring"
        assert col_multilinestring.type.geometry_type == "MULTILINESTRING"
        col_multipolygon = table.c["multipolygon"]
        assert col_multipolygon.name == "multipolygon"
        assert col_multipolygon.type.geometry_type == "MULTIPOLYGON"

        assert get_class("table_a") is modelclass

    def test_get_class_dotted_notation(self) -> None:
        from c2cgeoportal_geoportal.lib.dbreflection import get_class

        self._create_table("table_b")
        modelclass = get_class("public.table_b")

        assert modelclass.__name__.startswith("Table_b_")
        assert modelclass.__table__.name == "table_b"
        assert modelclass.__table__.schema == "public"

    def test_mixing_get_class_and_queries(self) -> None:
        """This test shows that we can mix the use of DBSession and the db reflection API."""
        import transaction
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_geoportal.lib.dbreflection import get_class
        from sqlalchemy import text

        self._create_table("table_c")

        DBSession.execute(text("SELECT id FROM table_c"))

        modelclass = get_class("table_c")
        assert modelclass.__name__.startswith("Table_c_")

        # This commits the transaction created by DBSession.execute. This
        # is required here in the test because tearDown does table.drop,
        # which will block forever if the transaction is not committed.
        transaction.commit()

    def test_get_class_exclude_properties(self) -> None:
        from c2cgeoportal_geoportal.lib.dbreflection import get_class

        self._create_table("table_d")
        assert get_class("table_d", exclude_properties=["foo", "bar"]) is not None

    def test_get_class_attributes_order(self) -> None:
        from c2cgeoportal_geoportal.lib.dbreflection import get_class

        attributes_order = ["child1_id", "point", "child2_id"]

        self._create_table("table_d")
        cls = get_class("table_d", attributes_order=attributes_order)

        assert attributes_order == cls.__attributes_order__

    def test_get_class_enumerations_config(self) -> None:
        from c2cgeoportal_geoportal.lib.dbreflection import get_class

        enumerations_config = {"child1_id": {"value": "id", "order_by": "name"}}

        self._create_table("table_d")
        cls = get_class("table_d", enumerations_config=enumerations_config)

        assert enumerations_config == cls.__enumerations_config__
        association_proxy = getattr(cls, cls.child1_id.info["association_proxy"])
        assert association_proxy.value_attr == "id"
        assert association_proxy.order_by == "name"

        # Without order_by.
        enumerations_config = {"child1_id": {"value": "id"}}
        cls = get_class("table_d", enumerations_config=enumerations_config)

        association_proxy = getattr(cls, cls.child1_id.info["association_proxy"])
        assert association_proxy.value_attr == "id"
        assert association_proxy.order_by == "id"

    def test_get_class_readonly_attributes(self) -> None:
        from c2cgeoportal_geoportal.lib.dbreflection import get_class

        readonly_attributes = ["child1_id", "point"]

        self._create_table("table_d")
        cls = get_class("table_d", readonly_attributes=readonly_attributes)

        assert True is cls.child1_id.info.get("readonly")
        assert True is cls.point.info.get("readonly")
