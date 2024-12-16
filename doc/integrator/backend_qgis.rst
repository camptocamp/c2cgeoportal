.. _integrator_backend_qgis:

======================================
Specific configuration for QGIS server
======================================

QGIS Desktop configuration
==========================


Create a tunnel on the database server
**************************************

If you cannot connect directly to the database, you can create a tunnel to be able to connect:

.. prompt:: bash

   ssh -L 5432:localhost:5432 <server>

If you run QGIS in Docker, you should bind to a specific IP:

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
the URLs in the capabilities.

In the *WMS capabilities* section, you should take care to **uncheck** the checkbox *User layer ids as
names*. If this checkbox is enabled, you will have unreliable layer names.

In the *WMS capabilities* section, you should **check** the checkbox *Add geometry to feature response* in
order to make the WMS GetFeatureInfo work correctly.

In the *WFS capabilities* section, you should check the layers that need to be available in the WFS service.
Also take care on the Update Insert Delete column to make the layer available through the WFS transactional
API.

Your QGIS project layers' CRS should all be in the same CRS. This is subject to change.

Finally, in the project settings, in the QGIS server section, set all the published URL to:
``https://<application_base_url>/mapserv_proxy?ogcserver=<name>``.


Connect to Postgres database
****************************

If you want to add PostGIS layers on the main DB, create/edit your ``$HOME/.pg_service.conf`` file
and add a section for the DB you want to access:

.. code::

   [<package>]
   host=<host>  # Localhost address of the Docker network interface (=> ${IP})
   port=<database port>
   user=<database user>
   password=<database password>
   dbname=<database name>

   [<package>_master]
   host=<host>  # Localhost address of the Docker network interface (=> ${IP})
   port=<database port>
   user=<database user>
   password=<database password>
   dbname=<database name>

`<host>` can be:

* If you use the tunnel with QGIS on your host: ``localhost``.
* If you use the tunnel with QGIS on Docker: localhost address of the Docker network interface
  (=> `${IP}`, e.-g.: `172.17.0.1`).
* If you know the host you should use, use it.

Note that if you can connect directly to the database, you don't need this tunnel.
Ask your database administrator for the correct parameters. You probably just need
to change the host parameter.


Then, in QGIS, fill only the ``name`` and ``service`` fields when you create the DB connection.

Use ``<package>`` for read only layers, and ``<package>_master`` if the layer should be writable.

In the project repository, you should have a ``qgisserver/pg_service.conf.tmpl`` file
with a section looking like that:

.. code::

   [<package>]
   host=${PGHOST_SLAVE}
   port=${PGPORT_SLAVE}
   user=${PGUSER}
   password=${PGPASSWORD}
   dbname=${PGDATABASE}

   [<package>_master]
   host=${PGHOST}
   port=${PGPORT}
   user=${PGUSER}
   password=${PGPASSWORD}
   dbname=${PGDATABASE}

Do not forget to gracefully restart Apache.

Extra PostGIS connection
************************

If you need to add another database connection, add a new section in the ``$HOME/.pg_service.conf``.
In the ``qgisserver/pg_service.conf.tmpl`` files, add a new section:

.. code::

   [<extra_service>]
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

With this configuration, the connection will be passed through the environment variables,
so that you can change the database connection without rebuilding your application.


OGC server
==========

For QGIS version < 3.20, in the project file, you should set the online resource URL
(Project/Properties.../QGIS Server/General information/Online resource) to
``https://<host>/<entrypoint>/mapservproxy?ogcserver=<name>``, e.-g.
``https://geomapfish-demo-ci.camptocamp.com/mapservproxy?ogcserver=QGIS%20server``.

To use the QGIS server in authenticated mode through the mapserv proxy, it is required to be in docker mode,
and the configuration should be as follows:

* Name: ``<name>``, e.-g. ``QGIS server``
* Base URL: ``http://qgisserver:8080/``
* WFS URL: empty
* Server type: ``qgisserver``
* Image type: recommended to be ``image/png``
* Authentication type: ``Standard auth``
* WFS support: recommended to be ``[X]``
* Is single tile:  recommended to be ``[ ]``


Project in Database
*******************

If you store the project in the database, you should set the ``QGIS_PROJECT_FILE`` environment variable
to something like that:
``postgresql://<dbuser>:<dbpass>@<dbhost>:<dbport>?sslmode=require&dbname=<dbname>&schema=<dbschema>&project=<projectname>``.

If you specify it in the `MAP` parameter for the  OGC proxy, don't forget to correctly encode it, you can use this
`service <https://www.url-encode-decode.com/>`__ to encode it.

In multi project mode the best is to use in the OGC server URL like this `config://qgis1`, `config://qgis2`,
in the vars file add:

.. code:: yaml

   vars:
     servers:
       qgis1:
         url: '{QGISSERVER_URL}'
         params:
           MAP: postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}?sslmode={PGSSLMODE}&dbname={PGDATABASE}&schema=qgis&project=qgis1
       qgis2:
         url: '{QGISSERVER_URL}'
         params:
           MAP: postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}?sslmode={PGSSLMODE}&dbname={PGDATABASE}&schema=qgis&project=qgis2

With that you will not have URL encoding issues.


Access Restrictions
===================

The access restriction functionality described here is available only for Docker projects.

We provide a Docker image named ``camptocamp/geomapfish-qgisserver`` with tag pattern:
``gmf<Major GeoMapFish version}-qgis${Major QGIS}``.


Access Restriction on QGIS OGC server
*************************************

From version 2.7 the config is just made with the ``GEOMAPFISH_ACCESSCONTROL_BASE_URL`` environment
variable which contains the base URL of the OGC servers, by default it's set to
``QGISSERVER_URL``. And the plugin will search for the OGC servers that match with this base URL.
It also requires that the OGC servers are configured with an URL like that
``config://qgisserver?map=<project_file>``.

The configuration that use the ``QGIS_PROJECT_FILE`` or ``GEOMAPFISH_ACCESSCONTROL_CONFIG`` are still
working but are deprecated.


Protecting Attributes
*********************

Individual attributes can be protected via the layer metadata setting ``protectedAttributes``. To define which roles shall
have access, the functionality ``allowed_attributes`` must be used in combination with this setting. As WMS layer name,
the actual (exposed) WMS layer name must be used in this configuration.


Landing page
============

`The QGIS documentation <https://docs.qgis.org/latest/en/docs/server_manual/services.html#qgis-server-catalog>`_.

To have the landing page you should:

- Don't define the ``QGIS_PROJECT_FILE`` environment variable (the map should be defined in the OGC server,
  in the ``MAP`` attribute of the query string).
- Define the ``QGIS_SERVER_LANDING_PAGE_PROJECTS_DIRECTORIES`` or the
  ``QGIS_SERVER_LANDING_PAGE_PROJECTS_PG_CONNECTIONS`` environment variable.
- Create a new OGC server with a name e.g. ``qgis`` and no ``MAP`` in the query string.
- Define the ``QGIS_SERVER_LANDING_PAGE_PREFIX`` to, in our example, ``/mapserv_proxy/qgis``.

Then open the landing page in your browser with ``https://<host>/mapserv_proxy/qgis/``.
