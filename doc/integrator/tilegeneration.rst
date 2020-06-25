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

One issue we have if we want to generate all the tiles is that the generation time can grow to more than one
month, especially if we have a high resolution (low if in m/px) on the last zoom level.
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


Configuration
~~~~~~~~~~~~~

The configuration is done in the file ``tilegeneration/config.yaml.tmpl``.

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

     docker-compose exec tilecloudchain generate_tiles \
        --get-hash <max-zoom>/0/0 --layer <layer>

  We consider that the first tile of the max zoom is empty.
  Then copy-paste the result in the layer config.

If you generate the tiles locally, you do not need all the configuration variables, because many of them
in the ``generation`` part are for AWS generation.


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


AWS credentials
~~~~~~~~~~~~~~~

To be able to connect to the S3 service, you should define the following variables in the ``.env.mako``
file:

code::

  AWS_ACCESS_KEY_ID=<access_key_id>
  AWS_SECRET_ACCESS_KEY=<secret_access_key>

If you do not want to commit these credentials you can add them in your ``~/.bashrc`` file:

code::

  export AWS_ACCESS_KEY_ID=<access_key_id>
  export AWS_SECRET_ACCESS_KEY=<secret_access_key>


See also
~~~~~~~~

* :ref:`integrator_api`
* :ref:`administrator_mapfile_perepare_raster`
