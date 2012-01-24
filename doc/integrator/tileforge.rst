.. _administrator_tileforge:

Tileforge
=========

Configuration
-------------

The configuration file is ``tilecache/tilecache.cfg.in``.

The ``[cache]`` section describes how the tiles are saved.

The ``[DEFAULTS]`` section applies defaults to all layers.

The important attributes are:

 * ``layers`` the WMS layers or groups.
 * ``metadata_connection`` connexion to the database.
 * ``metadata_data`` the SQL request to get the geometries that should be generated. 
 * ``metadata_image_postproc`` a post process apply on the generated tiles.

Commands
--------

Usage::

    ./buildout/bin/tilemanager [OPTIONS] LAYERNAME [ZOOM_START ZOOM_STOP]

    Options:
      --version             show program's version number and exit
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

  ./buildout/bin/tilemanager -c tilecache/tilecache.cfg --bbox=<left>,<bottom>,<right>,<top> <tileforge_layer>

Run on configured diff table::

  ./buildout/bin/tilemanager -c tilecache/tilecache.cfg <tileforge_layer>

Tiles
-----

The tiles will be stored int the folder
``/var/sig/tilecache/c2cgeoportal->instanceid>_tilecache``,
in the WMTS format.

To seed only on the tiles that's have changes, you can add in table the
modified geometries, and in the coniguration file, in the layer definition
add ``metadata_connection = ${mapserver_connection}`` used to connect to 
the database, ``metadata_data = "<geometry> FROM <table>"``  to build
the select request to get the geometries.

A post prosses command can be set by using the attribute:
``#metadata_image_postproc``.

