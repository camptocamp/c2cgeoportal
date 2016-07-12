.. _integrator_backend_geoserver:

Specific configuration for GeoServer
=========================================

Viewer configuration
--------------------

In the ``<package>/templates/viewer.js`` file, make sure no namespace is added for WFS::

    cgxp.WFS_FEATURE_NS = undefined;

Application configuration
-------------------------

In the ``vars_<project>.yaml`` file, define in the ``vars`` section:

.. code:: yaml

    mapserverproxy:
        mapserv_url: http://your.geoserver/geoserver/wms
        geoserver: true
