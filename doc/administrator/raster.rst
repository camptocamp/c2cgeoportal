.. _administrator_raster:

Raster configuration
=====================

With c2cgeoportal we can access directly to raster file to have a value on a 
point (with raster web service) or on a line (with profile web service).

For that you should configure them in the ``buildout.cfg`` file in the 
``[vars]`` section bay adding somthing like this::

    raster = {
            "mnt": { "type": "shp_index", "file": "/var/sig/altimetrie/mnt.shp", "round": 1 },
            "mns": { "type": "shp_index", "file": "/var/sig/altimetrie/mns.shp", "round": 1 }
        }

The mnt/mns is a reference name of the raster layer.

The type shp_index is actually the only supported type.

The file is the Shape Index file that collect the raster files.

The raster files should be in the Binary Terrain (BT/VTP .bt 1.3) format.

The round is used to round the result, 1 => round on the unit, 
0.01 on the hundredth, an so on.

Those raster data will be used by the RightClick, the YXZ and the Profile components.
