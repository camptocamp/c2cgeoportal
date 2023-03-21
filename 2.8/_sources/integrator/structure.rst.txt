.. _integrator_structure:

Project structure
=================

We can split the project in 3 parts.

Configuration
-------------

These files are use to build the config image.

``mapserver``: all the files needed by Mapserver will be in the folder ``/etc/mapserver`` in the config
image.

``qgisserver``: all the files needed by QGIS server will be in the folder ``/etc/qgisserver`` in the config
image.

``tilegeneration``: all the files needed by TileCloud-chain will be in the folder ``/etc/tilegeneration``
in the config image.

``print/print-apps``: all the files needed my Mapfish print will be in the folder
``/usr/local/tomcat/webapps/ROOT/print-apps`` in the config image.

``geoportal/vars*.yaml``, ``geoportal/CONST_vars.yaml``, ``geoportal/CONST_config-schema.yaml``: All the
files needed to build the config will be in the file ``/etc/geomapfish/config.yaml`` in the config image.

``geoportal/geomapfish_geoportal/static``: All the static files needed for your application that are
available in the static view with cache buster will be in the folder ``/etc/geomapfish/static`` in the
config image.

``geoportal/geomapfish_geoportal/locale``: Contains the files needed to localise your application will be in
the folder ``/etc/geomapfish/locale`` in the config image.

Custom application
------------------

.. note::

    This section is not relevant in the simple application mode.

``geoportal/geomapfish_geoportal`` the pyramid application.

``geoportal/webpack.*`` the webpack build configuration.

other files in ``geoportal`` essentially files related to the build.

In the image everything will be in the ``/app`` folder except the result of the webpack build which will be
in the directory ``/etc/static-ngeo/``.

Other files
-----------

The files in ``CONST_create_template`` is the clean instantiation or the create scaffold during the last
upgrade. It is used the create the diff during the migration.

The files in ``.github``, ``ci``, or directly in the project base are used by the CI, by the IDE, or by
the build part out of Docker.
