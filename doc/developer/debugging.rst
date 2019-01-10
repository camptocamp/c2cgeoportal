.. _developer_debugging:

Application debugging
=====================

The goal of this document is to give some troubleshooting tips.

Browser
-------

Using a browser-integrated debugging tool usually available with the ``F12`` key.

Sources map
-----------

For debugging purposes, it is better to have all the JavaScript and Style Sheets in separated, non-minified
files. To achieve this, you can simply use the sources maps, function activable in the browsers debugging
tool.

Webpack
-------

To have faster builds you need to use the Webpack dev server; you can achieve this as follows.

In the ``geoportal/demo_geoportal/static-ngeo/js/apps/<interface>.html.ejs`` file
remove the ``ng-strict-di`` in the ``html`` tag.

In the file ``docker-compose-dev.yaml`` set the ``INTERFACE`` to the wanted value.

Run:

.. prompt:: bash

   docker-compose --file=docker-compose.yaml --file=docker-compose-dev.yaml up

Open the application at the following URL: ``https://<host>/<entry_point>/dev/<interface>.html``.

Pyramid
-------

If the ``pyramid_debugtoolbar`` is enabled the error is directly shown in the query that fails.

Mapserver
---------

Sometime more information are available by using this command:

.. prompt:: bash

    docker-compose exec mapserver shp2img -m <mapfile> -o test.png -e <minx> <miny> <maxx> <maxy> \
        -s <sizex> <sizey> -l <layers>

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

   ./docker-run --env=DEBUG=TRUE make ...

It will add a message at the start of each rule with the list of files that required an update, e.-g.:

.. code::

   Build /build/c2ctemplate-cache.json due modification on vars.yaml
   -rw-r--r-- 1 sbrunner geomapfish 1321 2019-01-09 16:59:20.845623078 +0000 /build/c2ctemplate-cache.json
   -rw-rw-r-- 1 sbrunner geomapfish 1299 2019-01-10 08:31:35.707376156 +0000 vars.yaml

Docker-compose
--------------

Logs
....

With the following command you can access the logs:

.. prompt:: bash

   docker-compose logs [<service_name>]

Go inside a container
.....................

With the following command you can get a terminal in a container:

.. prompt:: bash

   docker-compose exec [--user=root] <service_name> bash

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


Developing in Python
--------------------

Add the following environment variable to the geoportal container:

``GUNICORN_PARAMS="-b :80 --worker-class gthread --threads 1 --workers 1 --reload"``

TODO

You can also do a graceful restart of the running gunicorn:

.. prompt:: bash

   docker-compose exec geoportal bash
   kill -s HUP `ps aux|grep gunicorn|head --lines=1|awk '{print $2}'`  # graceful

And finally if you stop and start the container you will see your modifications:

.. prompt:: bash

   docker-compose stop geoportal
   docker-compose start geoportal

Mount c2cgeoportal in the container
...................................

Clone and build c2cgeoportal, see: developer_server_side.

Add a ``docker-compose.override.yml`` file with a ``geoportal`` service containing the following lines:

.. code:: yaml

   version: '2'

   services:
     geoportal:
       volumes:
         - <c2cgeoportal_git_root>/commons/c2cgeoportal_commons:/opt/c2cgeoportal_commons/c2cgeoportal_commons
         - <c2cgeoportal_git_root>/geoportal/c2cgeoportal_geoportal:/opt/c2cgeoportal_geoportal/c2cgeoportal_geoportal
         - <c2cgeoportal_git_root>/admin/c2cgeoportal_admin:/opt/c2cgeoportal_admin/c2cgeoportal_admin

Access to a hidden service
--------------------------

Within the Docker composition you can access a port of a container, you can achieve this via curl, e.-g.:

.. prompt: bash

   curl "http://mapserver:8080?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetCapabilities"

You can also expose a service out of the Docker composition. For that, add a port in your
``docker-compose.yaml``, e.g.:

.. code:: yaml

   services:
     <service>:
       port:
         - 8086:8080

Be careful one port can be open only one time on a server.

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

For performance and proxy issues make sure that all internal URLs in the config file
use localhost (use ``curl "http://localhost/<path>" --header Host:<server_name>``
to test it).

Tilecloud chain
...............

Points to check with TileCloud chain:

* Disabling metatiles should be avoided.
* Make sure that ``empty_metatile_detection`` and ``empty_tile_detection`` are configured correctly.
* Make sure to not generate tiles with a higher resolution than in the raster sources.
