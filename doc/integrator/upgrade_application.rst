.. _integrator_upgrade_application:

==================================
Upgrading a GeoMapFish application
==================================

The upgrade can be done from the previous version or the previous LTS version.

Prepare upgrade
~~~~~~~~~~~~~~~

:git:`Read the 'Information to know before starting the upgrade' chapters in the changelog
</geoportal/c2cgeoportal_geoportal/scaffolds/update/{{cookiecutter.project}}/CONST_CHANGELOG.txt>`.
If you are currently using an LTS (Long-term support) release, you should read all the chapters,
if you are using the previous version, only the first chapter is relevant.

Be sure that your ``managed_files`` list is up-to-date in your ``project.yaml`` file.

If you are not sure whether this list is up-to-date, you can perform an update up to step 7 on your
current version and see if some files get modified by the update process.
If the update process modified files which you do not want modified, then add these files to the
``managed_files`` list.

Prepare the database
~~~~~~~~~~~~~~~~~~~~

Clone the schema with e.g.:

.. code:: sql

    SET statement_timeout TO '600s';
    SELECT clone_schema('main_<old_version>', 'main_<new_version>', TRUE);
    SELECT clone_schema('static_<old_version>', 'static_<new_version>', TRUE);

Update the ``PGSCHEMA`` and the ``PGSCHEMA_STATIC`` in your ``env.project`` file.

From a version prior to 2.4.x
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Upgrade your project first to 2.4, as this is the current long-term release. Migration scripts and
instructions assume that your minimal version is the current long-term release.

From a version 2.4.x
~~~~~~~~~~~~~~~~~~~~

Clean your project (include ignored files):

.. prompt:: bash

   git clean -dx --force

Build the project file if needed:

.. prompt:: bash

   ./docker-run make project.yaml

Get the upgrade script:

.. prompt::
    :language: bash
    :substitutions:

    curl https://raw.githubusercontent.com/camptocamp/c2cgeoportal/|main_branch|/scripts/upgrade > upgrade
    chmod +x upgrade

Upgrade in Git ignore:

.. prompt:: bash

    echo /upgrade >> .gitignore
    git add .gitignore
    git commit -m "Add /upgrade in .gitignore"

Run the upgrade:

.. prompt:: bash

   ./upgrade <version>

Then follow the instructions.


From a version 2.5 and next
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Start the upgrade:

.. prompt:: bash

    ./build --upgrade <version>

Then follow the instructions.

The ``<version>`` can be ``x.y.z.p`` to target a stable version, or ``master`` to target the master branch.

If for some reason you need to debug what happens during the upgrade see: :ref:`here <upgrade_debugging>`.

Upgrade the database
~~~~~~~~~~~~~~~~~~~~

The database will be automatically upgraded during the upgrade process.

To upgrade only the database you can use alembic directly.

The help:

.. prompt:: bash

   docker-compose exec geoportal alembic --help

Upgrade the main schema:

.. prompt:: bash

   docker-compose exec geoportal alembic --name=main upgrade head

Upgrade the static schema:

.. prompt:: bash

   docker-compose exec geoportal alembic --name=static upgrade head
