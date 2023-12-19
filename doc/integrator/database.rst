.. _integrator_database:

Database
========

Update lifecycle
----------------

The recommended setup is to have integration and production data on the same database, using
separate schemas. This setup allows for simpler switches between integration and production.

The recommended setup for the ``static`` schema is to have exactly one schema for integration
and one for production, e.-g.:
``integration_static`` for the integration environment,
and ``production_static`` for production environment.

For the data of the ``main`` schema, we recommend to have one schema for each version of the application.
The following example shows how an update can be performed from a version ``2019`` to a version ``2020``:

+-------------------------+-------------------------------+------------------------------+
|                         | Integration schema name       | Production schema name       |
+=========================+===============================+==============================+
| Initial state           | main_2019                     | main_2019                    |
+-------------------------+-------------------------------+------------------------------+
| Start a new version     | main_2020                     | main_2019                    |
+-------------------------+-------------------------------+------------------------------+
| Do the changes          | main_2020                     | main_2019                    |
+-------------------------+-------------------------------+------------------------------+
| Publish the new version | main_2020                     | main_2020                    |
+-------------------------+-------------------------------+------------------------------+


Initial state
~~~~~~~~~~~~~

Starting point is that the current version is the same on integration and production => ``main_2019``.


Prepare the project
~~~~~~~~~~~~~~~~~~~

To be able to proceed like this, the variables ``PGSCHEMA`` and the ``DOCKER_PGSCHEMA_STATIC``
should be managed in your makefiles:

* The variable ``PGSCHEMA`` should be set in the ``Makefile``; in this example, it will be set to
  ``main_2019``.
* The ``DOCKER_PGSCHEMA_STATIC`` variable for production should be set in a specific makefile
  for production e.-g. ``production.mk``; it will be set for example to ``integration_static`` in the
  Makefile, and to ``production_static`` in the production makefile.
* The line ``PGSCHEMA=main`` should be removed from your ``env.project`` file.


Start a new version
~~~~~~~~~~~~~~~~~~~

When starting changes such as an application change and/or administration settings,
create a new schema ``main_2020`` and use it on integration. Now, integration uses ``main_2020``,
while production still uses ``main_2019``.

To create the new schema, you should copy the old one, for that `c2cgeoportal` provides a Postgres
function called `clone_schema`.
If you have not yet created this function in your database, use to following command to create it:

.. prompt:: bash

   docker compose exec tools psql --file=/opt/clone_schema.sql

To use the function, connect to your database and perform the following statement:

.. code:: sql

    SELECT clone_schema(
        '<current_schema_name>',
        '<new_schema_name>', TRUE);

In our example, it will be:

.. code:: sql

    SELECT clone_schema('main_2019', 'main_2020', TRUE);

The ``PGSCHEMA`` variable should be set in the ``Makefile`` to ``main_2020``.


Do the changes
~~~~~~~~~~~~~~

Now you can do the changes including upgrades.

If you want to restructure a geodata table, you should create a new table, use the new table name in your
mapfiles and your QGIS projects. The new table will be automatically used when you publish the new version.

To do a test on an editing table during integration, you should copy the table with e.-g.:

.. code:: sql

  CREATE TABLE edit.poi AS TABLE edit.oi_integration;

Use the new table in the 'Geo table' field of your layer in the administration interface.

Do your tests.

Don't forget to put back your old value before publishing the new version.


Publish the new version
~~~~~~~~~~~~~~~~~~~~~~~

Publish the new version on production: now, integration and production both use ``main_2020``.

For OpenShift projects, just push the integration branch into the production branch.

The schema ``main_2019`` still exists, so if needed, the production can be rolled back to this content.


Editing
~~~~~~~

To have a different schema for the geodata used in the editing, we can define the geo_table as follows:
``{GEODATA_SCHEMA}.table`` where ``{GEODATA_SCHEMA}`` will be replaced by the ``GEODATA_SCHEMA``
environment variable.
