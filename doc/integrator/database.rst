.. _administrator_database:

The database in c2cgeoportal
============================

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

Create and populate the database::
    
    sudo -u postgres buildout/bin/create_db CONST_production.ini -p

Set the version::

    sudo -u postgres ./buildout/bin/manage_db version_control --VERSION `./buildout/bin/manage_db version`

with ``<db_name>`` and ``<schema_name>`` replaced by the actual database name,
and schema name, respectively.

Create a database user
----------------------

You probably want to create a specific database user for the application. This
can be done with this command::

    sudo -u postgres createuser -P <db_user>

Give the rights to the user::

    sudo -u postgres psql -c "GRANT USAGE ON SCHEMA <schema_name> TO \"<db_user>\";" <db_name>
    sudo -u postgres psql -c "GRANT ALL ON ALL TABLES IN SCHEMA <schema_name> TO \"<db_user>\";" <db_name>

Create the full-text search table
---------------------------------

If *full-text search* is enabled in the application a table dedicated to
full-text search table is needed in the database. This table must be named
``tsearch`` (for *text search*) and must be in the application-specific schema.

To create the table the following SQL should be used::

    sudo -u postgres psql -c "CREATE TABLE <schema_name>.tsearch (
      id SERIAL PRIMARY KEY,
      layer_name TEXT,
      label TEXT,
      ts TSVECTOR);" <db_name>
    sudo -u postgres psql -c "SELECT AddGeometryColumn('<schema_name>', 'tsearch', 'the_geom', <srid>, 'GEOMETRY', 2);" <db_name>
    sudo -u postgres psql -c "CREATE INDEX tsearch_ts_idx ON <schema_name>.tsearch USING gin(ts);" <db_name>
    sudo -u postgres psql -c "GRANT SELECT ON TABLE <schema_name>.tsearch TO "<db_user>";" <db_name>

with ``<schema_name>``, ``<srid>``, and ``<db_user>`` substituted as
appropriate.

Here's an example of an insertion in the ``tsearch`` table::

    INSERT INTO app_schema.tsearch
      (the_geom, layer_name, label, ts)
    VALUES
      (ST_GeomFromText('POINT(2660000 1140000)', 21781, 'Layer group',
       'text to display', to_tsvector('french', 'text to search'));

Where ``Layer group`` is the name of the layer group that should be acctivate,
``text to display`` is the text thai is display in the results,
``test ot search`` is the text that we search for,
``french`` is the use language.

Here's another example where rows from a ``SELECT`` are inserted::

    INSERT INTO app_schema.tsearch
      (the_geom, layer_name, label, ts)
    SELECT
      geom, 21781, 'layer group name', text, to_tsvector('german', text)
    FROM table;


Database version management
---------------------------

Acctually we use sqlalchemy-migrate to manage our database updates.
http://code.google.com/p/sqlalchemy-migrate/

With our structure the standars scripte don't work than we need to use
``./buildout/bin/manage_db``.

To get the database version available in the application code::

    ./buildout/bin/manage_db version

The verions of the database::

    ./buildout/bin/manage_db db_version

Upgrade the database::

    ./buildout/bin/manage_db upgrade

More help and commands::

    ./buildout/bin/manage_db help

