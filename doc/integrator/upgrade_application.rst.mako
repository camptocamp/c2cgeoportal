.. _integrator_upgrade_application:

==================================
Upgrading a GeoMapFish application
==================================


From a version 2.3 and next
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Build the project file:

.. prompt:: bash

   ./docker-run make project.yaml

Change the version in the file ``.config`` to the wanted version.

If you should specify a makefile:

.. prompt:: bash

   ./docker-run --home make --makefile=<user>.mk upgrade

Also:

.. prompt:: bash

   ./docker-run --home make upgrade

Then follow the instructions.


Convert a version 2.3 to Docker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add ``UPGRADE_ARGS += --force-docker --new-makefile=Makefile`` in your ``<user>.mk`` file.

.. prompt:: bash

   git add <user>.mk
   git commit --message="Start upgrade"
   ./docker-run --home make --makefile=temp.mk upgrade

Then follow the instructions.

Remove the ``UPGRADE_ARGS`` in your ``<user>.mk`` file.

.. prompt:: bash

   git add <user>.mk
   git commit --quiet --message="Finish upgrade"

Upgrade the database
~~~~~~~~~~~~~~~~~~~~

The database will be automatically upgraded during the upgrade process.

To upgrade only the database you can use alembic directly.

The help:

.. prompt:: bash

   ./docker-compose-run alembic --help

Upgrade the main schema:

.. prompt:: bash

   ./docker-compose-run alembic --name=main --config=geoportal/alembic.ini upgrade head

Upgrade the static schema:

.. prompt:: bash

   ./docker-compose-run alembic --name=static --config=geoportal/alembic.ini upgrade head
