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

.. code::

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

.. code::

   {
        "url": "<wms server url>",
        "urlWfs": "<wfs server url>",
        "wfsSupport": (true|false),
        "imageType": "image/(jpeg|png)",
        "isSingleTile": (true|false),
        "type": "(mapserver|geoserver|qgisserver|arcgis|other)",
        "credential: (true|false),"
        "attributes": {
            "<type name>": {
                "<attribute name>": {
                    "type": "<the type name>",
                    "namespace": "<the namespace URL>",
                    "alias": "<the optional alias>",
                    "minOccurs": "<the optional minimum occurs>",
                    "maxOccurs": "<the optional maximum occurs>"
                }
            }
        }
    }


Theme
~~~~~

.. code::

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

.. code::

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

.. code::

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

.. code::

   {
       "functionality": {
           "<functionality_name>": ["functionality_value"],
           ...
       },
       "two_factor_enable": true/false, # Is the two-factor authentication enabled?
       "is_intranet": true/false
   }

.. _developer_webservices_auth_connected:

Connected JSON result
~~~~~~~~~~~~~~~~~~~~~

.. code::

   {
       "username": "<username>",
       "is_intranet": true/true,
       "two_factor_enable": true/false, # Is the two-factor authentication enabled?
       "roles": [{
           "name": "<role_name>",
           "id": <role_id>
       }, ...],
       "functionality": {
           "<functionality_name>": ["functionality_value"],
           ...
       }
   }

User login
----------

Login to the application.

URL: ``.../login``

Parameters (post form):

* ``login``
* ``password``
* ``otp``: The second factor code

Result HTTP code:

* 200 Success: Success.
* 302 Found: Success with providing ``came_from`` parameter.
* 400 Bad request: When ``login`` or ``password`` is missing.
* 401 Unauthorized: On login failed.


Login successful
~~~~~~~~~~~~~~~~


Init without two-factor authentication JSON result
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code::

   {
       "username": "<username>",
       "is_password_changed": false, # Always false
       "two_factor_enable": false # Always false
   }


Init two-factor authentication JSON result
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code::

   {
       "username": "<username>",
       "two_factor_totp_secret": "<secret>", # The two-factor authentication secret on first login
       "otp_uri": "The OTM URI"
       "is_password_changed": false, # Always false
       "two_factor_enable": true # Always true
   }

Change password
---------------

Used to change the user password.

URL: ``.../loginchangepassword``

Method: ``POST``

Parameters (post form):

* ``login``
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
       "success": true
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
       "success": true
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
* ``ranksystem``: Can be set to ``ts_rank_cd`` to use the ``ts_rank_cd`` rank system instead of ``similarity``.

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

.. code::

    {
        "items": [{
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

.. code::

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
* ``layers``: On which layers; default is all.
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

.. code::

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

.. code::

   {
       "geometries": [<geomA>, <geomB>]
   }

Where ``<geomA>`` is a GeoJSON geometry to extrude,
and the ``<geomB>`` is the geometry used to do the extrude.

Result: the new ``GeoJSON`` geometry.


Localization pot
================

This service create and returns the list of strings to translate for the localization in gettext POT format.

URL: ``.../locale.pot``

Method: ``GET``

Parameters
----------

 - ``interfaces``: List of interfaces we want to use.
 - ``theme_regex``: Regular expression used to filter the themes.
 - ``group_regex``: Regular expression used to filter the layer groups.
 - ``wmslayer_regex``: Regular expression used to filter the WMS layers.
 - ``wmtslayer_regex``: Regular expression used to filter the WMTS layers.
 - ``ignore_i18n_errors``: ``TRUE`` to ignore most of the error expected during the extraction.
