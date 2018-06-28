.. _administrator_tilegeneration:

TileGeneration
==============

Introduction
------------

With this solution we solve the following issue:

* Managing millions of files on the file system is difficult.

* We should be able to update all the generated tiles.

* We should not have thousands of expired files.

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
We should use metatiles to do not have too may request to postgres.
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

.. prompt:: bash

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

* Build the project:

  .. prompt:: bash

     make docker-build

* In the ``<prokect>.mk`` activate the tile generation:

  .. code::

     TILECLOUD_CHAIN ?= TRUE

* If you use local cache activate the capabilities generation with:

  .. code::

     TILECLOUD_CHAIN_LOCAL ?= TRUE

  and set the ``wmtscapabilities_file`` to ``${wmtscapabilities_path}`` in your
  ``tilegeneration/config.yaml.mako`` file.

* In your ``<prod>.mk`` you can also set the capabilities file name with:

  .. code::

     WMTSCAPABILITIES_PATH = 1.0.0/WMTSCapabilities.xml

* Add configuration to Git:

  .. prompt:: bash

    git add tilegeneration

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
  tilecloud-chain has a tool to help us:

  .. prompt:: bash

     ./docker-run generate_tiles --get-hash <max-zoom>/0/0 --layer <layer>

  We consider that the first tile of the max zoom is empty.
  Than copy past the result in the layer config.

* If you need it you can generate the WMTS capabilities file:

  .. prompt:: bash

     ./docker-run generate_controller --generate-wmts-capabilities

* And an OpenLayers test page:

  .. prompt:: bash

     ./docker-run generate_controller --openlayers-test

If you generate the tiles locally you do not need all the configuration
variables, because many of them in the ``generation`` part are for
AWS generation.

Tile Generation and management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This package offers two commands lines, one to generate the tiles locally,
see help:

.. prompt:: bash

    ./docker-run generate_tiles --help

one to generate the tiles using AWS, see help:

.. prompt:: bash

    ./docker-run generate_controller --help

Before start a tile generation on S3 measure the cost:

.. prompt:: bash

    ./docker-run generate_controller --cost

If you setup all the default options you can generate the tiles by
using the command:

.. prompt:: bash

    ./docker-run generate_tiles

.. note:: Make sure you export AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:

   .. prompt:: bash

       export AWS_ACCESS_KEY_ID=XXXXX
       export AWS_SECRET_ACCESS_KEY=YYYY

   If you forget it you will get an explicit message.
