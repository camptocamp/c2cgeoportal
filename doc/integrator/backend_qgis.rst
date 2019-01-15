.. _integrator_backend_qgis:

=========================================
Specific configuration for QGIS mapserver
=========================================

QGIS Desktop configuration
==========================


Create a tunnel on the database server
**************************************

If you cannot connect directly to the database you can create a tunnel to be able to connect to them:

.. prompt:: bash

   ssh -L 5432:localhost:5432 <server>

If you run QGIS in Docker you should bind to a specific IP:

.. prompt:: bash

   IP=$(ip addr show dev $(route | grep default | awk '{print $(NF)}' | head -1) | awk '$1 ~ /^inet/ { sub("/.*", "", $2); print $2 }' | head -1)
   ssh -L ${IP}:5432:localhost:5432 <remote server>

Run the client with Docker
**************************

In a Docker mode, QGIS is configured in the ``qgisserver/`` directory. To edit the configuration,
run this target and open the ``/etc/project/project.qgs`` file:

.. prompt:: bash

   make edit-qgis-project

OWS configuration
*****************

You should setup your OWS service in the QGIS project properties in the OWS tab.

You should **check** *Service Capabilities* and **fill** *Online resource* to correctly generate
the URL's in the capabilities.

In the *WMS capabilities* section, you should take care to **uncheck** the checkbox *User layer ids as
names*. If this checkbox is enabled you will have unreliable layers name.

In the *WMS capabilities* section, you should **check** the checkbox *Add geometry to feature response* in
order to make the WMS GetFeatureInfo working correctly.

In the *WFS capabilities* section, you should check the layers that need to be available in the WFS service.
Also take care on the Update Insert delete column to make the layer available throw the WFS transactional
API.

Finally, your QGIS project layers CRS should all be in the same CSR. This is subject to change.

Connect to Postgres database
****************************

If you want to add PostGIS layers on the main DB, create/edit your ``$HOME/.pg_service.conf`` file
and add a section for the DB you want to access:

.. code::

   [<package>]
   host=<host>  # Localhost address of the Docker network interface (=> ${IP})
   dbname=<database name>
   user=<database user>
   password=<database password>
   port=5432

`<host>` can be:

* If you use the tunnel with QGIS on your host: ``localhost``.
* If you use the tunnel with QGIS on Docker: localhost address of the Docker network interface
  (=> `${IP}`, e.-g.: `172.17.0.1`).
* If you know the host you should use, use it.

Note that if you can connect directly to the database, you don't need this tunnel.
Ask to your database administrator the correct parameters. You probably just need
to change the host parameter.


Then, in QGIS, fill only the ``name`` and ``service`` fields when you create the DB connection.

In the project repository you should have a ``qgisserver/pg_service.conf.tmpl`` file
with a section looking like that:

.. code::

   [<package>]
   host=${PGHOST}
   dbname=${PGDATABASE}
   user=${PGUSER}
   password=${PGPASSWORD}
   port=${PGPORT}

If you don't use Docker you also should add this int the Apache QGIS configuration:

.. code::

    SetEnv QGIS_PROJECT_FILE ${directory}/qgisserver.qgs
    + SetEnv PGSERVICEFILE ${directory}/pg_service.conf

Don't forget to graceful Apache.

Extra PostGIS connexion
***********************

If you need to add other database connection just add a new section in the
``$HOME/.pg_service.conf``.

In the and ``qgisserver/pg_service.conf.tmpl`` files add a new section like that:

.. code::

   [<package>]
   host=${EXTRA_PGHOST}
   dbname=${EXTRA_PGDATABASE}
   user=${EXTRA_PGUSER}
   password=${EXTRA_PGPASSWORD}
   port=${EXTRA_PGPORT}

And in your ``docker-compose.yaml`` file:

.. code:: yaml

   services:
     qgisserver:
       environment:
         EXTRA_PGHOST=<host>
         EXTRA_PGDATABASE=<database>
         EXTRA_PGUSER=<user>
         EXTRA_PGPASSWORD=<pass>
         EXTRA_PGPORT=<port>

With that you can respect that the connection should be passed throw the environments variables
to be able change the database connexion without rebuilding your application.


OGC server
==========

In the project file you should set the online resource URL
(Project/Properties.../QGIS Server/General information/Online resource) to
``https://<host>/<entrypoint>/mapservproxy?ogcserver=<name>``, e.-g.
``https://geomapfish-demo-ci.camptocamp.com/mapservproxy?ogcserver=QGIS%20server``.

To use the QGIS server in authenticated mode through the mapserv proxy, it's required to be in docker mode,
and he should be configured as follow:

* Name: ``<name>``, e.-g. ``QGIS server``
* Base URL: ``http://qgisserver:8080/``
* WFS URL: empty
* Server type: ``qgisserver``
* Image type: recommended to be ``image/png``
* Authentication type: ``Standard auth``
* WFS support: recommended to be ``[X]``
* Is single tile:  recommended to be ``[ ]``

Access Restriction
******************

The access restriction is available only for Docker projects

We provide an Docker image named ``camptocamp/geomapfish-qgisserver`` with tag pattern:
``gmf<Major GeoMapFish version}-qgis${Major QGIS}``.

Configuration for a single project, just provide the OGC server name in the environment variable named:
``GEOMAPFISH_OGCSERVER``.

If you need to provide more than one QGIS projects you should write a config file named, e.g.
``qgisserver/accesscontrol_config.yaml``, with the content:

.. code:: yaml

   map_config:
     <project file path>:
       ogc_server: <OGC server name>

``<project file path>`` should have exactly the same value a the ``MAP`` parameter in the ``Base URL``
vavalue of the OGC sever.

And finally you should provide the ``GEOMAPFISH_ACCESSCONTROL_CONFIG`` to point to config file e.-g.
``/etc/qgisserver/accesscontrol_config.yaml``, and ``QGIS_PROJECT_FILE`` to be empty.

Project in Database
*******************

If you store the project in the database you should set the ``QGIS_PROJECT_FILE`` environment variable
to something like that:
``postgresql://<dbuser>:<dbpass>@<dbhost>:<dbport>?sslmode=disable&dbname=<dbname>&schema=<dbschema>&project=<projectname>``.

If you specify it in the `MAP` parameter for the  OGC proxy, don't forget to correctly encode it, you can use this
`service <https://www.url-encode-decode.com/>`__ to encode it.
