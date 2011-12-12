
.. _infrastructure_notice:

=====================
Infrastructure notice
=====================

Create a WMTS layer
===================

* Make sure that ``/var/sig/tilecache/`` exists and is writeable by the user ``www-data``.
* Add the matching layers definitions in the mapfile (``mapserver/c2cgeoportal.map.in``).
* Add a layer entry in ``tilecache/tilecache.cfg.in``. The ``layers`` attribute 
  must contain the list of mapserver layers defined above.
* Update the layers sources list (``viewer_layers`` block) in the 
  ``<package>/templates/viewer.js`` template. The ``layer`` parameter is the name 
  of the tilecache layer entry just added in ``tilecache/tilecache.cfg.in``.

