.. _integrator_fulltext_search:

Full-text search
================

Enabling the *full-text search* feature involves adding a ``FullTextSearch``
plugin to the viewer, and creating and populating a dedicated table in the
database.

The FullTextSearch plugin
-------------------------

The viewer should include a ``FullTextSearch`` plugin for the *text search*
feature to be available in the user interface.

See the `FullTextSearch API doc
<http://docs.camptocamp.net/cgxp/lib/plugins/FullTextSearch.html>`_ for the
list of options the plugin can receive.

*The main viewer includes a FullTextSearch plugin by default.*

The full-text search table
--------------------------

The *text search* feature requires a dedicated PostgreSQL table. The full-text
search table should be named ``tsearch`` (for *text search*) and should be in
the application-specific schema.

You don't need to create the table yourself, as it is created by the
``create_db`` command line (see the section
:ref:`integrator_install_application`).

If you did want to create the table manually you'd use the following commands::

    $ sudo -u postgres psql -c "CREATE TABLE <schema_name>.tsearch (
        id SERIAL PRIMARY KEY,
        layer_name TEXT,
        label TEXT,
        public BOOLEAN DEFAULT 't',
        role_id INTEGER REFERENCES <schema_name>.role,
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
      (the_geom, layer_name, label, public, role_id, ts)
    VALUES
      (ST_GeomFromText('POINT(2660000 1140000)', 21781), 'Layer group',
       'text to display', 't', NULL, to_tsvector('french', 'text to search'));

Where ``Layer group`` is the name of the layer group that should be activated,
``text to display`` is the text that is displayed in the results,
``test to search`` is the text that we search for,
``french`` is the used language.

Here's another example where rows from a ``SELECT`` are inserted::

    INSERT INTO app_schema.tsearch
      (the_geom, layer_name, label, public, role_id, ts)
    SELECT
      geom, 'layer group name', text, 't', NULL, to_tsvector('german', text)
    FROM table;

.. note::

    The language string used as the first argument to the ``to_tsvector``
    function should match that defined in the ``default_locale_name`` variable of
    the application configuration (``config.yaml``). For example if you have
    "french" text in the database the application's ``default_locale_name`` should
    be ``fr``. In other words c2cgeoportal assumes that the database language
    and the application's default language match.

Security
--------

The ``tsearch`` table includes two security-related columns, namely ``public``
and ``role_id``. If ``public`` is ``true`` then the row is available to any
user, including anonymous users. And in that case, the ``role_id`` column is
ignored by ``c2cgeoportal``. If ``public`` is ``false`` then the row isn't
available to anonymous users. If ``role_id`` is ``NULL``, the row is available
to any authenticated user. If ``role_id`` is not ``NULL``, the row is only
available to users of the corresponding role.
