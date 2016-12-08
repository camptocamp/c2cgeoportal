.. _integrator_backend_geoserver:

Specific configuration for GeoServer
=========================================

Viewer configuration
--------------------

In the ``<package>/templates/viewer.js`` file, make sure no namespace is added for WFS::

    cgxp.WFS_FEATURE_NS = undefined;

Application configuration
-------------------------

Add an OGC server in the admin interface for Geoserver (type: geoserver, auth: Geoserver auth).

In the ``vars_<project>.yaml`` file, define in the ``vars`` section:

.. code:: yaml

    mapserverproxy:
        default_ogc_server: <ogc server name>
