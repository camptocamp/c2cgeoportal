.. _integrator_database:

========
Database
========

To be able to do a rollback the integration and the production data should be in the same database,
but the schema will be different.

For the static schema will have one for the integration and one for the production environments, e.-g.:
``integration_static`` for the integration environment,
and ``production_static`` for the production environment.

For the main schema will have one for each version of the application. We will have the following livecycle:

Current version:
integration and production => ``main_2017``

Start an upgrade (application or admin (layertree)), create an new schema and use it on integration:
integration = ``main_2018``, and production => ``main_2017``

Do the changes or the upgrade.

Publish the new version:
integration and production => ``main_2018``

The schema ``main_2017`` still exists to be able to rollback the production.

To do that we should manage the ``PGSCHEMA`` and the ``PGSCHEMA_STATIC`` variable in your makefiles.

The ``PGSCHEMA`` should be set in the ``Makefile`` and the ``PGSCHEMA_STATIC`` for the production should be
set in a specific makefile for the production e.-g. ``production.mk``.

To to the schema we provide a Postgres function, to create it:

.. prompt:: bash

   sudo -u postgres psql <database> --file=scripts/CONST_clone_schema.sql

To use it:

.. code:: sql

   SELECT clone_schema('<current_schema_name>', '<new_schema_name>', TRUE);
