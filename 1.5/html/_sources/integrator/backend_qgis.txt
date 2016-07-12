.. _integrator_backend_qgis:

Specific configuration for QGIS mapserver
=========================================

WFS namespace
-------------

In the ``<package>/templates/viewer.js`` file, define the url of the WFS service
which will be used to get the namespace required to parse the WFS response,
and indicate that we don't want duplicate layer name above the legend::

    cgxp.WMS_FEATURE_NS = "http://www.qgis.org/gml";
    cgxp.LEGEND_INCLUDE_LAYER_NAME = false;

Change the DPI value to use the same as in the server::

    - OpenLayers.DOTS_PER_INCH = 92;
    + OpenLayers.DOTS_PER_INCH = 2.54 / 100 / 0.00028;

Apache configuration
--------------------

In the ``apache/mapserv.conf.in`` do the following changes:

.. code::

   - ScriptAlias /${vars:instanceid}/mapserv /usr/lib/cgi-bin/mapserv
   + ScriptAlias /${vars:instanceid}/mapserv /usr/lib/cgi-bin/qgis_mapserv.fcgi

   - SetEnv MS_MAPFILE ${buildout:directory}/mapserver/c2cgeoportal.map
   + SetEnv QGIS_PROJECT_FILE ${buildout:directory}/qgisserver.qgs

Application configuration
-------------------------

In the ``config.yaml.in`` file, define:

.. code:: yaml

    mapserv_url: http://your.arcgis.server/arcgis/services/SOME/FOLDER/MapServer/WMSServer

Cleanup
-------

Remove the mapserver folder:

.. prompt:: bash

   git rm mapserver

Connect to Postgres from QGIS desktop
-------------------------------------

This chapter is subject to change when the QGIS plugin is available.

Throw a tunnel
~~~~~~~~~~~~~~

The first solution is to create a tunnel with ssh:

.. prompt:: bash

   ssh -L 5432:localhost:54532 <server>

And use the following connection attributes::

   Name: <aname>
   Host: localhost
   Port: 5432
   Database: <database>
   SSL mode: Disable
   Username: www-data
   Password: www-data

Directly on the server
~~~~~~~~~~~~~~~~~~~~~~

For that you should ask the sysadmins to be able to access to the
postgres port on the server from your infra.

Then use the following connection attributes::

   Name: <aname>
   Host: <server>
   Port: 5432
   Database: <database>
   SSL mode: require
   Username: www-data
   Password: www-data

Deploy notes
~~~~~~~~~~~~

TODO
