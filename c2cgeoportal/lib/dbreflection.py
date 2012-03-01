import functools

from sqlalchemy import Table, sql, types
from sqlalchemy.engine import reflection
from geoalchemy import Geometry, GeometryColumn

from papyrus.geo_interface import GeoInterface

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

def column_reflect_listener(table, column_info, engine):
    if isinstance(column_info['type'], types.NullType):

        # SQLAlchemy set type to NullType, which means SQLAlchemy does not know
        # the type advertized by the database. This may be a PostGIS geometry
        # colum, which we verify by querying the geometry_columns table. If
        # this is a geometry column we set "type" to an actual Geometry object.

        results = engine.execute(sql.text(SQL_GEOMETRY_COLUMNS),
                                 table_schema='public',
                                 table_name=table.name,
                                 geometry_column=column_info['name']).fetchall()
        if len(results) == 1:
            column_info['type'] = Geometry(srid=results[0][3])

def get_class(tablename, Base):
    """
    Get the SQLAlchemy mapped class for "tablename".
    """
    engine = Base.metadata.bind

    # create table and reflect it
    table = Table(tablename, Base.metadata,
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
    cls = type(
            tablename.capitalize(),
            (GeoInterface, Base),
            dict(__table__=table)
            )

    # override the mapped class' geometry columns
    for col in table.columns:
        if isinstance(col.type, Geometry):
            setattr(cls, col.name, GeometryColumn(col.type))

    return cls
