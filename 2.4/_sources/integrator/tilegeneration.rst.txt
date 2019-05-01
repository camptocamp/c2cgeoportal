.. _administrator_tilegeneration:

TileGeneration
==============

Introduction
------------

With this solution, we solve the following issues:

* Managing millions of files on the file system is difficult.
* We should be able to update all the generated tiles.
* We should not have thousands of expired files.

To do so, we need need a tool that can generate the tiles,
update some of them contained in given geometries and delete empty tiles.

On-the-fly tiles generation introduces some issues such as having a growing
number of tiles that may become unmanageable. For example, when updating the
data, it is not possible to figure out what tiles should be updated.

For high usage websites, we want to put the tiles on S3 with the same tool.

One issue we have if we want to generate all the tiles is that the generation time can grow to more than one month,
especially if we have a high resolution (low if in m/px) on the last zoom level.
Therefore for the last zoom level we should generate the tiles on the fly
with a low expiry (4 hours for example).
We should use metatiles to reduce the number of requests to postgres.
And the tiles should be deleted after the expiry time.

The chosen solution is a combination of two tools:

* `MapCache <https://mapserver.org/trunk/mapcache/>`_ for the last zoom level.

* `TileCloud-Chain <https://github.com/camptocamp/tilecloud-chain>`_ for the tile generation.

MapCache
--------

MapCache is a tool of the MapServer Suite.

It is recommended to use `Memcached <https://memcached.org/>`_ as cache,
since it is the only system that offers automatic deletion of the expired tiles.

To use it, you should have MapCache and Memcached installed on your computer.
And Memcached should listen on port 11211.

To clear/flush Memcached cache, use the following command in the container:

.. prompt:: bash

    echo "flush_all" | /bin/netcat -q 2 127.0.0.1 11211

See the `TileCloud-chain documentation for more details
<https://github.com/camptocamp/tilecloud-chain#configure-mapcache>`_.

TileCloud-chain
---------------

TileCloud-chain is a TileCloud-based tool that offers a build chain for
generating tiles from WMS of Mapnik on a local storage or S3 using a
WMTS layout.

It supports the following AWS services for generating tiles:
EC2, SQS, SNS.

See the `readme <https://pypi.python.org/pypi/tilecloud-chain>`_.

Initialization
~~~~~~~~~~~~~~

* Build the project as usual

* In the ``<project>.mk``, activate the tile generation:

  .. code::

     TILECLOUD_CHAIN ?= TRUE

* If you use local cache, activate the capabilities generation with:

  .. code::

     TILECLOUD_CHAIN_LOCAL ?= TRUE

  and set the ``wmtscapabilities_file`` to ``${WMTSCAPABILITIES_PATH}`` in your
  ``tilegeneration/config.yaml.mako`` file.

* In your ``<prod>.mk``, you can also set the capabilities file name with:

  .. code::

     WMTSCAPABILITIES_PATH = 1.0.0/WMTSCapabilities.xml

* Add configuration to Git:

  .. prompt:: bash

    git add tilegeneration

Configuration
~~~~~~~~~~~~~

The configuration is done in the file
``tilegeneration/config.yaml.mako``. The original file is available at:
https://github.com/camptocamp/tilecloud-chain/blob/master/tilecloud_chain/scaffolds/create/tilegeneration/config.yaml.mako_tmpl

The main thing to do is to:

* Set the resolutions we want to generate in the ``grids``.
  If we want to generate different resolutions per layer, we should create different grids.
  Sub-level of ``grids`` is the grid name.

* Configure the ``caches`` and set the ``generation``/``default_cache``.
  Sub-level of ``caches`` is the cache name.

* Configure the ``layer_default``, the ``layers``, and the ``generation``/``default_layers``.
  Sub-level of ``layers`` is the layer name.

* We can drop the empty tiles with a hash comparison, tilecloud-chain has a tool to help us:

  .. prompt:: bash

     docker-compose exec tilecloudchain generate_tiles --get-hash <max-zoom>/0/0 --layer <layer>

  We consider that the first tile of the max zoom is empty.
  Then copy-paste the result in the layer config.

* If you need it, you can generate the WMTS capabilities file:

  .. prompt:: bash

     docker-compose exec tilecloudchain generate_controller --generate-wmts-capabilities

* And an OpenLayers test page:

  .. prompt:: bash

     docker-compose exec tilecloudchain generate_controller --openlayers-test

If you generate the tiles locally, you do not need all the configuration
variables, because many of them in the ``generation`` part are for
AWS generation.

Tile Generation and management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This package offers two tools, one to generate the tiles locally, see help:

.. prompt:: bash

    docker-compose exec tilecloudchain generate_tiles --help

one to generate the tiles using AWS, see help:

.. prompt:: bash

    docker-compose exec tilecloudchain generate_controller --help

Before starting a tile generation on S3, measure the cost:

.. prompt:: bash

    docker-compose exec tilecloudchain generate_controller --cost

If you setup all the default options, you can generate the tiles by using the command:

.. prompt:: bash

    docker-compose exec tilecloudchain generate_tiles

.. note:: Make sure you export AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:

   .. prompt:: bash

       export AWS_ACCESS_KEY_ID=XXXXX
       export AWS_SECRET_ACCESS_KEY=YYYY

   If you forget it, you will get an error message.
