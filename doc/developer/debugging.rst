.. _developer_debugging:

Application debugging
=====================

The goal of this document is to give some troubleshooting tips.

First, you should copy the file ``docker-compose.override.sample.yaml`` to
``docker-compose.override.yaml``, and update the composition ``docker compose up -d``.

Then access the application on `https://localhost:8484/ <https://localhost:8484/>`_.


Browser
-------

You can use the browser-integrated debugging tool, usually available with the ``F12`` key.


Sources map
-----------

For debugging purposes, it is better to have all the JavaScript and Style Sheets in separated, non-minified
files. To achieve this, you can use the sources maps, a function activable in the browser's debugging tool.


Webpack
-------

To have faster builds, you need to use the Webpack dev server; you can achieve this as follows.

In the file ``geoportal/<package>_geoportal/static-ngeo/js/apps/<interface>.html.ejs``,
remove the ``ng-strict-di`` in the ``html`` tag.

Be sure that the service ``webpack_dev_server`` is present and uncommented in the
``docker-compose.override.yaml`` file.

Restart your application as usual.

Open the application at the following URL: ``https://localhost:8484/dev/<interface>.html``.


Pyramid debugtoolbar
--------------------

With the default ``docker-compose.override.yaml``, the debug toolbar should appear.

Then the error is directly shown in the request that fails.

You can also open the debug toolbar at `https://localhost:8484/_debug_toolbar/ <https://localhost:8484/_debug_toolbar/>`_


Authentication
--------------

For better security, the session cookie is accessible only via http protocol (meaning, not in JavaScript),
and is secure (meaning, the cookie is transmitted only in https requests, not in http requests).
For this reason, you should have your application running on https also in your development environment.

With the default configuration in the file ``docker-compose.override.yaml``, your application will be
available in ``https``, and the authentication will work.


Auto login
----------

To be automatically logged in with a user present in the database you should set in the
``docker-compose.override.yaml``:

.. code:: yaml

   services:
     geoportal:
       environment:
         - DEV_LOGINNAME=<username>

Then you will directly be logged in to the user.

C2C WSGI Utils tools
--------------------

:ref:`integrator_c2cwsgiutils` offers some debugging tools on the URL ``/c2c``.

Cache
-----

There a view that expose the cache status of the application, to be able to access to this view you should
set the environment variable ``GEOMAPFISH_DEBUG_MEMORY_CACHE`` to ``true``.

Then you can access the cache status through the :ref:`integrator_c2cwsgiutils` ``/c2c`` URL.

Mapserver
---------

Sometimes, more information can be obtained by using this command:

.. prompt:: bash

    docker compose exec mapserver shp2img -m /etc/mapserver/mapserver.map -o /tmp/test.png \
        -e 500000 100000 700000 300000 -s 1000 1000 [-l <layers>]

You may also activate MapServer's debug mode and set the environment variable ``MS_DEBUGLEVEL``
of the MapServer container ``DEBUG`` to ``5`` (most verbose level, default is 0).

`More information <https://mapserver.org/optimization/debugging.html?highlight=debug#debug-levels>`_


Docker-compose
--------------

Logs
....

With the following command, you can access the logs:

.. prompt:: bash

   docker compose logs -f --tail=20 [<service_name>]

To have the access log on gunicorn you should add the option ``--access-logfile=-`` in the gunicorn
configuration (``gunicorn.conf.py`` file).

Go inside a container
.....................

With the following command, you can get a terminal in a container:

.. prompt:: bash

   docker compose exec [--user=root] <service_name> bash

Multiple dev on one server
..........................

When you want to run multiple instances on the same server, you should:

- Use a different docker tag for each instance (``DOCKER_TAG`` in the file ``.env`` files,
  used on the build and on the run)
- Use a different project name for each instance (``COMPOSE_PROJECT_NAME`` in the
  ``.env`` or option ``-p`` of ``docker compose``)
- Use a different port for each instance (``DOCKER_PORT`` in the ``.env``)
- If you want to serve your instances through the same Apache server, each instance must have
  different entry points. (``VISIBLE_ENTRY_POINT`` in the ``.env``)


Developing in Python
--------------------

Create a development ``docker-compose.override.yaml``
.....................................................

Be sure that the volume for the project is not commented out in ``docker-compose.override.yaml``.

With the ``docker-compose.override.yaml`` configuration, Gunicorn will automatically restart
on code modification.

You can also do a graceful reload of the running Gunicorn webserver:

.. prompt:: bash

   kill -s HUP `ps aux|grep gunicorn|head --lines=1|awk '{print $2}'`

Working on c2cgeoportal itself
..............................

Clone and build c2cgeoportal, see :ref:`developer_server_side`.

If it is not already done, copy the file ``docker-compose.override.sample.yaml`` to
``docker-compose.override.yaml``.
Be sure that the volumes for c2cgeoportal are uncommented.

Remote debugging using Visual Studio Code
.........................................

* In ``geoportal/requirements.txt`` uncomment ``ptvsd``.
* In the code add ``breakpoint()`` where you want to add a breakpoint.
* In Visual Studio Code use the config:

  .. code::

     {
         "name": "Python: Remote Attach",
         "type": "python",
         "request": "attach",
         "port": 5678,
         "host": "localhost",
         "pathMappings": [
             {
                 "localRoot": "${workspaceFolder}/project/",
                 "remoteRoot": "/app/"
             },
             {
                 "localRoot": "${workspaceFolder}/c2cgeoportal/",
                 "remoteRoot": "/opt/c2cgeoportal/"
             }
         ]
     },

See also: `ptvsd usage <https://github.com/microsoft/ptvsd#ptvsd-import-usage>`_,
`Python debug configurations in Visual Studio Code <https://code.visualstudio.com/docs/python/debugging>`_

.. _upgrade_debugging:

Debugging the upgrade procedure
...............................

When upgrading a c2cgeoportal application, things happen as follow:

- You manually run `./build --upgrade <target_version>`;
- This script downloads the `./upgrade` script from target branch on GitHub;
- The freshly downloaded `./upgrade` script pull images from Docker Hub;
- The `c2cupgrade` tool is ran from the fresh pulled image.

Note that this does not offer you the possibility to interfere or debug anything.

To be able to debug this workflow, we've added a `--debug` parameter on those scripts that you can set to
the root of your local c2cgeoportal folder, example:

  .. code:: bash

   # Initiate the upgrade by getting the ./upgrade script from you local c2cgeoportal clone.
   ./build --debug=../c2cgeoportal --upgrade master

   # Run the upgrade step 1 without pulling images from Docker hub,
   # and with c2cupgrade file mounted from you local c2cgeoportal folder.
   ./upgrade --debug=../c2cgeoportal latest 1

With this it is possible to debug `./upgrade` and `c2cupgrade` scripts on the fly when upgrading a real
c2cgeoportal application.

Profiling
.........

We can profile the application by using `wsgi_lineprof <https://wsgi-lineprof.readthedocs.io/>`_.

* In ``geoportal/requirements.txt`` uncomment ``wsgi-lineprof``.
* In ``geoportal/<package>_geoportal/__init__.py`` replace ``return config.make_wsgi_app()`` by:

  .. code:: python

    from wsgi_lineprof.middleware import LineProfilerMiddleware
    from wsgi_lineprof.filters import FilenameFilter, TotalTimeSorter
    filters = [
        FilenameFilter("c2cgeoportal.*", regex=True),
        TotalTimeSorter(),
    ]
    return LineProfilerMiddleware(config.make_wsgi_app(), filters=filters)

Then in the logs you will have messages with the profiling information.

Access to a hidden service
--------------------------

Within the Docker composition, you can access a port of a container; you can achieve this via ``curl``, e.-g.:

.. prompt:: bash

   docker compose exec tools curl "http://mapserver:8080?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetCapabilities"

You can also expose a service out of the Docker composition. For that, add a port in your
``docker-compose.yaml``, e.g.:

.. code:: yaml

   services:
     <service>:
       port:
         - 8086:8080

Be careful, each port can be open only one time on a server.


Use a specific version of ngeo
------------------------------

Clone ngeo and build:

.. prompt:: bash

   cd geoportal
   git clone https://github.com/camptocamp/ngeo.git
   cd ngeo
   git check <branch>
   cd ../..

Add the following alias in your ``webpack.apps.js.tmpl`` file:

.. code:: js

    resolve: {
      alias: {
        <package>: ...,
   +    ngeo: path.resolve(__dirname, 'ngeo/src'),
   +    gmf: path.resolve(__dirname, 'ngeo/contribs/gmf/src'),
      }
    }
