.. _administrator_tilegeneration:

TileGeneration
==============

Introduction
------------

With this solution we solve the following issue:

 * Managing millions of files on the file system is difficult.

 * We should be able to update all the generated tiles.

 * We shouldn't have thousands of expired files.

To do so we need need a tool that can generate the tiles,
update some of them contained in given geometries and delete empty tiles.

On-the-fly tiles generation introduces some issues such as having a growing
number of tiles that may become unmanageable. For example when updating the
data, it is not possible to figure out what tiles should be updated.

For the high usage website we want to put the tiles on S3
with the same tool.

One issue we have if we want to generate all the tiles, the generation
time can grow to more than one month, especially if we have
a high resolution (low if in m/px) on the last zoom level.
Than for the last zoom level we should generate the tiles on the fly
with a low expiry (4 hours for example).
We should use metatiles to don't have too may request to postgres.
And the tiles should be delete after the expiry time.

The chosen solution is a combination of two tools:

 * `MapCache <http://mapserver.org/trunk/mapcache/>`_ for the last zoom level.

 * `TileCloud-Chain <https://github.com/sbrunner/tilecloud-chain>`_ for the tile generation.

MapCache
--------

MapCache is a tool of the MapServer Suite.

It is recommended to use `Memcached <http://memcached.org/>`_ as cache,
since it is the only system that offers automatic deletion of the expired tiles.

To use it you should have MapCache and Memcached installed on your computer.
And Memcached should listen on port 11211.

To clear/flush Memcached cache, use the following command:

   .. code:: bash
     
     echo "flush_all" | /bin/netcat -q 2 127.0.0.1 11211

See the `TileCloud-chain documentation for more details
<https://github.com/sbrunner/tilecloud-chain#configure-mapcache>`_

TileCloud-chain
---------------

TileCloud-chain is a TileCloud-based tool that offers a build chain for
generating tiles from WMS of Mapnik on a local storage or S3 using a
WMTS layout.

It supports the following AWS services for generating tiles:
EC2, SQS, SNS.

`See readme <http://pypi.python.org/pypi/tilecloud-chain>`_.

Initialization
~~~~~~~~~~~~~~

 * Add ``tilecloud-chain`` to the dependencies in the ``setup.py``.

 * Build the project::

   ./buildout/bin/buildout -c buildout_<user>.cfg

 * Install the base template template::

   ./buildout/bin/pcreate --interactive -s tilecloud_chain ../<project_name> package=<package_name>

 * Add configuration to Git:

   .. code:: bash

   	git add tilegeneration buildout_tilegeneration.cfg

Configuration
~~~~~~~~~~~~~

The configuration is done in the self-documented file
``tilegeneration/config.yaml``. The original file is available at:
https://github.com/sbrunner/tilecloud-chain/blob/master/tilecloud_chain/scaffolds/create/tilegeneration/config.yaml.in_tmpl

The main thing to do is to:

 * Set the resolutions we want to generate in the ``grids``.
   If we want to generate different resolution per layers we should create
   deferent grid.
   Sub-level of ``grids`` is the grid name.

 * Configure the ``caches`` and set the ``generation``/``default_cache``.
   Sub-level of ``caches`` is the cache name.

 * Configure the ``layer_default``, the ``layers``, and the
   ``generation``/``default_layers``.
   Sub-level of ``layers`` is the layer name.

 * We can drop the empty tiles with an hash comparison,
   tilecloud-chain has a tool to help us::

       ./buildout/bin/generate_tiles --get-hash <max-zoom>/0/0 --layer <layer>

   We consider that the first tile of the max zoom is empty.
   Than copy past the result in the layer config.

 * If you need it you can generate the WMTS capabilities file::

     ./buildout/bin/generate_controller --generate_wmts_capabilities

 * And an OpenLayers test page::

     ./buildout/bin/generate_controller --openlayers-test

If you generate the tiles locally you don't need all the configuration
variables, because many of them in the ``generation`` part are for
AWS generation.

Tile Generation and management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This package offers two commands lines, one to generate the tiles locally,
see help::

    ./buildout/bin/generate_tiles --help

one to generate the tiles using AWS, see help::

    ./buildout/bin/generate_controller --help

Before start a tile generation on S3 measure the cost::

    ./buildout/bin/generate_controller --cost

If you setup all the default options you can generate the tiles by
using the command::

    ./buildout/bin/generate_tiles

.. note:: Make sure you export AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY::
       export AWS_ACCESS_KEY_ID=XXXXX
       export AWS_SECRET_ACCESS_KEY=YYYY

   If you forget it you will get an explicit message.

Integration in c2cgeoportal
~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the ``viewer.js``, ``api/viewer.js`` and ``edit.js``:

 * Be sure that ``OpenLayers.IMAGE_RELOAD_ATTEMPTS`` is not defined.
 * In ``WMTS_OPTION`` url should be ${tiles_url}.

In the ``config.yaml.in`` define ``tiles_url`` to something like, for S3 usage::

    tiles_url:
    - http://a.tiles.${vars:host}/
    - http://b.tiles.${vars:host}/
    - http://c.tiles.${vars:host}/
    - http://d.tiles.${vars:host}/

The configuration of the ``tiles`` vhost will be done by the sysadmins.

To get your tiles URL in the ``viewer.js`` do:

.. code:: javascript

    <%
    from json import dumps
    %>
    var WMTS_OPTIONS = {
        url: ${dumps(request.registry.settings['tiles_url']) | n},
        ...
    }

And in the ``mobile/config.js`` do:

.. code:: javascript

    var dummy = "<% from json import dumps %>";
    jsonFormat = new OpenLayers.Format.JSON();
    try {
        App.tilesURL = jsonFormat.read('${dumps(request.registry.settings["tiles_url"]) | n}');
    }
    catch (e) {
        App.tilesURL = "";
    }
    var WMTS_OPTIONS = {
        url: App.tilesURL,
        ...
    }

SwitchableWMTS
--------------

Useful tool to switch from TileCloud to MapCache.

See: https://github.com/camptocamp/cgxp/blob/master/openlayers.addins/SwitchableWMTS/lib/OpenLayers/Layer/SwitchableWMTS.js

Internal service
----------------

If you use an internal service to access to the tiles you can use sub domaine
to access to them by using that in ``WMTS_OPTION``::

    url: [
        '${request.route_url('<view>', path='', subdomain='s1')}',
        '${request.route_url('<view>', path='', subdomain='s2')}',
        '${request.route_url('<view>', path='', subdomain='s3')}',
        '${request.route_url('<view>', path='', subdomain='s4')}'
    ]

With ``<view>`` the name of the view that serve the tiles.
The sub domain should obviously be define in the DNS and in the Apache
vhost. If the application is served on deferent URL and you want to use
the sub domain on only one of them you can define in the ``config.yaml.in``
the following::

    # The URL template used to generate the sub domain URL
    # %(sub)s will be replaced by the sub domain value.
    subdomain_url_template: http://%(sub)s.${vars:host}

Tileforge
---------

If you still want to use Tileforge, follow the instructions below.

Integration in c2cgeoportal
~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the ``production.ini.in`` and ``development.ini.in``,
in section ``[app:app]`` add::

    # For tilecache controller
    tilecache.cfg = ${buildout:directory}/tilecache/tilecache.cfg

In ``buildout.cfg`` section ``[buildout]`` add::

    find-links += http://pypi.camptocamp.net/internal-pypi/index/tileforge

In ``<package>/__init__.py`` function ``main`` add::

    from c2cgeoportal.views.tilecache import load_tilecache_config

    # add a TileCache view
    load_tilecache_config(config.get_settings())
    config.add_route('tilecache', '/tilecache{path:.*?}')
    config.add_view(
        view='c2cgeoportal.views.tilecache:tilecache',
        route_name='tilecache')

In ``setup.py`` attribute ``install_requires`` add ``'tileforge',``.

Configuration
~~~~~~~~~~~~~

The configuration file is ``tilecache/tilecache.cfg.in``.

The ``[cache]`` section describes how the tiles are saved.

The ``[DEFAULTS]`` section applies default values to all layers.

The important attributes are:

 * ``layers`` the WMS layers or groups.
 * ``metadata_connection`` connection to the database.
 * ``metadata_data`` the SQL request to get the geometries that should be generated.
 * ``metadata_image_postproc`` a post process apply on the generated tiles.


The destination folder needs to be created with the good rights,
(www-data should be able to write on it)::

    mkdir /var/sig/tilecache
    chmod o+w /var/sig/tilecache

Commands
~~~~~~~~

Usage::

    ./buildout/bin/tilemanager [OPTIONS] LAYERNAME [ZOOM_START ZOOM_STOP]

    Options:
      --version             show program version number and exit
      -h, --help            show this help message and exit
      -c CONFIG, --config=CONFIG
                            path to configuration file
      -b BBOX, --bbox=BBOX  restrict to specified bounding box
      -t THREADS, --threads=THREADS
                            number of concurrent threads to run (defaults is 8)
      -r RETRY, --retry=RETRY
                            retry to generated tiles from RETRY file
      -v, --verbose         make lots of noise


Run on a BBOX::

    sudo -u www-data ./buildout/bin/tilemanager -c tilecache/tilecache.cfg --bbox=<left>,<bottom>,<right>,<top> <tileforge_layer>

Run on configured diff table::

    sudo -u www-data ./buildout/bin/tilemanager -c tilecache/tilecache.cfg <tileforge_layer>

.. note:

    We run the tile forge with the www-data rights to allows the web server to creates new tiles.

Tiles
~~~~~

The tiles will be stored in the folder
``/var/sig/tilecache/c2cgeoportal->instanceid>_tilecache``,
in the WMTS format.

To regenerate only the tiles that have changed, you can
specify in the layer the attribute ``metadata_data`` how to get the
geometries where there are some modifications. For example:
``metadata_data = "<geometry_column> FROM <table>"``.
We also need the database connection than we need:
``metadata_connection = ${mapserver_connection}``.

A post-processing command can be set by using the attribute:
``metadata_image_postproc``.
