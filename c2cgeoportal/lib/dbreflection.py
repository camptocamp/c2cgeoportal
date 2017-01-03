# -*- coding: utf-8 -*-

# Copyright (c) 2011-2017, Camptocamp SA
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


import functools
import warnings

from sqlalchemy import Table, sql, MetaData
from sqlalchemy.orm import relationship
from sqlalchemy.orm.util import class_mapper
from sqlalchemy.exc import SAWarning
from sqlalchemy.ext.declarative import declarative_base

from geoalchemy2 import Geometry

from papyrus.geo_interface import GeoInterface
from papyrus.xsd import tag


_class_cache = {}

Base = declarative_base()

SQL_GEOMETRY_COLUMNS = """
    SELECT
      srid,
      type
    FROM
      geometry_columns
    WHERE
      f_table_schema = :table_schema AND
      f_table_name = :table_name AND
      f_geometry_column = :geometry_column
    """


def init(engine):
    """
    Initialize the db reflection module. Give the declarative base
    class an engine, required for the reflection.
    """
    Base.metadata.bind = engine


class _AssociationProxy(object):
    # A specific "association proxy" implementation

    def __init__(self, target, value_attr):
        self.target = target
        self.value_attr = value_attr

    def __get__(self, obj, type=None):
        if obj is None:
            # For "hybrid" descriptors that work both at the instance
            # and class levels we could return an SQL expression here.
            # The code of hybrid_property in SQLAlchemy illustrates
            # how to do that.
            raise AttributeError  # pragma: no cover
        target = getattr(obj, self.target)
        return getattr(target, self.value_attr) if target else None

    def __set__(self, obj, val):
        from c2cgeoportal.models import DBSession
        o = getattr(obj, self.target)
        # if the obj as no child object or if the child object
        # does not correspond to the new value then we need to
        # read a new child object from the database
        if not o or getattr(o, self.value_attr) != val:
            relationship_property = class_mapper(obj.__class__) \
                .get_property(self.target)
            child_cls = relationship_property.argument
            o = DBSession.query(child_cls).filter(
                getattr(child_cls, self.value_attr) == val).first()
            setattr(obj, self.target, o)


def _xsd_sequence_callback(tb, cls):
    from c2cgeoportal.models import DBSession
    for k, p in cls.__dict__.iteritems():
        if not isinstance(p, _AssociationProxy):
            continue
        relationship_property = class_mapper(cls) \
            .get_property(p.target)
        target_cls = relationship_property.argument
        query = DBSession.query(getattr(target_cls, p.value_attr))
        attrs = {}
        attrs["minOccurs"] = str(0)
        attrs["nillable"] = "true"
        attrs["name"] = k
        with tag(tb, "xsd:element", attrs) as tb:
            with tag(tb, "xsd:simpleType") as tb:
                with tag(tb, "xsd:restriction",
                         {"base": "xsd:string"}) as tb:
                    for value, in query:
                        with tag(tb, "xsd:enumeration", {"value": value}):
                            pass


def _column_reflect_listener(inspector, table, column_info, engine):
    if isinstance(column_info["type"], Geometry):  # pragma: no cover
        query = engine.execute(
            sql.text(SQL_GEOMETRY_COLUMNS),
            table_schema=table.schema,
            table_name=table.name,
            geometry_column=column_info["name"]
        )
        results = query.fetchall()
        if len(results) == 1:
            column_info["type"].geometry_type = results[0][1]
            column_info["type"].srid = int(results[0][0])


def _get_schema(tablename):
    if "." in tablename:
        schema, tablename = tablename.split(".", 1)
    else:
        schema = "public"

    return tablename, schema


def get_table(tablename, schema=None, session=None):
    from c2cgeoportal.models import management

    if schema is None:
        tablename, schema = _get_schema(tablename)

    if session is not None:
        engine = session.bind.engine
        metadata = MetaData(bind=engine)
    else:
        engine = Base.metadata.bind
        metadata = Base.metadata

    # create table and reflect it
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            "Did not recognize type 'geometry' of column",
            SAWarning)
        table = Table(
            tablename, metadata,
            schema=schema,
            autoload=True,
            autoload_with=engine,
            listeners=[(
                "column_reflect",
                functools.partial(
                    _column_reflect_listener,
                    engine=engine
                )
            )] if management else []
        )
    return table


def get_class(tablename, session=None, exclude_properties=None):
    """
    Get the SQLAlchemy mapped class for "tablename". If no class exists
    for "tablename" one is created, and added to the cache. "tablename"
    must reference a valid string. If there is no table identified by
    tablename in the database a NoSuchTableError SQLAlchemy exception
    is raised.
    """
    if exclude_properties is None:
        exclude_properties = []
    tablename, schema = _get_schema(tablename)
    cache_key = (schema, tablename, ",".join(exclude_properties))

    if cache_key in _class_cache:
        return _class_cache[cache_key]

    table = get_table(tablename, schema, session)

    # create the mapped class
    cls = _create_class(table, exclude_properties)

    # add class to cache
    _class_cache[cache_key] = cls

    return cls


def _create_class(table, exclude_properties=None):

    if exclude_properties is None:  # pragma: nocover
        exclude_properties = []
    cls = type(
        str(table.name.capitalize()),
        (GeoInterface, Base),
        dict(
            __table__=table,
            __mapper_args__={"exclude_properties": exclude_properties}
        ),
    )

    for col in table.columns:
        if col.foreign_keys and col.name not in exclude_properties:
            _add_association_proxy(cls, col)

    return cls


def _add_association_proxy(cls, col):
    if len(col.foreign_keys) != 1:  # pragma: no cover
        raise NotImplementedError

    fk = next(iter(col.foreign_keys))
    child_tablename, child_pk = fk.target_fullname.rsplit(".", 1)
    child_cls = get_class(child_tablename)

    try:
        proxy = col.name[0:col.name.rindex("_id")]
    except ValueError:  # pragma: no cover
        proxy = col.name + "_"

    # The following is a workaround for a bug in the geojson lib. The
    # geojson lib indeed treats properties named "type" specifically
    # (this is a GeoJSON keyword), and produces a UnicodeEncodeError
    # if the property includes non-ascii characters.
    if proxy == "type":
        proxy = "type_"  # pragma: no cover

    rel = proxy + "_"
    primaryjoin = (getattr(cls, col.name) == getattr(child_cls, child_pk))
    relationship_ = relationship(child_cls, primaryjoin=primaryjoin,
                                 lazy="immediate")
    setattr(cls, rel, relationship_)

    setattr(cls, proxy, _AssociationProxy(rel, "name"))

    if cls.__add_properties__ is None:
        cls.__add_properties__ = [proxy]
    else:
        cls.__add_properties__.append(proxy)
