.. _administrator_database:

Create and prepare the database
===============================

Any c2cgeoportal application requires a PostgreSQL/PostGIS database. The
application works with its own tables, which store users, layers, etc. These
tables are located in a specific schema of the database.

.. note::

    Multiple specific schemas are actually used in a parent/child architecture.

If the application has MapServer layers linked to PostGIS tables, these tables
and the application-specfic tables must be in the same database, preferably in
separate schemas. This is required for layer access control (*restricted
layers*), where joining user/role tables to PostGIS layer tables is necessary.

Create the database
-------------------

To create the database you can use::

    sudo -u postgres createdb <db_name> -T template_postgis

with ``<db_name>`` replaced by the actual database name.

To create the application-specific schema use::

    sudo -u postgres psql -c "CREATE SCHEMA <schema_name>;" <db_name>

with ``<db_name>`` and ``<schema_name>`` replaced by the actual database name,
and schema name, respectively.

Create a database user
----------------------

You probably want to create a specific database user for the application. This
can be done with this command::

    sudo -u postgres createuser -P <db_user>

Create the full-text search table
---------------------------------

If *full-text search* is enabled in the application a table dedicated to
full-text search table is needed in the database. This table must be named
``tsearch`` (for *text search*) and must be in the application-specific schema.

To create the table the following SQL should be used::

    CREATE TABLE <schema_name>.tsearch (
      id SERIAL PRIMARY KEY,
      layer_name TEXT,
      label TEXT,
      ts TSVECTOR);
    SELECT AddGeometryColumn('<schema_name>', 'tsearch', 'the_geom', <srid>, 'GEOMETRY', 2);
    CREATE INDEX tsearch_ts_idx ON <schema_name>.tsearch USING gin(ts);
    GRANT SELECT ON TABLE $${vars:schema}.tsearch TO "<db_user>";

with ``<schema_name>``, ``<srid>``, and ``<db_user>`` substituted as
appropriate.

Here's an example of an insertion in the ``tsearch`` table::

    INSERT INTO app_schema.tsearch
      (the_geom, layer_name, label, ts)
    VALUES
      (ST_GeomFromText('POINT(2660000 1140000)', 21781, 'Layer name',
       'text to display', to_tsvector('german', 'text to search'));

Here's another example where rows from a ``SELECT`` are inserted::

    INSERT INTO app_schema.tsearch
      (the_geom, layer_name, label, ts)
    SELECT
      geom, 21781, 'layer group name', text, to_tsvector('german', text)
    FROM table;
