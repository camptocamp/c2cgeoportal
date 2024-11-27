.. _integrator_ogc_api:

OGC API Features
----------------

The OGC API is a new standard that defines a modular API following the REST standard to access spatial data.
The current implementation in c2cgeoportal is only on the server side. It is based on the
`OGC API - Features <https://ogcapi.ogc.org/features/>` standard and only works
with the ``items`` request using a ``bbox`` filter.

It is currently supported by both MapServer and QGIS Server.

In the MapServer configuration file, the following changes could be added to set an alias to a the ``MAPS`` block:

.. code::

    #
    # Map aliases
    #
    MAPS
        ExampleOGCserver "/etc/mapserver/mapserver.map"
    END

Then use this alias as the ogc-server value in the URL for MapServer.
e.g.: ``config://mapserver/mapserv_proxy/ExampleOGCserver``.

It is also recommended for any server type, to remove all special characters in the OGC Server names because they appear in the path of the URL.

QGIS Server and MapServer are already configured to support the OGC API and detect automatically if the compatible path is requested.

Landing pages for both MapServer and QGIS Server are not supported yet.

OGC API features are accessible through ``mapserv_proxy``, with the following URLs:
* ``/mapserv_proxy/<ogc-server>/ogcapi/*``: The MapServer path.
* ``/mapserv_proxy/<ogc-server>/wfs3/*``: The QGIS Server path.


OGC API Documentation
---------------------

`MapServer documentation <https://mapserver.org/ogc/ogc_api.html>`_.

`QGIS Server documentation <https://docs.qgis.org/latest/en/docs/server_manual/services/ogcapif.html>`_.
