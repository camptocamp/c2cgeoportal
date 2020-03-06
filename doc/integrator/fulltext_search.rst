.. _integrator_fulltext_search:

Full-text search
================

The full-text search table
--------------------------

The *text search* feature uses a dedicated PostgreSQL table. The full-text search table is named ``tsearch``
(for *text search*) and is in the application-specific schema.

You do not need to create the table yourself, as it was already created during application installation
(see the section :ref:`integrator_install_application`).


Populate the full-text search table
-----------------------------------

Here is an example of an insertion in the ``tsearch`` table:

.. code:: sql

    INSERT INTO app_schema.tsearch
      (the_geom, layer_name, label, public, role_id, lang, ts)
    VALUES (
       ST_GeomFromText('POINT(2660000 1140000)', 2056),
       'Group',
       'text to display',
       't',
       NULL,
       'fr',
       to_tsvector('french', regexp_replace('text to search', E'[\\[\\]\\(\\):&\\*]', ' ', 'g'))
    );

Where ``Layer group`` is the name of the layer group that should be activated,
``text to display`` is the text that is displayed in the results,
``test to search`` is the text that we search for,
``french`` is the used language.

Here is another example where rows from a ``SELECT`` are inserted:

.. code:: sql

    INSERT INTO app_schema.tsearch
      (the_geom, layer_name, label, public, role_id, lang, ts)
    SELECT
      geom,
      'layer group name',
      text,
      't',
      NULL,
      'de',
      to_tsvector('german', regexp_replace(text, E'[\\[\\]\\(\\):&\\*]', ' ', 'g'))
    FROM table;

.. note::

    The language string used as the first argument to the ``to_tsvector``
    function should match that defined in the ``default_locale_name`` variable of
    the application configuration (``vars.yaml``). For example, if you have
    "french" text in the database the application's ``default_locale_name`` should
    be ``fr``. In other words c2cgeoportal assumes that the database language
    and the application's default language match.


Populate with the themes
------------------------

A script is available to fill the full-text search table, for more information type:

.. prompt:: bash

   docker-compose exec geoportal theme2fts --help


Security
--------

The ``tsearch`` table includes two security-related columns, namely ``public``
and ``role_id``. If ``public`` is ``true`` then the row is available to any
user, including anonymous users. And in that case, the ``role_id`` column is
ignored by ``c2cgeoportal``. If ``public`` is ``false`` then the row is not
available to anonymous users. If ``role_id`` is ``NULL``, the row is available
to any authenticated user. If ``role_id`` is not ``NULL``, the row is only
available to users of the corresponding role.

.. note::

    If you want to restrict some data to specific roles, then you will need to
    insert that data multiple times. For example, if you want to make the data
    of a table *text-searchable*, and restrict that data to the roles whose ids
    are ``1`` and ``2`` you will use two SQL ``INSERT`` statements:

    .. code:: sql

        INSERT INTO app_schema.tsearch
           (the_geom, layer_name, label, public, role_id, lang, ts)
        SELECT
           geom,
           'layer group name',
           text,
           'f',
           1,
           'de',
           to_tsvector('german', regexp_replace(text, E'[\\[\\]\\(\\):&\\*]', ' ', 'g'))
        FROM table;

        INSERT INTO app_schema.tsearch
           (the_geom, layer_name, label, public, role_id, lang, ts)
        SELECT
           geom,
           'layer group name',
           text,
           'f',
           2,
           'de',
           to_tsvector('german', regexp_replace(text, E'[\\[\\]\\(\\):&\\*]', ' ', 'g'))
        FROM table;


.. _integrator_fulltext_search_params:

Params
------

The ``params`` column can contain a JSON with a dictionary of parameters.
For instance to specify a ``floor``:

.. code:: json

    {
        "floor": "1"
    }

Query string ``floor=1`` is then automatically appended to all WMS requests.


Actions
-------

The ``actions`` column contains a JSON with an array of actions like:

.. code:: json

    {
        "action": "add_layer",
        "data": "<the_layer_name>"
    }

.. code:: json

    {
        "action": "add_group",
        "data": "<the_group_name>"
    }

.. code:: json

    {
        "action": "add_theme",
        "data": "<the_theme_name>"
    }

Example of ``SQL`` ``INSERT`` of ``actions`` data to add the layer "cadastre" on the map:

.. code:: sql

   INSERT INTO app_schema.tsearch (..., actions)
   VALUES (..., '[{"action": "add_layer", "data": "cadastre"}]')


Interface
---------

If the ``interface_id`` column contains a value, it means that the result is only for this interface.


Lang
----

If the ``lang`` column contains a value, it means that the result is only for this language.


Configuration
-------------

In the configuration file ``vars.yaml`` you can add the following variables:

*  ``fulltextsearch_defaultlimit`` the default limit on the results, default is 30.
*  ``fulltextsearch_maxlimit`` the max possible limit, default is 200.


Ranking system
--------------

By default, the full-text search uses the `similarity` system of the
`pg_trgm module <https://www.postgresql.org/docs/9.0/static/pgtrgm.html>`_. This
is based only on the similarities of words, without language analysis, and it
cares only about how near your search is to the result. `12` is nearer to `12`
than `120`.

Ensure that the extension is created in you database:

.. prompt:: bash

  sudo -u postgres psql -c "CREATE EXTENSION pg_trgm" <db_name>

Alternatively, you can use the ``tsvector`` and ``ts_rank_cd`` to rank your search
results
(see: `textsearch-controls <https://www.postgresql.org/docs/9.0/static/textsearch-controls.html>`_).
These methods are useful to handle language-based strings. That means for instance
that plural nouns are the same as singular nouns. This system only checks if
your search word exists in the result. That means that if you search `B 12 Zug`,
`B 120 Zug` has the same weight because the system only see that the `12` exists
in each case. To use this system, your request must contains the
parameter ``rank_system=ts_rank_cd``.


Using the unaccent extension
----------------------------

By the default the full-text search is accent-sensitive.
To make it accent-insensitive Postgres's
`unaccent extension <https://www.postgresql.org/docs/9.0/static/unaccent.html>`_
can be used.

First connect to the database:

.. prompt:: bash

    sudo -u postgres psql -d <database>

For that we need the Postgres unaccent extension and dictionary:

.. code:: sql

    CREATE EXTENSION unaccent;

Insert the unaccent dictionary into a text search configuration
(`Documentation <https://www.postgresql.org/docs/9.1/static/sql-altertsconfig.html>`_):

.. code:: sql

    CREATE TEXT SEARCH CONFIGURATION fr (COPY = french);
    ALTER TEXT SEARCH CONFIGURATION fr
        ALTER MAPPING FOR hword, hword_part, word
        WITH unaccent, french_stem;

When populating the ``tsearch`` table use the text configuration 'fr'
instead of 'french'. For example:

.. code:: sql

    INSERT INTO <schema>.tsearch
      (the_geom, layer_name, label, public, role_id, ts)
    VALUES
      (ST_GeomFromText('POINT(2660000 1140000)', 2056), 'Layer group',
       'Accent text to display (éàè)', 't', NULL, to_tsvector('fr', 'Accent text to search (éàè)'));

And define the configuration in the ``vars.yaml`` file:

.. code:: yaml

    fulltextsearch:
        languages:
            fr: fr

``fr: fr`` is a link between the pyramid language and the text search configuration, by default it is
``fr: french`` because the default french text search configuration is named 'french'.


Synonym and Thesaurus Dictionary
--------------------------------

You may wish to avoid using the Synonym and Thesaurus dictionaries, because when these are used,
a word like 'alignement' is simplified as 'align':

.. code:: sql

   SELECT to_tsvector('fr', 'alignement');
   'align':1

Thus, 'alignem' does not match in the search, which might be considered unexpected behavior by users:

.. code:: sql

   SELECT to_tsquery('fr', 'alignem:*');
   'alignem':*

The change this behavior, you can create and use a new dictionary named `french_alt`:

.. code:: sql

   CREATE TEXT SEARCH DICTIONARY french_alt (TEMPLATE = pg_catalog.simple);
   ALTER TEXT SEARCH DICTIONARY french_alt (STOPWORDS = french);
   ALTER TEXT SEARCH CONFIGURATION fr ALTER MAPPING FOR asciiword WITH french_alt;

.. note::

   We keep the stop words to remove the French short words.
