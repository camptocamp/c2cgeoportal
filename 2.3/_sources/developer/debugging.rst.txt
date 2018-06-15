.. _developer_debugging:

Debugging
=========

The goal of this document is to give some troubleshooting tips.

Webpack
-------

For debugging purposes, it is better to have all the JavaScript and Style Sheets in separated, non-minified
files. To achieve this, you can simply use the sources maps, function activable in the browsers debugging
tool. And to have faster build you need to use the Webpack dev server; you can achieve this as follows.

Add in your makefile ``<user>.mk`` (Each developer should have a different port, e.g.: 8081):

.. code:: makefile

   DEV_SERVER_PORT = <dev-server-port>

.. prompt:: bash

   make serve

Open in the browser an URL like: ``https://<host><entry-point>/dev/<interface>.html``.

Browser
-------

Using a browser-integrated debugging tool usually available with the ``F12`` key.

Pyramid
-------

If the ``pyramid_debugtoolbar`` is enabled the error is directly shown in the query that fails.

Mapserver
---------

Sometime more information are available by using this command:

.. prompt:: bash

    shp2img -m <mapfile> -o test.png -e <minx> <miny> <maxx> <maxy> -s <sizex> <sizey> -l <layers>

You may also activate MapServer's debug mode and set environment variable of the MapServer container
``MS_DEBUGLEVEL`` to ``5`` (most verbose level, default is 0).

`More information <http://mapserver.org/optimization/debugging.html?highlight=debug#debug-levels>`_

PostgreSQL
----------

In the ``/etc/postgresql/9.*/main/postgresql.conf`` configuration file
you can set ``log_statement`` to ``all`` to see all the called statements.
This file must be edited using the ``postgres`` user.

Reloading PostgreSQL is required so that the new configuration is taken into
account:

.. prompt:: bash

    sudo /etc/init.d/postgres reload

Logs are available in the ``/var/log/postgresql/postgresql-9.*-main.log`` file.

Makefile
--------

To obtain additional debug messages, you can rebuild your project as follows:

.. prompt:: bash

   DEBUG=TRUE make ...

Actually we display the running rule and why she is running (dependence update).

Docker
------

Multiple dev on one server
..........................

When you want to run multiple instances on the same server you should:

- Use the global front
- Use a different docker tag for each instance
- Use a different project name for each instance

Global front
............

The global front will offer a unique entry point on port 80 that provide the 'main' project on `/` and the
others on `/<project_name>/`.

Activate it in the vars:

.. code:: yaml

   vars:
     docker_global_front: true

Build the project:

.. prompt:: bash

   ./docker-run make build

Run the global front:

.. prompt:: bash

   (cd global-front; docker-compose --project-name=global up --build)


And we should defined different instance name for the build:

.. prompt:: bash

   INSTANCE=<name> ./docker-run make build


Use a different docker tag
..........................

Just define an environment variable in the build:

.. prompt:: bash

   DOCKER_TAG=<tag> ./docker-run make build

Use a different project name
............................

Define the project name when you run the Docker composition:

.. prompt:: bash

   docker-compose --project-name=<name> ...

Run gunicorn to reload on modifications of Python files
.......................................................

Add the following environment variable to the geoportal container:

``GUNICORN_PARAMS="-b :80 --worker-class gthread --threads 1 --workers 1 --reload"``

Do a graceful restart of the running geoportal container
........................................................

.. prompt:: bash

   docker-compose exec geoportal bash
   kill -s HUP `ps aux|grep gunicorn|head --lines=1|awk '{print $2}'`  # graceful

Mount c2cgeoportal in the container
...................................

Add in the ``docker-compose.yaml`` file, in the ``geoportal`` service the following lines:

.. code:: yaml

   services:
     geoportal:
       volumes:
         - <c2cgeoportal_git_root>/geoportal/c2cgeoportal_commons:/opt/c2cgeoportal_geoportal/c2cgeoportal_commons
         - <c2cgeoportal_git_root>/geoportal/c2cgeoportal_geoportal:/opt/c2cgeoportal_geoportal/c2cgeoportal_geoportal
         - <c2cgeoportal_git_root>/geoportal/c2cgeoportal_admin:/opt/c2cgeoportal_geoportal/c2cgeoportal_admin

Expose a service
................

To expose a service out of the Docker composition you can add a port for the service in the vars, e.g.:

.. code:: yaml

   vars:
     docker_services:
       <service>:
         port: 8086

Be careful one port can be open only one time on a server.
Within the Docker composition you can access a port of a container, you can achieve this via curl.
This way, you do not need to publish this port on the main host.

.. prompt:: bash

   docker-compose exec geoportal bash
   curl "<url>"

Use Webpack dev server
......................

In the file ``docker-compose-dev.yaml`` set the ``INTERFACE`` to the wanted value.

Run:

.. prompt:: bash

   docker-compose --file=docker-compose.yaml --file=docker-compose-dev.yaml up

Open the application with on the following path: ``https://<host>/<entry_point>/dev/<interface>.html``.

Performance or network error
----------------------------

For performance and proxy issues make sure that all internal URLs in the config file
use localhost (use ``curl "http://localhost/<path>" -H Host:<server_name>``
to test it).

Tilecloud chain
...............

Points to check with TileCloud chain:

* Disabling metatiles should be avoided.
* Make sure that ``empty_metatile_detection`` and ``empty_tile_detection`` are configured correctly.
* Make sure to not generate tiles with a higher resolution than in the raster sources.
