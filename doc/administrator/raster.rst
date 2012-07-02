.. _administrator_raster:

Raster configuration
=====================

It is possible to access some raster file to get data about a
point (with ``raster`` web service) or a line (with ``profile`` web service).

To configure the web services, edit the ``buildout.cfg`` file
and add in the ``[vars]`` section::

    raster = {
            "mnt": { "type": "shp_index", "file": "/var/sig/altimetrie/mnt.shp", "round": 1 },
            "mns": { "type": "shp_index", "file": "/var/sig/altimetrie/mns.shp", "round": 1 }
        }

``mnt`` and ``mns`` are references to the raster layer.

As for now ``shp_index`` is the only supported type.

``file`` is the shape index that lists the raster files.

The raster files should be in the Binary Terrain (BT/VTP .bt 1.3) format.

``round`` specifies how the result must be rounded. For instance
'1': round to the unit, '0.01': round to the hundredth, an so on.

Those raster data will be used by the RightClick, the YXZ and the Profile components.
