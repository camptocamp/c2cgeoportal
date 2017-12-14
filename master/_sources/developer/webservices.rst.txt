.. _developer_webservices:

=========================
Webservices documentation
=========================


Theme webservice
================

URL: ``.../themes``

Parameters
----------

* ``version``: ``1`` or ``2``, API version, default is ``1``.
* ``interface``: used interface (optional).
* ``sets``: kind of data we want to get, can be ``all``, ``themes``, ``group``
  or ``background_layers``, default is ``all``.
* ``background``: parent group of background layers to get.
* ``group``: the group to get.
* ``catalog``: ``true`` or ``false``, different error reporting for catalog mode, default is ``false``.
* ``min_levels``: minimum number of group levels that is required, default is ``1``.
* ``role``: role name, not used by the server but it is required for the cache management.

Requests examples:

* themes?version=2
* themes?version=2&background=background
* themes?version=2&group=Transport

Result in v2
------------

Base for all possible results:

.. code:: json

    {
        "ogcServers": {
            "<name>": <OGC Server name>
            ...
        }
        "themes": [<themes>],
        "group": <group>,
        "background_layers": [<layers>],
        "errors": [<errors>]
    }

OGC Server
~~~~~~~~~~

.. code:: json

   {
        "url": "<wms server url>",
        "urlWfs": "<wfs server url>",
        "wfsSupport": (true|false),
        "imageType": "image/(jpeg|png)",
        "isSingleTile": (true|false),
        "type": "(mapserver|geoserver|qgisserver)",
        "credential: (true|false),"
    }


Theme
~~~~~

.. code:: json

    {
        "name": "<name>",
        "icon": "<icon_url>",
        "functionalities": {
            "<name>": "<values>"
        },
        "metadata": {
            "<name>": "<value>"
        },
        "children": [<items>]
    }


Group
~~~~~

.. code:: json

    {
        "name": "<name>",
        "mixed": (true|false),
        # if not mixed
        "ogcServer": {
            "url": "<wms server url>",
            "wfsUrl": "<wfs server url>",
            "wfsSupport": (true|false),
            "imageType": "image/(jpeg|png)",
            "isSingleTile": (true|false),
            "serverType": "(mapserver|geoserver|qgisserver)",
        }
        "metadata": {
            "<name>": "<value>"
        },
        "dimensions": {
            "<name>": "<value>"
        },
        "children": [<items>]
    }


Layer
~~~~~

.. code:: json

    {
        "name": "<name>",
        "type": "(WMS|WMTS)",
        "metadata": {
            "<name>": "<value>"
        },
        "dimensions": {
            "<name>": "<value>"
        }
    }


WMS Layer
~~~~~~~~~

.. code:: json

    {
        "id": <id>,
        "name": "<name in tree>",
        "layers": "<wms_layers>",
        "style": "<style>",
        # if not mixed
        "ogcServer": "<server name>",
        # derecated
        "url": "<wms server url>",
        "urlWfs": "<wfs server url>",
        "wfsSupport": (true|false),
        "isSingleTile": (true|false),
        "imageType": "image/(jpeg|png)",
        "serverType": "(mapserver|geoserver|qgisserver)",
        "minResolutionHint": <minResolutionHint>,
        "maxResolutionHint": <maxResolutionHint>,
        # end derecated
        "metadata": {
            "identifier_attribute_field": "<display_name>",
            "disclaimer": "<disclamer>",
            "legend": (true|false),
            "legend_rule": "<legend_rule>",
            "max_resolution": <max_resolution>,
            "min_resolution": <min_resolution>
        },
        "metadataUrls": {
            "url": <url>,
            "type": "TC211/FGDC",
            "format": "text/html"
        },
        "time": {
            "mode": "(value|range)",
            "interval": [<year>, <month>, <day>, <secound>],
            "resolution": "(year|month|day|secound)",
            "minValue": <minValue>,
            "maxValue": <maxValue>
        },
        "childLayers": [{
            "name": "<name>",
            "queryable": (true|false),
            "minResolutionHint": <minResolutionHint>,
            "maxResolutionHint": <maxResolutionHint>
        }],
        "edit_columns":[{
            "maxLength": <maxLength>,
            "name": "<name>",
            "nillable": (true|false),
            "restriction": "enumeration",
            "enumeration": [
                "<value>"
            ],
            "srid": <srid>,
            "type": "(xsd:string|xsd:decimal|xsd:integer|xsd:boolean|xsd:date|xsd:dateTime|xsd:double|xsd:duration|xsd:base64Binary|xsd:time|gml:CurvePropertyType|gml:GeometryCollectionPropertyType|gml:LineStringPropertyType|gml:MultiLineStringPropertyType|gml:MultiPointPropertyType|gml:MultiPolygonPropertyType|gml:PointPropertyType|gml:PolygonPropertyType)",
            "fractionDigits": <fractionDigits>,
            "totalDigits": <totalDigits>
        }]
    }


WMTS layer
~~~~~~~~~~

.. code:: json

    {
        "url": "<wmts_capabilities_url>",
        "layer": "<wmts_layer>",
        "style": "<style>",
        "matrix_set": "<matrix_set>"
    }


Authentication
==============

Login
-----

Used to login in the application.

URL: ``.../login``

Method: ``POST``

Parameters (post form):

* ``login``
* ``password``
* ``came_from`` the URL where we will redirect after a success

Result HTTP code:

* 200 Success: Success with the JSON result as :ref:`developer_webservices_auth_connected`.
* 302 Found: Success -> redirect on came_from.
* 400 Bad request: When something wrong.

Logout
------

Used to log out of the application.

URL: ``.../logout``

Method: ``GET``

Result HTTP code:

* 200 Success: Success.
* 400 Bad request: When something wrong.

User informations
-----------------

Used to get the user informations.

URL: ``.../loginuser``

Result HTTP code:

* 200 Success: Success.

Annoymous JSON result
~~~~~~~~~~~~~~~~~~~~~

.. code:: json

   {
       "functionality": {
           "<functionnality_name>": ["functionnality_value"],
           ...
       }
   }

.. _developer_webservices_auth_connected:

Connected JSON result
~~~~~~~~~~~~~~~~~~~~~

.. code:: json

   {
       "username": "<username>",
       "is_password_changed": "True"/"False", # If false the user should change his password
       "role_name": "<role_name>",
       "role_id": <role_id>
       "functionality": {
           "<functionnality_name>": ["functionnality_value"],
           ...
       }
   }


Change password
---------------

Used to change the user password.

URL: ``.../loginchange``

Method: ``POST``

Parameters (post form):

* ``oldPassword``
* ``newPassword``
* ``confirmNewPassword``

Result HTTP code:

* 200 Success: Success.
* 400 Bad request: When something wrong.

JSON result
~~~~~~~~~~~

.. code:: json

   {
       "success": "true"
   }


Generate a new password
-----------------------

URL: ``.../loginresetpassword``

Method: ``POST``

Used when the user lost his password.

Parameters (post form):

* ``login``

Result HTTP code:

* 200 Success: Success.
* 400 Bad request: When something wrong.

Success JSON result
~~~~~~~~~~~~~~~~~~~

.. code:: json

   {
       "success": "true"
   }


Full-Text Search
================

URL: ``.../fulltextsearch``

Parameters
----------

* ``query``: Text to search.
* ``limit``: The maximum number of results (optional).
* ``partitionlimit``: The maximum number of results per layer (optional).
* ``lang``: The used language (optional).
* ``interface``: The used interface (optional).
* ``callback``: Name of the callback function (optional, deprecated in v2).

Result
------

A GeoJSON of a feature collection with the properties:

* ``label``: Text to display.
* ``layer_name``: Layer to display.
* ``params``: :ref:`integrator_fulltext_search_params` to set.
* ``actions``: List of actions.

The `action` is a dictionary with:

* ``action``: the action: (add_theme|add_group|add_layer).
* ``data``: data needed for the action (actually, the item name).


Layers
======

Layer description
-----------------

URL: ``.../layers/<layer_id>/md.xsd``

Result
~~~~~~

A standard xsd document that describe the layer.

MapFish protocol
----------------

URL: ``.../layers/<layer_id>/....``

`Parameters and results, see the MapFish protocol <https://github.com/elemoine/papyrus/wiki/Protocol>`_.

Enumerate attributes
--------------------

URL: ``.../layers/<layer_name>/values/<field_name>``

Result
~~~~~~

.. code:: json

    {
        "items": [{
          "label": "<name>", // deprecated in v2
          "value": "<value>"
        }, ...]
    }


Update feature
------------------

URL: ``.../layers/<layer_name>/<layer_id>/<feature_id>``

Success:

.. code:: json

   {
       "type": "FeatureCollection",
       "features": [
          {
             "geometry": {
                "type": "MultiPoint",
                "coordinates": [
                   [
                      648902.2912000001,
                      185911.1152
                   ]
                ]
             },
             "type": "Feature",
             "id": 103,
             "properties": {
                "kind": "tree",
                "good": true,
                "name": "nom",
                "internal_id": null,
                "short_name": "court",
                "height": null,
                "short_name3": "R",
                "short_name2": "2"
             }
          }
       ]
   }

Error :

.. code:: json

    {
        "message": "error description",
        "error_type": "type of error"
    }

Update feature
------------------

URL: ``.../layers/<layer_name>/<layer_id>``

Success:

.. code:: json

   {
       "type": "FeatureCollection",
       "features": [
          {
             "geometry": {
                "type": "MultiPoint",
                "coordinates": [
                   [
                      648902.2912000001,
                      185911.1152
                   ]
                ]
             },
             "type": "Feature",
             "id": 103,
             "properties": {
                "kind": "tree",
                "good": true,
                "name": "nom",
                "internal_id": null,
                "short_name":" court",
                "height": null,
                "short_name3": "R",
                "short_name2": "2"
             }
          }
       ]
   }


Error :

.. code:: json

    {
        "message": "error description",
        "error_type": "type of error"
    }


Raster
======

URL: ``.../raster``

Parameters
----------

* ``lon``: The longitude.
* ``lat``: The latitude.
* ``layers``: The raster layers we want to query.
* ``callback``: Function name to do the callback (optional, deprecated in v2).

Result
------

.. code:: json

    {
        "<layer>": <value>,
        ...
    }


Digital Elevation Model
=======================

URL: ``.../profile.csv`` or ``.../profile.json``

Method ``POST``

Parameters
----------

* ``geom``: Geometry field used to get the profile data.
* ``layers``: On witch layers, default to all.
* ``nbPoints``: Maximum number of points.
* ``callback``: Function name to do the callback (optional, deprecated in v2).

Result
------

A JSON or a CSV file, with 'dist', 'value', 'x', 'y'.


Shortener
=========

Create
------

URL: ``.../short/create``

Method ``POST``

Parameters
~~~~~~~~~~

* ``url``: URL to shorten.
* ``email``: Email address to send a message to (optional).
* ``message``: The user message to add in the email (optional).
* ``callback``: Function name to do the callback (optional, deprecated in v2).

Result
~~~~~~

.. code:: json

    {
        "short_url": <the short URL>
    }

Get
---

URL: ``short/<ref>``

Result: code: 302, redirect to the original URL.


Echo
====

This service returns a file containing data submitted in the POST request as the "file" field.
This is used to be able to get the data in the client from a file select by the user.

URL: ``.../echo``

Result
------

The 'Content-Type' header is 'text/html', and the data is:

.. code:: json

    {
        "filename": <The base64 encoded file>
        "success": true
    }


Export CSV
==========

This service returns a file containing data submitted in the POST request as the "csv" field.
This is used to be able to get as a download file csv data build on the client.

URL: ``.../csv``

Parameters
----------

* ``csv_extension``: File extension, default to 'csv'.
* ``csv_encoding``: Character encoding, default to 'UTF-8',
* ``name``: File name without extension set in the 'Content-Disposition', default to 'export'.

Result
------

The 'Content-Type' header is 'text/csv',
and the data contains the given 'csv' data.

Geometry processing
===================

This service provides geometry processing (currently only one)

Difference
----------

URL: ``.../difference``

Method: ``POST``

Data:

.. code:: json

   {
       "geometries": [<geomA>, <geomB>]
   }

Where ``<geomA>`` is a GeoJSON geometry to extrude,
and the ``<geomB>`` is the geometry used to do the extrude.

Result: the new ``GeoJSON`` geometry.
