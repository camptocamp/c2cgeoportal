.. _integrator_raster:

Digital Elevation Tools
=======================

c2cgeoportal applications include web services for getting
`DEM <http://en.wikipedia.org/wiki/Digital_elevation_model>`_.
information.
The ``raster`` web service allows getting information for points.
The ``profile`` web service allows getting information for lines.

To configure these web services you need to set the ``raster`` variable in the
application config (``config.yaml``).  For example::

    raster:
      mns:
        file: /var/sig/altimetrie/mns.shp
        round: 1
      mnt:
        file: /var/sig/altimetrie/mnt.shp
        round: 1

``raster`` is a list of "DEM layers". There are only two entries in this example,
but there could be more.

The keys (``mnt`` and ``mns`` in this example) are just strings/names.
These strings can be translated for appropriate formatting in the UI.

``file`` provides the path to the shape index that references the raster files.
The raster files should be in the Binary Terrain (BT/VTP .bt 1.3) format.
One may use GDAL/OGR to convert data to such a format.

``round`` specifies how the result values should be rounded.
For instance '1': round to the unit, '0.01': round to the hundredth, etc.

The application viewer should be configured with one (or more) of the
``ContextualData`` and the ``Profile`` ``CGXP`` plugins for
the DEM data to be viewable in the web application.
