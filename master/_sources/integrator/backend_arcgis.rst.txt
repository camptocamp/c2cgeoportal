.. _integrator_backend_arcgis:

Specific configuration for Arcgis
=================================

WFS namespace
-------------

In the ``<package>/templates/viewer.js`` file, define the url of the WFS service which will be used
to get the namespace required to parse the WFS response::

    cgxp.WFS_FEATURE_NS = "http://your.arcgis.server/arcgis/services/SOME/FOLDER/MapServer/WFSServer";

Differentiating WMS and WFS services
------------------------------------

It may be necessary to differentiate the WMS and WFS services url.

In the ``vars_<project>.yaml`` file, define:

.. code:: yaml

    mapserv_url: http://your.arcgis.server/arcgis/services/SOME/FOLDER/MapServer/WMSServer
    mapserv_wfs_url: http://your.arcgis.server/arcgis/services/SOME/FOLDER/MapServer/WFSServer

These are the urls which respond respectively to the *WMS GetCapabilities* and
*WFS GetCapabilities*.

If your project has a parent (in a parent/child architecture),
in the ``config_child.yaml.mako`` file also define the WFS service separately:

.. code:: yaml

    external_mapserv_wfs_url: http://your.parent.arcgis.server/arcgis/services/SOME/FOLDER/MapServer/WFSServer


WFS geometryName
----------------

Also, the name of the geometry parameter in the WFS response is different in ArcGis.

in the ``<package>/templates/viewer.js`` file, for the *cgxp.plugins.WFSGetFeature* or *cgxp.plugins.GetFeature* plugins, add the
following parameter in the plugin configuration:

    geometryName: 'SHAPE'

Note
----

ArcGis (even 10.2) does not understand "application/vnd.ogc.gml" for *INFO_FORMAT* in
a *GetFeatureInfo* request and returns only a simple XML formated response
instead of GML.

This kind of result can not be parsed correctly by the *cgxp.plugins.GetFeature* plugin,
meaning a WMS GetFeatureInfo result will not display correctly.

It is recommended to use the *cgxp.plugins.WFSGetFeature* plugin that does *only* WFS
queries.
