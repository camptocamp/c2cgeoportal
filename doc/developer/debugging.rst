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

In the file ``geoportal/demo_geoportal/static-ngeo/js/apps/<interface>.html.ejs``,
remove the ``ng-strict-di`` in the ``html`` tag.

If it's not already done copy the file ``docker-compose.override.sample.yaml`` to
``docker-compose.override.yaml``.
Be sure thate the service ``webpack_dev_server`` is present and uncommented.

Restart your application as usual.

Open the application at the following URL: ``https://172.17.0.1:8484/dev/<interface>.html``.


Pyramid debugtoolbar
--------------------

If it's not already done copy the file ``docker-compose.override.sample.yaml`` to
``docker-compose.override.yaml``.

Then the error is directly shown in the query that fails.

You can also open it on `https://172.17.0.1:8484/_debug_toolbar/ <https://172.17.0.1:8484/_debug_toolbar/>`_


Authentication
--------------

For security issue the cookie is accessible only in http (meens not JavaScript),
and is secure (means sent on https request, not http).
For that and for some other issues we should have our application on https also for development.

To do that you should, if it's not already done, just copy the file ``docker-compose.override.sample.yaml``
to ``docker-compose.override.yaml``.

Then access the application on `https://172.17.0.1:8484/ <https://172.17.0.1:8484/>`_.


Mapserver
---------

Sometimes, more information can be obtained by using this command:

.. prompt:: bash

    docker-compose exec mapserver shp2img -m <mapfile> -o test.png -e <minx> <miny> <maxx> <maxy> \
        -s <sizex> <sizey> -l <layers>

You may also activate MapServer's debug mode and set the environment variable ``MS_DEBUGLEVEL``
of the MapServer container ``MS_DEBUGLEVEL`` to ``5`` (most verbose level, default is 0).

`More information <https://mapserver.org/optimization/debugging.html?highlight=debug#debug-levels>`_


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

- Use a different docker tag for each instance
- Use a different project name for each instance

Use a different docker tag
..........................

Just define an environment variable in the build:

.. prompt:: bash

   DOCKER_TAG=<tag> ./docker-run make build


Developing in Python
--------------------

Create a development docker-compose.override.yaml
.................................................

If it's not already done copy the file ``docker-compose.override.sample.yaml`` to
``docker-compose.override.yaml``.

Be sure that the volume for the project is not commented.

You can also do a graceful restart of the running gunicorn:

.. prompt:: bash

   docker-compose exec geoportal bash
   kill -s HUP `ps aux|grep gunicorn|head --lines=1|awk '{print $2}'`  # graceful

And finally if you restart the container you will see your modifications:

.. prompt:: bash

   docker-compose restart geoportal

Working on c2cgeoportal itself
..............................

Clone and build c2cgeoportal, see :ref:`developer_server_side`.

If it's not already done copy the file ``docker-compose.override.sample.yaml`` to
``docker-compose.override.yaml``.
Be sure that the volumes for c2cgeoportal are uncommented.


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

For performance and proxy issues, make sure that all internal URLs in the config file
use localhost (use ``curl "http://localhost/<path>" --header Host:<server_name>``
to test it).

TileCloud chain
...............

Points to check with TileCloud chain:

* Disabling metatiles should be avoided.
* Make sure that ``empty_metatile_detection`` and ``empty_tile_detection`` are configured correctly.
* Make sure to not generate tiles with a resolution higher than the one in the raster sources.
