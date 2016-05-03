.. _integrator_upgrade_application:

Upgrading a GeoMapFish application
==================================

Using the c2ctool command
-------------------------

The ``c2ctool`` is a tool to facilitate the common operations around GeoMapFish.


Easy updating an application code
---------------------------------

Verify that you have in your ``project.yaml.mako`` file the following ``template_vars``: ``package``, ``srid``, ``extent``, ``apache_vhost``, for example:

.. code:: yaml

   ...
   template_vars:
       package: ${'$'}{package}
       srid: ${'$'}{srid}
       extent: 489246, 78873, 837119, 296543
       apache_vhost: <apache_vhost>

Then run:

.. prompt:: bash

   make -f <makefile> update
   make -f <makefile> build

Where ``<makefile>`` is your user make file (``<user>.mk``).


Easy upgrading an application
-----------------------------

In the ``setup.py`` be sure not to specify a ``c2cgeoportal`` version,
because it will prevent the installation of the new ``c2cgeoportal`` egg.

We considers that your makefile is named ``<instanceid>.mk``, if it's not the case
add in your Makefile ``UPGRADE_MAKE_FILE = <user.mk>``

.. note:: For Windows:

   You should add ``UPGRADE_ARGS += --windows`` in your ``<package>.mk`` file.

Than just run:

.. prompt:: bash

   export VERSION=<target_version>
   make -f <makefile> upgrade_v2

.. note:: For Windows:

   You should add replace ``export VERSION=<target_version>`` with
   ``SET VERSION=<target_version>``.

Where ``<makefile>`` is your user Makefile (``<user>.mk``),
``<target_version>`` is the version that you wish to upgrade to
(for the development version it should be 'master').

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
