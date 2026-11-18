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

The OGC Server should have the same name than the alias and use the following URL:
``config://mapserver/mapserv_proxy/<alias>?MAP=<alias>``, where ``<alias>`` is the name of the alias.
The alias is at two place in the URL to make working both the WMS and the OGC API.

For QGIS Server, the URL didn't changes, it is ``config://qgisserver?MAP=<project_file>``.

QGIS Server and MapServer are already configured to support the OGC API and detect automatically if the compatible path is requested.

OGC API features are accessible through ``mapserv_proxy``, with the following URLs:

* ``/mapserv_proxy/<ogc-server>/ogcapi`` and ``/mapserv_proxy/<ogc-server>/ogcapi/*``:
  The MapServer and QGIS Server paths, the first one is the landing page.

QGIS Server uses ``/ogcapi`` as the OGC API root by default since QGIS 4, it can be configured with
``QGIS_SERVER_API_WFS3_ROOT_PATH`` since QGIS 3.44.3. The former ``/mapserv_proxy/<ogc-server>/wfs3/*``
paths are removed.

The ``ogcapi`` root path is also the one used by c2cgeoportal in the proxy routes and in the URLs
published in the themes, then ``QGIS_SERVER_API_WFS3_ROOT_PATH`` should keep its default value,
``/ogcapi``, in the QGIS Server configuration. With a QGIS Server older than 3.44.3 the OGC API root
path is ``/wfs3`` and doesn't match the c2cgeoportal paths.

QGIS Server builds the OGC API URLs from the request, the proxy forwards the original ``Host`` header and
the ``HTTPS`` environment variable of the QGIS Server container should be set to ``on`` when the
application is served in HTTPS.

As the links are built from the request URL path, the ``OGC API path forwarding`` option of the OGC
server should be enabled: the proxy forwards the full path visible by the client (including the entry
point, ``VISIBLE_ENTRY_POINT``) to QGIS Server. This option is automatically enabled by the database
upgrade for the existing OGC servers of type ``qgisserver``.

URLs published in the themes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When the map, query or edit protocol of an OGC server is an OGC API protocol, the
:ref:`themes webservice <developer_webservices>` publishes the root path of the API in
``uses.<use>.url``, and not the WMS/WFS style URL with parameters. Then the client builds its
requests from that root path, for example ``<url>/collections/<collection>/items``.

With an authentication others than ``No auth``, the root path is the one of the proxy,
``/mapserv_proxy/<ogc-server>/ogcapi``, and the ``ogcserver_type`` parameter tells to the proxy which
URL (base, query or edit URL) and which authentication of the OGC server should be used, like for the
WMS/WFS requests. Without a URL defined for the use, the parameter is only set for the map use, the
proxy then uses the base URL and the base authentication of the OGC server.

With the ``No auth`` authentication, the URL of the use is used as is (the internal ``config://``
schema is interpreted) and the OGC API root path is appended to it.


OGC API Documentation
---------------------

`MapServer documentation <https://mapserver.org/ogc/ogc_api.html>`_.

`QGIS Server documentation <https://docs.qgis.org/latest/en/docs/server_manual/services/ogcapif.html>`_.
