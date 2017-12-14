.. _integrator_upgrade_application:

==================================
Upgrading a GeoMapFish application
==================================


Then you have 4 different ways...

From a version 2.3 and next
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. prompt:: bash

   ./docker-run make upgrade

Then follow the instruction

Convert a version 2.3 to Docker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add ``UPGRADE_ARGS += --force-docker --new-makefile=Makefile`` in your ``<user>.mk`` file.

.. prompt:: bash

   git add <user>.mk
   git commit --message="Start upgrade"
   ./docker-run make --makefile=temp.mk upgrade

Then follow the instruction

Remove the ``UPGRADE_ARGS`` in your ``<user>.mk`` file.

.. prompt:: bash

   git add <user>.mk
   git commit --quiet --message="Finish upgrade"

Convert a version 2.3 to non-Docker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add the ``vhost`` in the ``template_vars`` of the ``project.yaml.mako`` file.
Add ``UPGRADE_ARGS += --nondocker --new-makefile=<package>.mk`` in the ``Makefile``.

.. prompt:: bash

   git add project.yaml.mako Makefile
   git commit --message="Start upgrade"
   ./docker-run make upgrade

Then follow the instruction

Remove the ``UPGRADE_ARGS`` in your ``Makefile``.

Upgrade a version 2.2
~~~~~~~~~~~~~~~~~~~~~

Add a section ``managed_files: [...]`` in the ``project.yaml.mako`` file.
All the files that's not in this section will be overwritten except::

 - {package}/templates/.*
 - {package}/locale/.*
 - {package}/static/.*
 - {package}/static-ngeo/.*
 - print/print-apps/.*
 - mapserver/.*
 - project.yaml.mako
 - setup.py
 - vars.yaml
 - Makefile

Prepare the upgrade:

.. prompt:: bash

   git submodule deinit <package>/static/lib/cgxp/
   git rm .gitmodules
   curl https://raw.githubusercontent.com/camptocamp/c2cgeoportal/master/docker-run > docker-run
   chmod +x docker-run
   git add docker-run project.yaml.mako
   git commit --quiet --message="Start upgrade"
   make --makefile=<package>.mk project.yaml

Pull the latest version of the Docker image:

.. prompt:: bash

    docker pull camptocamp/geomapfish-build:<version>

Where ``<version>`` is ``2.3.0`` for the first stable release of the version ``2.3``.

For Docker:

.. prompt:: bash

   ./docker-run --image=camptocamp/geomapfish-build --version=<version> \
       c2cupgrade --force-docker --new-makefile=Makefile --makefile=<package>.mk

And for non-Docker

.. prompt:: bash

   ./docker-run --image=camptocamp/geomapfish-build \
       c2cupgrade --nondocker --makefile=testgeomapfish.mk

Then follow the instruction

.. note:: Know issue

   if you have the following message:

   .. code::

      Host key verification failed.
      fatal: Could not read from remote repository.

      Please make sure you have the correct access rights
      and the repository exists.

   you can do the following command to fix it:

   .. prompt:: bash

      ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts

Upgrade the database
--------------------

The database will be automatically upgraded during the upgrade process.

To upgrade only the database you can use alembic directly.

The help:

.. prompt:: bash

   ./docker-run alembic --help

Upgrade the main schema:

.. prompt:: bash

   ./docker-run alembic --name=main upgrade head

Upgrade the static schema:

.. prompt:: bash

   ./docker-run alembic --name=static upgrade head
