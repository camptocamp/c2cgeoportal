.. _integrator_backend_qgis:

=========================================
Specific configuration for QGIS mapserver
=========================================

Viewer configuration
====================

In the ``<package>/templates/viewer.js`` file, define the url of the WFS service
which will be used to get the namespace required to parse the WFS response,
and indicate that we do not want duplicate layer name above the legend::

    cgxp.WMS_FEATURE_NS = "http://www.qgis.org/gml";
    cgxp.LEGEND_INCLUDE_LAYER_NAME = false;

Change the DPI value to use the same as in the server::

    - OpenLayers.DOTS_PER_INCH = 92;
    + OpenLayers.DOTS_PER_INCH = 2.54 / 100 / 0.00028;

In the ``cgxp_print`` plugin add the following configuration:

.. code:: javascript

   encodeLayer: { useNativeAngle: true, serverType: 'qgisserver' }
   encodeExternalLayer: { useNativeAngle: true, serverType: 'qgisserver' }


Apache configuration
====================

In the ``apache/mapserv.conf.mako`` do the following changes:

.. code::

   - ScriptAlias /${instanceid}/mapserv /usr/lib/cgi-bin/mapserv
   + ScriptAlias /${instanceid}/mapserv /usr/lib/cgi-bin/qgis_mapserv.fcgi

   - SetEnv MS_MAPFILE ${directory}/mapserver/c2cgeoportal.map
   + SetEnv QGIS_PROJECT_FILE ${directory}/qgisserver.qgs

Application configuration
=========================

Add an OGC server in the admin interface for QGIS server (type: qgisserver, auth: Standard auth).

In the ``vars_<project>.yaml`` file, define:

.. code:: yaml

    vars:
        ...
        mapserverproxy:
            default_ogc_server: <ogc server name>
    update_paths:
    ...
    - mapserverproxy

Cleanup
=======

Remove the mapserver folder:

.. prompt:: bash

   git rm mapserver

QGIS Desktop configuration
==========================

OWS configuration
*****************

You should setup your OWS service in the QGIS project properties in the OWS
tab.

You should take care to **uncheck** the checkbox *User Layer ids as names*. If
this checkbox is enabled you will have unreliabel layers name.

You should **check** the checkbox *Add geometry to feature response* in order
to make the WMS GetFeatureInfo working correctly.

In the *WFS capabilities* section, you should check the layers that need to be
available in the WFS service.

Finally, your QGIS project layers CRS should all be in the same CSR. This is subject to
change.

Connect to Postgres database
*****************************

This section is subject to change when the QGIS plugin is available.

The way you should connect QGIS to the database is based on an external file
called. pg_service.conf located in the home directory. The content of this file
is as follow::

    [geomapfish]
    host=localhost
    dbname=geomapfish
    user=www-data
    password=www-data
    port=5433

You probably need to create a tunnel with ssh:

.. prompt:: bash

   ssh -L 5432:localhost:54532 <server>

Note that if you can connect directly to the database, you don't need this tunnel.
Ask to your database administrator the correct parameters. You probably just need
to change the host parameter.

You can have several sections. A section start with a name with [] and
finish with a blanck line. This file should be a unix file.

On QGIS deskop, when creating a new PostGIS connection, give it a name and use
the service name (`geomapfish` in our example) in the connection parameters
form.

Copy past this file in the server, change the parameters to fit with the server
settings and add the variable environment setting in the Apache config::

    [..]
    SetEnv QGIS_PROJECT_FILE ${directory}/qgisserver.qgs
    + SetEnv PGSERVICEFILE path/to/pg_service.conf

Don't forget to restart Apache.

Deploy notes
************

TODO
