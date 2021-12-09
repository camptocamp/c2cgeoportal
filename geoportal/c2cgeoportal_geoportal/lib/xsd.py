# Copyright (c) 2018-2021, Camptocamp SA
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


from io import BytesIO
from typing import Any, Callable, Dict, Optional, Type, Union, cast

import sqlalchemy.sql.schema
from papyrus.xsd import XSDGenerator as PapyrusXSDGenerator
from papyrus.xsd import tag
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.orm.util import class_mapper


class XSDGenerator(PapyrusXSDGenerator):  # type: ignore
    """Extends the PapyrusXSDGenerator."""

    def add_class_properties_xsd(self, tb: str, cls: DeclarativeMeta) -> None:
        """
        Add the XSD for the class properties to the ``TreeBuilder``.

        And call the user ``sequence_callback``.
        """
        mapper = class_mapper(cls)
        properties = []
        if cls.__attributes_order__:
            for attribute_name in cls.__attributes_order__:
                attr = mapper.attrs.get(attribute_name)
                if attr:
                    properties.append(attr)

            # Add other attributes
            for p in mapper.iterate_properties:
                if p not in properties:
                    properties.append(p)
        else:
            properties = mapper.iterate_properties

        for p in properties:
            if isinstance(p, ColumnProperty):
                self.add_column_property_xsd(tb, p)

        if self.sequence_callback:
            self.sequence_callback(tb, cls)

    def add_column_property_xsd(self, tb: str, column_property: ColumnProperty) -> None:
        column = column_property.columns[0]
        if column.foreign_keys:
            self.add_association_proxy_xsd(tb, column_property)
            return

        super().add_column_property_xsd(tb, column_property)

    def add_association_proxy_xsd(self, tb: str, column_property: ColumnProperty) -> None:
        from c2cgeoportal_commons.models import DBSession  # pylint: disable=import-outside-toplevel

        column = column_property.columns[0]
        proxy = column.info["association_proxy"]
        attribute = column_property.class_attribute
        cls = attribute.parent.entity
        association_proxy = getattr(cls, proxy)
        relationship_property = class_mapper(cls).get_property(association_proxy.target)
        target_cls = relationship_property.argument
        query = DBSession.query(getattr(target_cls, association_proxy.value_attr))
        if association_proxy.order_by is not None:
            query = query.order_by(getattr(target_cls, association_proxy.order_by))
        attrs = {}
        if association_proxy.nullable:
            attrs["minOccurs"] = "0"
            attrs["nillable"] = "true"
        attrs["name"] = proxy
        with tag(tb, "xsd:element", attrs) as tb2:
            with tag(tb2, "xsd:simpleType") as tb3:
                with tag(tb3, "xsd:restriction", {"base": "xsd:string"}) as tb4:
                    for (value,) in query:
                        with tag(tb4, "xsd:enumeration", {"value": value}):
                            pass
            self.element_callback(tb4, column)

    def element_callback(self, tb: str, column: sqlalchemy.sql.schema.Column) -> None:
        if column.info.get("readonly"):
            with tag(tb, "xsd:annotation"):
                with tag(tb, "xsd:appinfo"):
                    with tag(tb, "readonly", {"value": "true"}):
                        pass


class XSD:
    """The XSD file generator on a pyramid view."""

    def __init__(
        self,
        include_primary_keys: bool = False,
        include_foreign_keys: bool = False,
        sequence_callback: Optional[str] = None,
        element_callback: Optional[str] = None,
    ):
        self.generator = XSDGenerator(
            include_primary_keys=include_primary_keys,
            include_foreign_keys=include_foreign_keys,
            sequence_callback=sequence_callback,
            element_callback=element_callback,
        )

    def __call__(
        self, table: str
    ) -> Callable[[Union[Type[str], Type[bytes]], Dict[str, Any]], Optional[bytes]]:
        def _render(cls: Union[Type[str], Type[bytes]], system: Dict[str, Any]) -> Optional[bytes]:
            request = system.get("request")
            if request is not None:
                response = request.response
                response.content_type = "application/xml"
                io = self.generator.get_class_xsd(BytesIO(), cls)
                return cast(bytes, io.getvalue())
            return None

        return _render
