.. _developer_webservices:

=========================
Webservices documentation
=========================


Theme webservice
================

URL: ``.../themes``

Parameters
----------

* ``version``: ``2``, API version, default is ``2``.
* ``interface``: used interface, default is ``desktop``.
* ``sets``: kind of data we want to get, can be ``all``, ``themes``, ``group``
  or ``background_layers``, default is ``all``.
* ``background``: parent group of background layers to get.
* ``group``: the group to get.
* ``min_levels``: minimum number of group levels that is required, default is ``1``.
* ``role``: role name, not used by the server but it is required for the cache management.

Requests examples:

* themes
* themes?background=background
* themes?group=Transport
* themes?group=Transport&sets=group

Result
------

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
        "serverType": "(mapserver|geoserver|qgisserver)",
        "minResolutionHint": <minResolutionHint>,
        "maxResolutionHint": <maxResolutionHint>,
        # end derecated
        "metadata": {
            "identifier_attribute_field": "<display_name>",
            "disclaimer": "<disclaimer>",
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
            "interval": [<year>, <month>, <day>, <second>],
            "resolution": "(year|month|day|second)",
            "minValue": <minValue>,
            "maxValue": <maxValue>
        },
        "childLayers": [{
            "name": "<name>",
            "queryable": (true|false),
            "minResolutionHint": <minResolutionHint>,
            "maxResolutionHint": <maxResolutionHint>
        }],
        "dimensionsFilters": {
            "<name>: {
               "field": "<field_name>",
               "value": "<value>"
            }
        },
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
* ``came_from`` the URL to which we will redirect after a successful request.

Result HTTP code:

* 200 Success: Success with the JSON result as :ref:`developer_webservices_auth_connected`.
* 302 Found: Success -> redirect to ``came_from``.
* 400 Bad request: When something is wrong.

Logout
------

Used to log out of the application.

URL: ``.../logout``

Method: ``GET``

Result HTTP code:

* 200 Success: Success.
* 400 Bad request: When something is wrong.

User information
----------------

Used to get the user information.

URL: ``.../loginuser``

Result HTTP code:

* 200 Success: Success.

Anonymous JSON result
~~~~~~~~~~~~~~~~~~~~~

.. code:: json

   {
       "functionality": {
           "<functionality_name>": ["functionality_value"],
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
       "roles": [{
           "name": "<role_name>",
           "id": <role_id>
       }, ...],
       "functionality": {
           "<functionality_name>": ["functionality_value"],
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
* 400 Bad request: When something is wrong.

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

Used when the user lost his/her password.

Parameters (post form):

* ``login``

Result HTTP code:

* 200 Success: Success.
* 400 Bad request: When something is wrong.

Success JSON result
~~~~~~~~~~~~~~~~~~~

.. code:: json

   {
       "success": "true"
   }

.. _developer_webservices_fts:

Full-text search
================

URL: ``.../fulltextsearch``

Parameters
----------

* ``query``: Text to search.
* ``limit``: The maximum number of results (optional).
* ``partitionlimit``: The maximum number of results per layer (optional).
* ``lang``: The language used (optional).
* ``interface``: The interface used (optional).

Result
------

A GeoJSON of a feature collection with the properties:

* ``label``: Text to display.
* ``layer_name``: Layer to display.
* ``params``: :ref:`integrator_fulltext_search_params` to set.
* ``actions``: List of actions.

The `actions` is a dictionary with:

* ``action``: the type of action (add_theme|add_group|add_layer).
* ``data``: data needed for the action (the item name).


Layers
======

Layer description
-----------------

URL: ``.../layers/<layer_id>/md.xsd``

Result
~~~~~~

A standard xsd document that describes the layer.

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
--------------

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
--------------

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

Result
------

.. code:: json

    {
        "<layer>": <value>,
        ...
    }


Digital Elevation Model
=======================

URL: ``.../profile.json``

Method ``POST``

Parameters
----------

* ``geom``: Geometry field used to get the profile data.
* ``layers``: On which layers; default to all.
* ``nbPoints``: Maximum number of points.

Result
------

A JSON file, with 'dist', 'value', 'x', 'y'.


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
