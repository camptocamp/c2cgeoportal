.. _administrator_tilegeneration:

TileGeneration
==============

Introduction
------------

With this solution we solve the following issue::

 * It difficult to manage millions of files on the files system.
 * We should be able to update all the generated tiles.
 * We shouldn't have thousand of expired files.

For this we need a tool to be able to generate the tiles,
To update on a geometry, to delete empty tiles.

The tile generation on the fly introduce some issue like
having a number of tile that growing and become unmanageable,
for example it the data will be updated it not possible to
know with tiles should be update.

For the high usage website we want to put the tiles on s3
with the same tool.

One issue we have if we want to generate all the tiles, the generation
time can grow to more than one month, especially if we have
a high resolution (low if in m/px) on the last zoom level.
Than for the last zoom level we should generate the tiles on the fly
with a low expiry (4 hours for example).
We should use metatiles to don't have too may request to postgres.
And the tiles should be delete after the expiry time.

The choosed solution is a combination of two tools::

 * `MapCache <http://mapserver.org/trunk/mapcache/>`_ for the last zoom level.
 * `TileCloud-Chain <https://github.com/sbrunner/tilecloud-chain>`_ for the tile generation.

MapCache
--------

MapCache is a tool of the MapServer Suite.

He should be configured to use `Memcached <http://memcached.org/>`_ as
used Cache, that the only cache that able to delete the expired tiles.

With a configured TileCloud-Chain you can add this configuration::

    mapcache:
        mapserver_url: <the url to mapserver, default is ``http://${vars:host}/${vars:instanceid}/mapserv``>
        config_file: <the generated file, default is ``apache/mapcache.xml.in``>
        resolutions: [<list of resolutions distributed by MapCache, the first on should be the same as TileCloud one>]
        memcache_host: <default is localhost>
        memcache_port: <default is 11211>
        layers: [<list of layers that should be served with MapCache>]

Than you should be able to generate the configuration::

   ./buildout/bin/generate_controller --mapcache

TileCloud-chain
---------------

TileCloud-chain is a tool based on TileCloud with offer build chain that
can generate tiles from WMS or Mapnik to the local storage or S3
using a WMTS layout.

He is able to use the following AWS services to generate the tiles:
EC2, SQS, SNS.

See: http://pypi.python.org/pypi/tilecloud-chain.

Initialisation
~~~~~~~~~~~~~~

 * Add ``tilecoud-chain`` to the dependencies in the ``setup.py``.

 * Build the project::

   ./buildout/bin/buildout -c buildout_<user>.cfg

 * Install the base template template::

   ./buildout/bin/pcreate --interactive -s tilecloud_chain ../<project_name> package=<package_name>

 * Add configuration to GIT::

   git add tilegeneration buildout_tilegeneration.cfg

Configuration
~~~~~~~~~~~~~

The configuration file is ``tilegeneration/config.yaml``,
he is self documented, original file:
https://github.com/sbrunner/tilecloud-chain/blob/master/tilecloud_chain/scaffolds/create/tilegeneration/config.yaml.in_tmpl

The main thing to do is to:

 * Set the resolutions we want to generate in the ``grids``.
   If we want to generate different resolution per layers we should create
   deferent grid.
   Sub-level of ``grids`` is the grid name.

 * Configure the ``caches`` and set the ``generation``/``default_cache``.
   Sub-level of ``caches`` is the cache name.

 * Configure de ``layer_default``, the ``layers``, and the
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

If you generate the tiles locally you don't needs all the configuration
variable, because many of them in the ``generation`` part are for
AWS generation.

Tile Generation and management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This package offer two commands line, one to generate the tiles locally,
see help::

    ./buildout/bin/generate_tiles --help

one to generate the tiles using AWS, see help::

    ./buildout/bin/generate_controller --help

Before start a tile generation on S3 measure the cost::

    ./buildout/bin/generate_tiles --cost

If you setup all the default options you can generates the tiles by
using the command::

    ./buildout/bin/generate_tiles

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

SwitchableWMTS
--------------

Useful tool to switch from TileCloud to MapCache.

See: https://github.com/camptocamp/cgxp/blob/master/openlayers.addins/SwitchableWMTS/lib/OpenLayers/Layer/SwitchableWMTS.js

Tileforge
---------

If you steel want to use Tileforge follows the following instruction.

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

The ``[DEFAULTS]`` section applies defaults values to all layers.

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
