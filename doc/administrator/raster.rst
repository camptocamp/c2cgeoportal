.. _administrator_raster:

Raster configuration
=====================

c2cgeoportal applications include web services for getting DEM
<http://en.wikipedia.org/wiki/Digital_elevation_model>
information.
The ``raster`` web service allows getting information for points.
The ``profile`` web service allows getting information for lines.

To configure these web services you need to set the raster
variable in the ``[vars]`` section of the project's ``buildout.cfg`` file.
For example::

    raster = {
            "mnt": { "file": "/var/sig/altimetrie/mnt.shp", "round": 1 },
            "mns": { "file": "/var/sig/altimetrie/mns.shp", "round": 1 }
        }

raster is a list of "DEM layers". There are only two entries in this example,
but there could be more.

The keys (``mnt`` and ``mns`` in this example) are just strings/names.
These strings can be translated for appropriate formatting in the UI.

``file`` provide the path to the shape index that references the raster files.
The raster files should be in the Binary Terrain (BT/VTP .bt 1.3) format.

``round`` specifies how the result values should be rounded.
For instance '1': round to the unit, '0.01': round to the hundredth, etc.

The application viewer should be configured with one (or more) of the
``RightClick``, the ``YXZ`` and the ``Profile`` ``CGXP`` plugins for
the DEM data to be viewable in the web application.
