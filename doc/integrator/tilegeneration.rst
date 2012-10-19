.. _administrator_tilegeneration:

TileCloud
=========

For the old project that use Tileforge see below.

With TileCloud and TileCloud-chain, we can generate tiles from WMS or Mapnik
to the local storage or S3 using a WMTS layout.

In the future he will be able to use Amazon services to generates the tiles
(AWS, ESB, SQS, SNS, CloudFront).

See: http://pypi.python.org/pypi/tilecloud-chain.

Initialisation and Configuration
--------------------------------

 * Add ``tilecoud-chain`` to the dependencies in the ``setup.py``.

 * Build the project::

   ./buildout/bin/buildout -c buildout_<user>.cfg

 * Install the base template template::

   ./buildout/bin/pcreate --interactive -s tilecloud_chain ../<project_name> package=<package_name>

 * Edit the configuration file ``tilegeneration/config.yaml``,
   actually he is self documented, original file:
   https://github.com/sbrunner/tilecloud-chain/blob/master/tilecloud_chain/scaffolds/create/tilegeneration/config.yaml

 * Add configuration to GIT::

   git add tilegeneration buildout_tilegeneration.cfg

Tile Generation and management
------------------------------

This package offer two commands line be free to see the help::

    ./buildout/bin/generate_controller --help
    ./buildout/bin/generate_tiles --help

Before start a tile generation on S3 measure the cost::

    ./buildout/bin/generate_tiles --cost

If you setup all the default options you can generates the tiles by
using the command::

    ./buildout/bin/generate_tiles

Integration in c2cgeoportal
---------------------------

In the ``viewer.js``, ``apiviewer.js`` and ``edit.js``:

 * Be sure that ``OpenLayers.IMAGE_RELOAD_ATTEMPTS`` is not defined.
 * In ``WMTS_OPTION`` url should be ${tilecache_url}.

In the ``config.yaml.in`` define ``tilecache_url`` to something like, for S3 usage::

    tilecache_url:
    - http://wmts0.<host>
    - http://wmts1.<host>
    - http://wmts2.<host>
    - http://wmts3.<host>
    - http://wmts4.<host>

And for tiles on local file system::

    tilecache_url:
    - http://${vars:host}/${vars:instanceid}/tiles

If your tiles is on local file system you should also create a way to access to
your tiles than create the file ``apache/tiles.conf.in`` with the content::

    Alias /${vars:instanceid/tiles/ /var/sig/tilecache/
    <Location /${vars:instanceid}/tiles>
        ExpiresActive on
        ExpiresDefault "now plus 4 hours"
        Header set Cache-Control "public, max-age=28800"
    </Location>


MapCache
========

Map cache can be a good solution to cash the tiles of the last zoom levels.

The idea is to generate the tiles with TileCloud got the first zoom levels
and have a short time (some hours) cache for the last zoom levels.

See: http://mapserver.org/trunk/mapcache/config.html


SwitchableWMTSSource
====================

Useful tool to switch from TileCloud to MapCache.

See: http://docs.camptocamp.net/cgxp/lib/plugins/SwitchableWMTSSource.html


Tileforge
=========

Integration in c2cgeoportal
---------------------------

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
-------------

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
--------

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
-----

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

