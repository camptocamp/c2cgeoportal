.. _integrator_upgrade_application:

==================================
Upgrading a GeoMapFish application
==================================

----------------
Preliminary work
----------------

Depending on your current installation, some preliminary work is necessary before applying the
update steps via scripts.

GMF 1.X to GMF 2.2
------------------
If you are updating directly from a GeoMapFish 1.X version to GeoMapFish 2.2,
you need to follow the update instructions for GeoMapFish 2.1 first before
proceeding with the update to GeoMapFish 2.2.
See
`2.1 upgrade instructions <https://camptocamp.github.io/c2cgeoportal/2.1/integrator/upgrade_application.html>`_.

updating your project environment
---------------------------------
Before upgrading your application to a newer version of c2cgeoportal, you should make sure that
your project environment is up-to-date with regard to your project repository and with regard to the
required dependencies.
For this, execute the following commands:

.. prompt:: bash

   make -f <makefile> update
   make -f <makefile> build

Where ``<makefile>`` is your user make file (``<user>.mk``).

-------------------------
Upgrading the application
-------------------------

In the ``setup.py`` be sure not to specify a ``c2cgeoportal`` version,
because it will prevent the installation of the new ``c2cgeoportal`` egg.

Verify that you have in your ``project.yaml.mako`` file the following ``template_vars``:
``package``, ``srid``, ``extent``, ``apache_vhost``, for example:

.. code:: yaml

    ...
    template_vars:
        package: ${'$'}{package}
        srid: ${'$'}{srid}
        extent: 489246, 78873, 837119, 296543
        apache_vhost: <apache_vhost>


We consider that your makefile is named ``<instanceid>.mk``, if it is not the case
add in your Makefile ``UPGRADE_MAKE_FILE = <user.mk>``

.. note:: For Windows:

   You should add ``UPGRADE_ARGS += --windows`` in your ``<package>.mk`` file.

To upgrade, run:

.. prompt:: bash

   export VERSION=<target_version>
   make -f <makefile> upgrade

.. note:: For Windows:

   You should replace ``export VERSION=<target_version>`` with
   ``SET VERSION=<target_version>``.

Where ``<makefile>`` is your user Makefile (``<user>.mk``),
``<target_version>`` is the version that you wish to upgrade to.

And follow the instructions.

.. note:: For Windows:

    If you are using Windows, you will have to execute some steps prior
    to the instructions hereunder:

    * Uninstall manually the old c2cgeoportal egg:

        ``.build/venv/Scripts/pip uninstall c2cgeoportal``

    * Clean / remove the generated files:

        ``make -f <makefile> clean``

    * Change the version in ``setup.py`` and ``CONST_requirements.txt``
      to the version you wish to install.
    * Build your application:

        ``make -f <makefile> build``

    *  Put your modifications under git revision:

        ``git add setup.py``

        ``git add CONST_requirements.txt``

        ``git commit -m "Upgrade c2cgeoportal version"``

        ``git push <remote> <branch>``

    * Follow the Windows instructions hereunder, note that you will have to use
      ``.build\venv\Scripts\...`` instead of ``.build\venv\bin\...`` in all given
      commands

--------------------
Upgrade the database
--------------------

The database will be automatically upgraded during the upgrade process.

To upgrade only the database you can use alembic directly.

The help:

.. code:: bash

   .build/venv/bin/alembic --help

Upgrade the main schema:

.. code:: bash

   .build/venv/bin/alembic --config alembic.ini upgrade head

Upgrade the static schema:

.. code:: bash

   .build/venv/bin/alembic --config alembic_static.ini upgrade head

.. _integrator_upgrade_application_cgxp_to_ngeo:

-----------------
From CGXP to ngeo
-----------------

Layer definition for ngeo clients is separate and different from layer
definition for CGXP clients, see :ref:`administrator_administrate_layers`
for details.
To migrate the layer definitions from the CGXP structure to the ngeo
structure, you can use the script ``.build/venv/bin/themev1tov2``.

Text translations for ngeo clients are separate and different from text
translations for CGXP clients.
To migrate the text translations from CGXP to ngeo, you can use the script
``.build/venv/bin/l10nv1tov2``.
For example, for converting french texts the script can be used as follows:

.. code:: bash

   .build/venv/bin/l10nv1tov2 fr geoportal/static/js/Proj/Lang/fr.js \
   geoportal/locale/fr/LC_MESSAGES/geoportal-client.po
