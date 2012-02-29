import functools

from sqlalchemy import Table, sql, types
from sqlalchemy.engine import reflection
from geoalchemy import Geometry

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
        results = engine.execute(sql.text(SQL_GEOMETRY_COLUMNS),
                                 table_schema='public',
                                 table_name=table.name,
                                 geometry_column=column_info['name']).fetchall()
        if len(results) == 1:
            result = results[0]
            column_info['type'] = Geometry(srid=result[3])

def reflecttable(tablename, engine, metadata):
    """
    Create a Table object for the database table "tablename", using reflection.
    """
    return Table(
        tablename,
        metadata,
        autoload=True,
        autoload_with=engine,
        listeners=[
            ('column_reflect',
             functools.partial(column_reflect_listener, engine=engine))
            ]
        )

