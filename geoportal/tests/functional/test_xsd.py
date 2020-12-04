# -*- coding: utf-8 -*-

# Copyright (c) 2018-2019, Camptocamp SA
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

# pylint: disable=missing-docstring,attribute-defined-outside-init,protected-access,attribute-defined-outside-init


from unittest import TestCase
from unittest.mock import Mock, patch

from tests.functional import setup_common as setup_module
from tests.functional import teardown_common as teardown_module  # noqa


class TestXSDGenerator(TestCase):

    _tables = None

    def setup_method(self, _):
        setup_module()

        import transaction
        from sqlalchemy import Column, ForeignKey, types
        from sqlalchemy.ext.declarative import declarative_base
        from sqlalchemy.orm import relationship

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
            custom_order = Column(types.Integer)

            def __init__(self, name, custom_order):
                self.name = name
                self.custom_order = custom_order

        class Parent(Base):
            __tablename__ = "parent"
            id = Column(types.Integer, primary_key=True)
            child1_id = Column(types.Integer, ForeignKey("child.id"))
            child2_id = Column(types.Integer, ForeignKey("child.id"))
            other = Column(types.String)
            readonly = Column(types.String, info={"readonly": True})
            child1_ = relationship(Child, primaryjoin=(child1_id == Child.id))
            child1 = _AssociationProxy("child1_", "name")
            child1_id.info["association_proxy"] = "child1"
            child2_ = relationship(Child, primaryjoin=(child2_id == Child.id))
            child2 = _AssociationProxy("child2_", "name", nullable=False, order_by="custom_order")
            child2_id.info["association_proxy"] = "child2"

        Child.__table__.create()
        Parent.__table__.create()
        self._tables = [Parent.__table__, Child.__table__]

        DBSession.add_all([Child("foo", 2), Child("zad", 1), Child("bar", 2)])
        transaction.commit()
        self.metadata = Base.metadata
        self.cls = Parent

    def teardown_method(self, _):
        import transaction

        transaction.commit()

        if self._tables is not None:
            for table in self._tables:
                table.drop()

    @patch("c2cgeoportal_geoportal.lib.xsd.XSDGenerator.add_column_property_xsd")
    def test_add_class_properties_xsd_column_order(self, column_mock):
        from c2cgeoportal_geoportal.lib.xsd import XSDGenerator

        tb = Mock()
        self.cls.__attributes_order__ = ["child1_id", "other"]

        gen = XSDGenerator(include_foreign_keys=True)
        gen.add_class_properties_xsd(tb, self.cls)

        called_properties = [kall[0][1].class_attribute.name for kall in column_mock.call_args_list]
        assert len(called_properties) == 5
        assert self.cls.__attributes_order__ == called_properties[: len(self.cls.__attributes_order__)]

    @patch("c2cgeoportal_geoportal.lib.xsd.XSDGenerator.add_association_proxy_xsd")
    @patch("c2cgeoportal_geoportal.lib.xsd.PapyrusXSDGenerator.add_column_property_xsd")
    def test_add_column_property_xsd(self, column_mock, proxy_mock):
        from sqlalchemy.orm.util import class_mapper

        from c2cgeoportal_geoportal.lib.xsd import XSDGenerator

        gen = XSDGenerator(include_foreign_keys=True)

        tb = Mock()
        mapper = class_mapper(self.cls)

        p = mapper.attrs["child1_id"]
        gen.add_column_property_xsd(tb, p)
        proxy_mock.assert_called_once_with(tb, p)

        p = mapper.attrs["other"]
        gen.add_column_property_xsd(tb, p)
        column_mock.assert_called_once_with(tb, p)

    def test_add_column_readonly(self):
        from xml.etree.ElementTree import TreeBuilder, tostring

        from sqlalchemy.orm.util import class_mapper

        from c2cgeoportal_geoportal.lib.xsd import XSDGenerator

        gen = XSDGenerator(include_foreign_keys=True)
        mapper = class_mapper(self.cls)
        tb = TreeBuilder()

        p = mapper.attrs["readonly"]
        gen.add_column_property_xsd(tb, p)
        e = tb.close()

        self.assertEqual(
            '<xsd:element name="readonly" minOccurs="0" nillable="true" type="xsd:string">'
            "<xsd:annotation>"
            "<xsd:appinfo>"
            '<readonly value="true" />'
            "</xsd:appinfo>"
            "</xsd:annotation>"
            "</xsd:element>",
            tostring(e).decode("utf-8"),
        )

    def test_add_association_proxy_xsd(self):
        from xml.etree.ElementTree import TreeBuilder, tostring

        from sqlalchemy.orm.util import class_mapper

        from c2cgeoportal_geoportal.lib.xsd import XSDGenerator

        gen = XSDGenerator(include_foreign_keys=True)

        mapper = class_mapper(self.cls)

        tb = TreeBuilder()
        gen.add_association_proxy_xsd(tb, mapper.attrs["child1_id"])
        e = tb.close()

        self.assertEqual(
            '<xsd:element minOccurs="0" nillable="true" name="child1">'
            "<xsd:simpleType>"
            '<xsd:restriction base="xsd:string">'
            '<xsd:enumeration value="foo" />'
            '<xsd:enumeration value="zad" />'
            '<xsd:enumeration value="bar" />'
            "</xsd:restriction>"
            "</xsd:simpleType>"
            "</xsd:element>",
            tostring(e).decode("utf-8"),
        )

        # Test child 2 with an order by.
        mapper = class_mapper(self.cls)

        tb = TreeBuilder()
        gen.add_association_proxy_xsd(tb, mapper.attrs["child2_id"])
        e = tb.close()

        self.assertEqual(
            '<xsd:element name="child2">'
            "<xsd:simpleType>"
            '<xsd:restriction base="xsd:string">'
            '<xsd:enumeration value="zad" />'
            '<xsd:enumeration value="foo" />'
            '<xsd:enumeration value="bar" />'
            "</xsd:restriction>"
            "</xsd:simpleType>"
            "</xsd:element>",
            tostring(e).decode("utf-8"),
        )
