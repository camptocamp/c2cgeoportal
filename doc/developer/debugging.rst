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

You can run `DEBUG=TRUE make ...` to have some debug message.
Actually we display the running rule and why she is running (dependence update).

Docker
------

Edit a file in a running apache WSGI container

.. prompt:: bash

   docker exec -ti <package>_wsgi_1 bash
   vi ...
   kill -s USR1 1  # graceful


Performance or network error
----------------------------

For performance and proxy issues make sure that all internal URLs in the config file
use localhost (use ``curl "http://localhost/<path>" -H Host:<server_name>``
to test it).

Tilecloud chain
...............

Points to check with TileCloud chain::

 * Disabling metatiles should be avoided.
 * Make sure that``empty_metatile_detection`` and ``empty_tile_detection`` are configured correctly.
 * Make sure to not generate tiles with a higher resolution than in the raster sources.
