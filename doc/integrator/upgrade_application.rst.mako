.. _integrator_upgrade_application:

Upgrading a GeoMapFish application
==================================


Updating the application code
-----------------------------

Verify that you have in your ``project.yaml.mako`` file the following ``template_vars``: ``package``, ``srid``, ``extent``, for example:

.. code:: yaml

   ...
   template_vars:
       package: ${'$'}{package}
       srid: ${'$'}{srid}
       extent: 489246, 78873, 837119, 296543

Then run:

.. prompt:: bash

   make update
   make build


Upgrading an application
------------------------

In the ``setup.py`` be sure not to specify a ``c2cgeoportal`` version,
because it will prevent the installation of the new ``c2cgeoportal`` egg.

.. note:: For Windows:

   You should add ``UPGRADE_ARGS += --windows`` in your ``<package>.mk`` file.

To upgrade run:

.. prompt:: bash

    wget https://raw.githubusercontent.com/camptocamp/c2cgeoportal/${main_version}/c2cgeoportal/scaffolds/create/docker-run_tmpl
    mv docker-run_tmpl docker-run
    sed -i 's/{{geomapfish_version}}/<target_version>/g'
    chmod +x docker-run
    ./docker-run make upgrade

Where ``<target_version>`` is the version that you wish to upgrade to.

And follow the instructions.

.. note:: For Windows:

    If you are using Windows, you will have to execute some steps prior
    to the instructions hereunder:

    * Uninstall manually the old c2cgeoportal egg:

        ``.build/venv/Scripts/pip uninstall c2cgeoportal``

    * Clean / remove the generated files:

        ``make -f <makefile> clean``

    * Change the version in ``setup.py``
      to the version you wish to install.
    * Build your application:

        ``make -f <makefile> build``

    *  Put your modifications under git revision:

        ``git add setup.py``

        ``git commit -m "Upgrade c2cgeoportal version"``

        ``git push <remote> <branch>``

    * Follow the Windows instructions hereunder, note that you will have to use
      ``.build\venv\Scripts\...`` instead of ``.build\venv\bin\...`` in all given
      commands

Upgrade the database
--------------------

The database will be automatically upgraded during the upgrade process.

To upgrade only the database you can use alembic directly.

The help:

.. code:: bash

   ./docker-run alembic --help

Upgrade the main schema:

.. code:: bash

   ./docker-run alembic --config alembic.ini upgrade head

Upgrade the static schema:

.. code:: bash

   ./docker-run alembic --config alembic_static.ini upgrade head
