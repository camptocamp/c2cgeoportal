.. _integrator_tilegeneration_doc:

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

* `TileCloud-Chain <https://github.com/camptocamp/tilecloud-chain>`_ for the tile generation.


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


.. note::

   Points to check with TileCloud chain:

   * Disabling metatiles should be avoided.
   * Make sure that ``empty_metatile_detection`` and ``empty_tile_detection`` are configured correctly.
   * Make sure to not generate tiles with a resolution higher than the one in the raster sources.

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

To be able to connect to the S3 service, you should define the following variables in the ``env.project``
file:

.. code::

  AWS_ACCESS_KEY_ID=<access_key_id>
  AWS_SECRET_ACCESS_KEY=<secret_access_key>

If you do not want to commit these credentials you can add them in your ``~/.bashrc`` file:

.. code::

  export AWS_ACCESS_KEY_ID=<access_key_id>
  export AWS_SECRET_ACCESS_KEY=<secret_access_key>


Web Interface
~~~~~~~~~~~~~

It is possible to run tile generation commands through a web interface located at URL
``<application main URL>/tiles/admin/``. This interface is protected by a password that
must be specified in the ``C2C_SECRET`` environment variable in the ``env.project`` file.

Predefined commands may be set in parameter ``server > predefined_commands`` in the
``tilegeneration/config.yaml.tmpl`` file.


See also
~~~~~~~~

* :ref:`integrator_api`
* :ref:`administrator_mapfile_perepare_raster`
