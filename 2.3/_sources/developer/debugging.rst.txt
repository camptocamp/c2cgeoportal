.. _developer_debugging:

Application debugging
=====================

The goal of this document is to give some troubleshooting tips.

Webpack
-------

For debugging purposes, it is better to have all the JavaScript and Style Sheets in separated, non-minified
files. To achieve this, you can simply use the sources maps, function activable in the browser's debugging
tool. To have faster builds, you need to use the Webpack dev server; you can achieve this as follows.

In the file ``geoportal/demo_geoportal/static-ngeo/js/apps/<interface>.html.ejs``,
remove the ``ng-strict-di`` in the ``html`` tag.

Add in your makefile ``<user>.mk`` (each developer should have a different port, e.g.: 8081):

.. code:: makefile

   DEV_SERVER_PORT = <dev-server-port>

.. prompt:: bash

   FINALISE=TRUE make --makefile=<user>.mk serve-<interface>

Open in the browser an URL like:
``https://<host>/<instanceid>/dev/<interface>.html``.
for non-Docker version: ``https://<host>/<instanceid>/wsgi/dev/<interface>.html``.

Browser
-------

You can use the browser-integrated debugging tool, usually available with the ``F12`` key.

Pyramid
-------

If the ``pyramid_debugtoolbar`` is enabled, the error is directly shown in the query that fails.

Mapserver
---------

Sometimes, more information can be obtained by using this command:

.. prompt:: bash

    shp2img -m <mapfile> -o test.png -e <minx> <miny> <maxx> <maxy> -s <sizex> <sizey> -l <layers>

You may also activate MapServer's debug mode and set the environment variable ``MS_DEBUGLEVEL``
of the MapServer container ``MS_DEBUGLEVEL`` to ``5`` (most verbose level, default is 0).

`More information <http://mapserver.org/optimization/debugging.html?highlight=debug#debug-levels>`_

PostgreSQL
----------

In the configuration file ``/etc/postgresql/9.*/main/postgresql.conf``,
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

With this setting, the rule being executed is displayed and the reason why it is
being executed (for example, a dependency update).

Docker
------

Multiple dev on one server
..........................

When you want to run multiple instances on the same server, you should:

- Use the global front
- Use a different docker tag for each instance
- Use a different project name for each instance

Global front
............

The global front offers a unique entry point on port 80 that provides the 'main' project on `/` and the
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


Define a different instance name for the build:

.. prompt:: bash

   INSTANCE=<name> ./docker-run make build


Use a different docker tag
..........................

Just define an environment variable in the build:

.. prompt:: bash

   DOCKER_TAG=<tag> ./docker-run make build

Run gunicorn to reload on modifications of Python files
.......................................................

Add the following environment variable to the geoportal container:

``GUNICORN_PARAMS="-b :8080 --worker-class gthread --threads 2 --workers 2 --reload"``

Do a graceful restart of the running geoportal container
........................................................

.. prompt:: bash

   docker-compose exec geoportal bash
   kill -s HUP `ps aux|grep gunicorn|head --lines=1|awk '{print $2}'`  # graceful

Mount c2cgeoportal in the container
...................................

Clone and build c2cgeoportal, see :ref:`developer_server_side`.

Add a ``docker-compose.override.yaml`` file with a ``geoportal`` service containing the following lines:

.. code:: yaml

   version: '2'

   services:
     geoportal:
       volumes:
         - <c2cgeoportal_git_root>/commons/c2cgeoportal_commons:/opt/c2cgeoportal_commons/c2cgeoportal_commons
         - <c2cgeoportal_git_root>/geoportal/c2cgeoportal_geoportal:/opt/c2cgeoportal_geoportal/c2cgeoportal_geoportal
         - <c2cgeoportal_git_root>/admin/c2cgeoportal_admin:/opt/c2cgeoportal_admin/c2cgeoportal_admin

Expose a service
................

To expose a service out of the Docker composition, you can add a port for the service in the vars, e.g.:

.. code:: yaml

   vars:
     docker_services:
       <service>:
         port: 8086

Be careful, a port can be open only one time on a server.
Within the Docker composition, you can access a port of a container; you can achieve this via curl.
This way, you do not need to publish this port on the main host.

.. prompt:: bash

   docker-compose exec geoportal bash
   curl "<url>"

Use Webpack dev server
......................

In the file ``docker-compose-dev.yaml``, set the ``INTERFACE`` to the value wanted.

Run:

.. prompt:: bash

   docker-compose --file=docker-compose.yaml --file=docker-compose-dev.yaml up -b

Open the application at the following path: ``https://<host>/<entry_point>/dev/<interface>.html``.

Use a specific version of ngeo
------------------------------

Clone ngeo and build:

.. prompt:: bash

   cd geoportal
   git clone https://github.com/camptocamp/ngeo.git
   cd ngeo
   git check <branch>
   npm install
   npm prepublish
   cd ../..

Add the following alias in your ``webpack.apps.js.mako`` file:

.. code:: js

    resolve: {
      alias: {
        <package>: ...,
   +    ngeo: path.resolve(__dirname, 'ngeo/src'),
   +    gmf: path.resolve(__dirname, 'ngeo/contribs/gmf/src'),
      }
    }

Force rebuild the application:

.. prompt:: bash

   ./docker-run rm /build/apps.<interface>.timestamp
   ./docker-run make build


Performance or network error
----------------------------

For performance and proxy issues, make sure that all internal URLs in the config file
use localhost (use ``curl "http://localhost/<path>" --header Host:<server_name>``
to test it).

TileCloud chain
...............

Points to check with TileCloud chain:

* Disabling metatiles should be avoided.
* Make sure that ``empty_metatile_detection`` and ``empty_tile_detection`` are configured correctly.
* Make sure to not generate tiles with a resolution higher than the one in the raster sources.
