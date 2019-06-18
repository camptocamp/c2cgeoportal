.. _integrator_raster:

Digital Elevation Tools
=======================

c2cgeoportal applications include web services for getting
`DEM <https://en.wikipedia.org/wiki/Digital_elevation_model>`_ information.
The ``raster`` web service allows getting information for points.
The ``profile`` web service allows getting information for lines.

To configure these web services, you need to set the ``raster`` variable in the application config (``vars.yaml``). For example:

.. code:: yaml

    raster:
        mns:
            file: /var/sig/altimetrie/mns.vrt
            type: gdal
            round: 1
        mnt:
            file: /var/sig/altimetrie/mnt.vrt
            type: gdal
            round: 1

``raster`` is a list of "DEM layers". There are only two entries in this example, but there could be more.

``file`` provides the path to the shape index that references the raster files.
The raster files should be in the Binary Terrain (BT/VTP .bt 1.3) format.
One may use GDAL/OGR to convert data to such a format.

``type`` ``shp_index`` (default) for Mapserver shape index, or ``gdal`` for all supported GDAL sources.
We recommend to use a `vrt <https://www.gdal.org/gdal_vrttut.html>`_ file built with
`gdalbuildvrt <https://www.gdal.org/gdalbuildvrt.html>`_.

``nodata`` specifies the nodata value.
By default the nodata value is directly read from the source.

``round`` specifies how the result values should be rounded.
For instance '1': round to the unit, '0.01': round to the hundredth, etc.

.. note:: gdalbuildvrt usage example:

    Set the environment variables (example for Exoscale):

    .. prompt:: bash

        export AWS_DEFAULT_REGION=ch-dk-2
        export AWS_S3_ENDPOINT=sos-ch-dk-2.exo.io
        export AWS_ACCESS_KEY_ID=<key>
        export AWS_SECRET_ACCESS_KEY=<secret>

    Get the list of uploaded files:

    .. prompt:: bash

        aws --endpoint-url https://sos-ch-dk-2.exo.io/ --region ch-dk-2 s3 ls s3://<bucket>/<folder>

    Create a file named e.g.: ``list.txt`` with the files we want to generate.

    .. code::

        /vsis3/<bucket>/<folder>/<file>

    And finally generate the VRT file with:

    .. prompt:: bash

        gdalbuildvrt -input_file_list list.txt /vsis3/<bucket>/<folder>/<file>.vrt
