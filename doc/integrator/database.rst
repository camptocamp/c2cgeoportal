.. _integrator_database:

Database
========

Update lifecycle
----------------
The recommended setup is to have integration and production data on the same database, using
separate schemas. This setup allows for simpler switches between integration and production.

The recommended setup for the ``static`` schema is to have exactly one schema for integration
and one for the production, e.-g.:
``integration_static`` for the integration environment,
and ``production_static`` for the production environment.

For the data of the ``main`` schema, we recommend to have one schema for each version of the application.
The following example shows how an update can be performed from a version ``2017`` to a version ``2018``:

* Starting point is that the current version is the same on integration and production => ``main_2017``
* When starting the changes, such as an application change and/or administration settings,
  create a new schema ``main_2018`` and use it on integration. Now, integration uses ``main_2018``,
  while production still uses ``main_2017``.
* Do the changes or the upgrade.
* Publish the new version on production: now, integration and production both use ``main_2018``
* The schema ``main_2017`` still exists, so if needed, the production can be rolled back to this content.

To be able to proceed like this, the variables ``PGSCHEMA`` and the ``DOCKER_PGSCHEMA_STATIC``
should be managed in your makefiles:

* the ``PGSCHEMA`` variable should be set in the ``Makefile``.
* the ``DOCKER_PGSCHEMA_STATIC`` variable for the production should be set in a specific makefile for the production e.-g. ``production.mk``.
* the line ``PGSCHEMA=${docker_schema}`` should be removed from your ``.env.mako`` file.

Copying a schema
----------------
To copy a schema, `c2cgeoportal` provides a Postgres function called `clone_schema`.
If you have not created it in your database, use to following command to create this function:

.. prompt:: bash

   docker-compose exec geoportal psql <database> --file=scripts/CONST_clone_schema.sql

To use the function, connect to your database and perform the following statement:

.. code:: sql

   SELECT clone_schema('<current_schema_name>', '<new_schema_name>', TRUE);
