import functools
import warnings

from sqlalchemy import Table, sql, types, MetaData
from sqlalchemy.orm import relationship
from sqlalchemy.orm.util import class_mapper
from sqlalchemy.exc import SAWarning
from sqlalchemy.ext.declarative import declarative_base

from geoalchemy import Geometry, GeometryColumn
from geoalchemy import (Point, LineString, Polygon,
                        MultiPoint, MultiLineString, MultiPolygon)

from papyrus.geo_interface import GeoInterface
from papyrus.xsd import tag


_class_cache = {}

_geometry_type_mappings = dict(
    [(t.name, t) for t in (Point, LineString, Polygon,
                           MultiPoint, MultiLineString, MultiPolygon)])

Base = declarative_base()

SQL_GEOMETRY_COLUMNS = """
    SELECT
      f_table_schema,
      f_table_name,
      f_geometry_column,
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


class _association_proxy(object):
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
            raise AttributeError  # pragma: nocover
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
        if not isinstance(p, _association_proxy):
            continue
        relationship_property = class_mapper(cls) \
            .get_property(p.target)
        target_cls = relationship_property.argument
        query = DBSession.query(getattr(target_cls, p.value_attr))
        attrs = {}
        attrs['minOccurs'] = str(0)
        attrs['nillable'] = 'true'
        attrs['name'] = k
        with tag(tb, 'xsd:element', attrs) as tb:
            with tag(tb, 'xsd:simpleType') as tb:
                with tag(tb, 'xsd:restriction',
                         {'base': 'xsd:string'}) as tb:
                    for value, in query:
                        with tag(tb, 'xsd:enumeration', {'value': value}):
                            pass


def _column_reflect_listener(table, column_info, engine):
    if isinstance(column_info['type'], types.NullType):

        # SQLAlchemy set type to NullType, which means SQLAlchemy does not know
        # the type advertized by the database. This may be a PostGIS geometry
        # colum, which we verify by querying the geometry_columns table. If
        # this is a geometry column we set "type" to an actual Geometry object.

        query = engine.execute(sql.text(SQL_GEOMETRY_COLUMNS),
                               table_schema=table.schema,
                               table_name=table.name,
                               geometry_column=column_info['name'])
        results = query.fetchall()
        if len(results) == 1:
            geometry_type = _geometry_type_mappings[results[0][4]]
            column_info['type'] = geometry_type(srid=results[0][3])


def get_table(tablename, DBSession=None):
    # TODO: factorize with get_class
    if '.' in tablename:
        schema, tablename = tablename.split('.', 1)
    else:
        schema = 'public'

    if DBSession is not None:
        engine = DBSession.bind.engine
        metadata = MetaData(bind=engine)
    else:
        engine = Base.metadata.bind
        metadata = Base.metadata

    # create table and reflect it
    with warnings.catch_warnings():
        warnings.filterwarnings(
            'ignore',
            "Did not recognize type 'geometry' of column",
            SAWarning)
        table = Table(
            tablename, metadata,
            schema=schema,
            autoload=True,
            autoload_with=engine,
            listeners=[(
                'column_reflect',
                functools.partial(
                    _column_reflect_listener,
                    engine=engine))
            ]
        )
    return table


def get_class(tablename, DBSession=None):
    """
    Get the SQLAlchemy mapped class for "tablename". If no class exists
    for "tablename" one is created, and added to the cache. "tablename"
    must reference a valid string. If there's no table identified by
    tablename in the database a NoSuchTableError SQLAlchemy exception
    is raised.
    """

    if '.' in tablename:
        schema, tablename = tablename.split('.', 1)
    else:
        schema = 'public'

    if (schema, tablename) in _class_cache:
        return _class_cache[(schema, tablename)]

    if DBSession is not None:
        engine = DBSession.bind.engine
        metadata = MetaData(bind=engine)
    else:
        engine = Base.metadata.bind
        metadata = Base.metadata

    # create table and reflect it
    with warnings.catch_warnings():
        warnings.filterwarnings(
            'ignore',
            "Did not recognize type 'geometry' of column",
            SAWarning)
        table = Table(
            tablename, metadata,
            schema=schema,
            autoload=True,
            autoload_with=engine,
            listeners=[(
                'column_reflect',
                functools.partial(
                    _column_reflect_listener,
                    engine=engine))
            ]
        )

    # create the mapped class
    cls = _create_class(table)

    # add class to cache
    _class_cache[(schema, tablename)] = cls

    return cls


def _create_class(table):

    cls = type(
        str(table.name.capitalize()),
        (GeoInterface, Base),
        dict(__table__=table)
    )

    for col in table.columns:
        if col.foreign_keys:
            _add_association_proxy(cls, col)
        elif isinstance(col.type, Geometry):
            setattr(cls, col.name, GeometryColumn(col.type))

    return cls


def _add_association_proxy(cls, col):
    if len(col.foreign_keys) != 1:  # pragma: no cover
        raise NotImplementedError

    fk = next(iter(col.foreign_keys))
    child_tablename, child_pk = fk.target_fullname.rsplit('.', 1)
    child_cls = get_class(child_tablename)

    try:
        proxy = col.name[0:col.name.rindex('_id')]
    except ValueError:  # pragma: no cover
        proxy = col.name + '_'

    # The following is a workaround for a bug in the geojson lib. The
    # geojson lib indeed treats properties named "type" specifically
    # (this is a GeoJSON keyword), and produces a UnicodeEncodeError
    # if the property includes non-ascii characters.
    if proxy == 'type':
        proxy = 'type_'  # pragma: no cover

    rel = proxy + '_'
    primaryjoin = (getattr(cls, col.name) == getattr(child_cls, child_pk))
    relationship_ = relationship(child_cls, primaryjoin=primaryjoin,
                                 lazy='immediate')
    setattr(cls, rel, relationship_)

    setattr(cls, proxy, _association_proxy(rel, 'name'))

    if cls.__add_properties__ is None:
        cls.__add_properties__ = [proxy]
    else:
        cls.__add_properties__.append(proxy)
