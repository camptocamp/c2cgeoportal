# Copyright (c) 2011-2024, Camptocamp SA
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

import random
import threading
import warnings
from collections.abc import Iterable
from typing import Any, Union

import sqlalchemy.ext.declarative
from papyrus.geo_interface import GeoInterface
from sqlalchemy import Column, Integer, MetaData, Table
from sqlalchemy.exc import SAWarning
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import Session
from sqlalchemy.orm.util import class_mapper

from c2cgeoportal_geoportal.lib.caching import get_region

CACHE_REGION_OBJ = get_region("obj")
SQL_GEOMETRY_COLUMNS = """
    SELECT srid, type
    FROM geometry_columns
    WHERE
      f_table_schema = :table_schema AND
      f_table_name = :table_name AND
      f_geometry_column = :geometry_column
    """


class _AssociationProxy:
    # A specific "association proxy" implementation

    def __init__(self, target: str, value_attr: str, nullable: bool = True, order_by: str | None = None):
        self.target = target
        self.value_attr = value_attr
        self.nullable = nullable
        self.order_by = order_by

    def __get__(
        self,
        obj: sqlalchemy.ext.declarative.ConcreteBase,
        type_: sqlalchemy.ext.declarative.DeclarativeMeta | None = None,
    ) -> Union["_AssociationProxy", str] | None:
        if obj is None:
            # For "hybrid" descriptors that work both at the instance
            # and class levels we could return an SQL expression here.
            # The code of hybrid_property in SQLAlchemy illustrates
            # how to do that.
            return self
        target = getattr(obj, self.target)
        return getattr(target, self.value_attr) if target else None

    def __set__(self, obj: str, val: str) -> None:
        from c2cgeoportal_commons.models import DBSession  # pylint: disable=import-outside-toplevel

        assert DBSession is not None

        o = getattr(obj, self.target)
        # if the obj as no child object or if the child object
        # does not correspond to the new value then we need to
        # read a new child object from the database
        if not o or getattr(o, self.value_attr) != val:
            relationship_property = class_mapper(obj.__class__).get_property(self.target)
            child_cls = relationship_property.argument
            o = DBSession.query(child_cls).filter(getattr(child_cls, self.value_attr) == val).first()
            setattr(obj, self.target, o)


def _get_schema(tablename: str) -> tuple[str, str]:
    if "." in tablename:
        schema, tablename = tablename.split(".", 1)
    else:
        schema = "public"

    return tablename, schema


_get_table_lock = threading.RLock()


def get_table(
    tablename: str,
    schema: str | None = None,
    session: Session | None = None,
    primary_key: str | None = None,
) -> Table:
    """Build an SQLAlchemy table."""
    if schema is None:
        tablename, schema = _get_schema(tablename)

    if session is not None:
        assert session.bind is not None
        engine = session.bind.engine
        metadata = MetaData()
    else:
        from c2cgeoportal_commons.models import Base  # pylint: disable=import-outside-toplevel
        from c2cgeoportal_commons.models import DBSession  # pylint: disable=import-outside-toplevel

        assert DBSession is not None
        assert DBSession.bind is not None

        engine = DBSession.bind.engine
        metadata = Base.metadata

    # create table and reflect it
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", "Did not recognize type 'geometry' of column", SAWarning)
        args = []
        if primary_key is not None:
            # Ensure we have a primary key to be able to edit views
            args.append(Column(primary_key, Integer, primary_key=True))
        with _get_table_lock:
            table = Table(
                tablename,
                metadata,
                *args,
                schema=schema,
                autoload_with=engine,
                keep_existing=True,
            )
    return table


@CACHE_REGION_OBJ.cache_on_arguments()
def get_class(
    tablename: str,
    exclude_properties: list[str] | None = None,
    primary_key: str | None = None,
    attributes_order: list[str] | None = None,
    enumerations_config: dict[str, str] | None = None,
    readonly_attributes: list[str] | None = None,
) -> type:
    """
    Get the SQLAlchemy mapped class for "tablename".

    If no class exists for "tablename" one is created, and added to the cache. "tablename" must reference a
    valid string. If there is no table identified by tablename in the database a NoSuchTableError SQLAlchemy
    exception is raised.
    """

    tablename, schema = _get_schema(tablename)

    table = get_table(tablename, schema, None, primary_key=primary_key)

    # create the mapped class
    cls = _create_class(
        table,
        exclude_properties=exclude_properties,
        attributes_order=attributes_order,
        enumerations_config=enumerations_config,
        readonly_attributes=readonly_attributes,
    )

    return cls


def _create_class(
    table: Table,
    exclude_properties: Iterable[str] | None = None,
    attributes_order: list[str] | None = None,
    enumerations_config: dict[str, str] | None = None,
    readonly_attributes: list[str] | None = None,
    pk_name: str | None = None,
) -> type:
    from c2cgeoportal_commons.models import Base  # pylint: disable=import-outside-toplevel

    exclude_properties = exclude_properties or ()
    attributes = {
        "__table__": table,
        "__mapper_args__": {"exclude_properties": exclude_properties},
        "__attributes_order__": attributes_order,
        "__enumerations_config__": enumerations_config,
    }
    if pk_name is not None:
        attributes[pk_name] = Column(Integer, primary_key=True)
    # The randint is to fix the SAWarning: This declarative base already contains a class with the same
    # class name and module name
    cls = type(
        f"{table.name.capitalize()}_{random.randint(0, 9999999)}",  # nosec
        (GeoInterface, Base),
        attributes,
    )

    for col in table.columns:
        if col.name in (readonly_attributes or []):
            col.info["readonly"] = True
        if col.foreign_keys and col.name not in exclude_properties:
            _add_association_proxy(cls, col)

    return cls


def _add_association_proxy(cls: type[Any], col: sqlalchemy.sql.schema.Column[Any]) -> None:
    if len(col.foreign_keys) != 1:
        raise NotImplementedError

    fk = next(iter(col.foreign_keys))
    child_tablename, child_pk = fk.target_fullname.rsplit(".", 1)
    child_cls = get_class(child_tablename)

    try:
        proxy = col.name[0 : col.name.rindex("_id")]
    except ValueError:
        proxy = col.name + "_"

    # The following is a workaround for a bug in the geojson lib. The
    # geojson lib indeed treats properties named "type" specifically
    # (this is a GeoJSON keyword), and produces a UnicodeEncodeError
    # if the property includes non-ascii characters.
    if proxy == "type":
        proxy = "type_"

    rel = proxy + "_"
    primaryjoin = getattr(cls, col.name) == getattr(child_cls, child_pk)
    relationship_ = relationship(child_cls, primaryjoin=primaryjoin, lazy="immediate")
    setattr(cls, rel, relationship_)

    nullable = True
    cls_column_property = getattr(cls, col.name).property
    for column in cls_column_property.columns:
        nullable = nullable and column.nullable

    value_attr = "name"
    order_by = value_attr

    if cls.__enumerations_config__ and col.name in cls.__enumerations_config__:
        enumeration_config = cls.__enumerations_config__[col.name]
        if "value" in enumeration_config:
            value_attr = enumeration_config["value"]
            order_by = value_attr
        if "order_by" in enumeration_config:
            order_by = enumeration_config["order_by"]

    setattr(cls, proxy, _AssociationProxy(rel, value_attr, nullable=nullable, order_by=order_by))

    if cls.__add_properties__ is None:
        cls.__add_properties__ = [proxy]
    else:
        cls.__add_properties__.append(proxy)

    col.info["association_proxy"] = proxy
