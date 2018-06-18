.. _integrator_backend_arcgis:

Specific configuration for Arcgis
=================================

Differentiating WMS and WFS services
------------------------------------

It may be necessary to differentiate the WMS and WFS services url.

In the ``OgcServer`` file, define:

.. code:: yaml

    mapserv_url: http://your.arcgis.server/arcgis/services/SOME/FOLDER/MapServer/WMSServer
    mapserv_wfs_url: http://your.arcgis.server/arcgis/services/SOME/FOLDER/MapServer/WFSServer

These are the urls which respond respectively to the *WMS GetCapabilities* and
*WFS GetCapabilities*.


Note
----

ArcGis (even 10.2) does not understand "application/vnd.ogc.gml" for *INFO_FORMAT* in
a *GetFeatureInfo* request and returns only a simple XML formatted response
instead of GML.
