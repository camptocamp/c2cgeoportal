.. _integrator_fulltext_search:

Full-text search
================

If *full-text search* is enabled in the application, a PostgreSQL table
dedicated to full-text search is required.

The full-text search table
--------------------------

This full-text search table should be named ``tsearch`` (for *text search*) and
should be in the application-specific schema.

You don't need to create the table yourself, as it is created by the
``create_db`` command line (see the section
:ref:`integrator_install_application`).

If you did want to create the table manually you'd use the following commands::

    $ sudo -u postgres psql -c "CREATE TABLE <schema_name>.tsearch (
        id SERIAL PRIMARY KEY,
        layer_name TEXT,
        label TEXT,
        ts TSVECTOR);" <db_name>
    $ sudo -u postgres psql -c "SELECT AddGeometryColumn('<schema_name>', 'tsearch', 'the_geom', <srid>, 'GEOMETRY', 2);" <db_name>
    $ sudo -u postgres psql -c "CREATE INDEX tsearch_ts_idx ON <schema_name>.tsearch USING gin(ts);" <db_name>

with ``<schema_name>``, ``<srid>``, and ``<db_name>``  substituted as appropriate.

Also make sure that the db user can ``SELECT`` in the ``tsearch`` table::

    $ sudo -u postgres psql -c "GRANT SELECT ON TABLE <schema_name>.tsearch TO "<db_user>";" <db_name>

with ``<db_user>``, and ``<db_name>`` substituded as appropriately.

Populate the full-text search table
-----------------------------------

Here's an example of an insertion in the ``tsearch`` table::

    INSERT INTO app_schema.tsearch
      (the_geom, layer_name, label, ts)
    VALUES
      (ST_GeomFromText('POINT(2660000 1140000)', 21781, 'Layer group',
       'text to display', to_tsvector('french', 'text to search'));

Where ``Layer group`` is the name of the layer group that should be activated,
``text to display`` is the text that is displayed in the results,
``test to search`` is the text that we search for,
``french`` is the used language.

Here's another example where rows from a ``SELECT`` are inserted::

    INSERT INTO app_schema.tsearch
      (the_geom, layer_name, label, ts)
    SELECT
      geom, 21781, 'layer group name', text, to_tsvector('german', text)
    FROM table;

.. note::

    The language string used as the first argument to the ``to_tsvector``
    function should match that defined in the ``default_language`` variable of
    the Buildout configuration. For example if you have "french" text in the
    database the application's ``default_language`` should be ``fr``. In other
    words c2cgeoportal assumes that the database language and the application's
    default language match.
