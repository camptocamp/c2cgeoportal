import functools

from sqlalchemy import Table, sql, types
from sqlalchemy.orm import relationship
from sqlalchemy.orm.util import class_mapper
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy

from geoalchemy import Geometry, GeometryColumn
from geoalchemy import (Point, LineString, Polygon,
                        MultiPoint, MultiLineString, MultiPolygon)

from papyrus.geo_interface import GeoInterface
from papyrus.xsd import tag


_class_cache = {}

_geometry_type_mappings = dict(
    [(t.name, t) for t in (Point, LineString, Polygon,
                           MultiPoint, MultiLineString, MultiPolygon)]
    )

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


def xsd_sequence_callback(tb, cls):
    from c2cgeoportal.models import DBSession
    for k, p in cls.__dict__.iteritems():
        if not isinstance(p, AssociationProxy):
            continue
        relationship_property = class_mapper(cls) \
                                    .get_property(p.target_collection)
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


def column_reflect_listener(table, column_info, engine):
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


def get_class(tablename):
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

    engine = Base.metadata.bind

    # create table and reflect it
    table = Table(tablename, Base.metadata,
                  schema=schema,
                  autoload=True,
                  autoload_with=engine,
                  listeners=[
                        ('column_reflect',
                         functools.partial(column_reflect_listener,
                                           engine=engine)
                         )
                    ]
                  )

    # create the mapped class
    cls = _create_class(table)

    # add class to cache
    _class_cache[(schema, tablename)] = cls

    return cls


def _create_class(table):

    # redefine __update__ and __read__ from GeoInterface to deal
    # with association proxies in the mapped class

    def __update__(self, feature):
        from c2cgeoportal.models import DBSession
        GeoInterface.__update__(self, feature)
        # deal with association proxies
        for k, p in self.__class__.__dict__.iteritems():
            if not isinstance(p, AssociationProxy):
                continue
            relationship_property = class_mapper(self.__class__) \
                                        .get_property(p.target_collection)
            if relationship_property.uselist:  # pragma: no cover
                raise NotImplementedError
            value = feature.properties.get(k)
            if value is not None:
                child_cls = relationship_property.argument
                obj = DBSession.query(child_cls).filter(
                    getattr(child_cls, p.value_attr) == value).first()
                if obj is not None:
                    setattr(self, p.target_collection, obj)

    def __read__(self):
        feature = GeoInterface.__read__(self)
        # deal with association proxies
        for k, p in self.__class__.__dict__.iteritems():
            if not isinstance(p, AssociationProxy):
                continue
            relationship_property = class_mapper(self.__class__) \
                                        .get_property(p.target_collection)
            if relationship_property.uselist:  # pragma: no cover
                raise NotImplementedError
            feature.properties[k] = getattr(self, k)
        return feature

    class_dict = dict(__table__=table, __update__=__update__,
                      __read__=__read__)

    cls = type(
            str(table.name.capitalize()),
            (GeoInterface, Base),
            class_dict
            )

    for col in table.columns:
        if col.foreign_keys:
            add_association_proxy(cls, col)
        elif isinstance(col.type, Geometry):
            setattr(cls, col.name, GeometryColumn(col.type))

    return cls


def add_association_proxy(cls, col):
    if len(col.foreign_keys) != 1:  # pragma: no cover
        raise NotImplementedError

    fk = next(iter(col.foreign_keys))
    tablename, _ = fk.target_fullname.rsplit('.', 1)
    child_cls = get_class(tablename)

    try:
        proxy = col.name[0:col.name.rindex('_id')]
    except ValueError:  # pragma: no cover
        proxy = col.name + '_'

    # The following is a workaround for a bug in the geojson lib. The
    # geojson lib indeed treats properties named "type" specifically
    # (this is a GeoJSON keyword), and produces a UnicodeEncodeError
    # if the property includes non-ascii characters.
    if proxy == 'type':
        proxy = 'type_'

    rel = proxy + '_'
    setattr(cls, rel, relationship(child_cls, lazy='immediate'))

    def getset_factory(collection_type, proxy):

        def getter(obj):
            if obj is None:
                return None
            return getattr(obj, proxy.value_attr)

        def setter(obj, value):
            # we should never be updating an
            # existing object
            assert False
        return getter, setter

    def creator(value):
        from c2cgeoportal.models import DBSession
        return DBSession.query(child_cls).filter(
                getattr(child_cls, proxy.value_attr) == value).first()

    setattr(cls, proxy, association_proxy(rel, 'name', creator=creator,
                                          getset_factory=getset_factory))
