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
* ``sets``: kind of data we want to get, can be ``all``, ``themes``, ``group``
  or ``background_layers``, default is ``all``.
* ``background``: parent group of background layers to get.
* ``group``: the group to get.
* ``catalog``: ``true`` or ``false``, different error reporting for catalog mode, default is ``false``.
* ``min_levels``: minimum number of group levels that's required, default is ``1``.
* ``role``: role name, not used by the server but it's required for the cache management.


Result in v2
------------

Base for all possible results:

.. code:: json

    {
        themes: [<themes>],
        group: <group>,
        background_layers: [<layers>],
        errors: [<errors>]
    }


Theme:

.. code:: json

    {
        "name": <name>,
        "icon": <icon_url>,
        "functionalities": {
            <name>: <values>
        },
        "ui_metadata": {
            <name>: <value>
        },
        "children": [<items>]
    }


Group:

.. code:: json

    {
        "name": <name>,
        "ui_metadata": {
            <name>: <value>
        },
        "children": [<items>]
    }


Layer:

.. code:: json

    {
        "name": <name>,
        "type": "internal WMS/external WMS/WMTS",
        "ui_metadata": {
            <name>: <value>
        }
    }


Internal WMS Layer:

.. code:: json

    {
        "layer": <wms_layers>,
        "image_type": "image/png",
        "style": <style>,
        "queryable": 0/1,
        "minResolutionHint": <minResolutionHint>,
        "maxResolutionHint": <maxResolutionHint>,
        "metadataUrls": {
            "url": <url>,
            "type": "TC211/FGDC",
            "format": "text/html"
        },
        "time": {
            "mode": "value/range",
            "interval": [year, mounth, day, secound],
            "resolution": "year/mounth/day/secound",
            "minValue": <minValue>,
            "maxValue": <maxValue>
        },
        "childLayers": [{
            "name": <name>,
            "queryable": 0/1,
            "minResolutionHint": <minResolutionHint>,
            "maxResolutionHint": <maxResolutionHint>
        }]
    }


External WMS Layer:

.. code:: json

    {
        "url": <wms_server_url>,
        "layer": <wms_layers>,
        "image_type": "image/png",
        "style": <style>,
        "is_single_tile": true/false,
        "time": {
            "mode": "value/range",
            "interval": [year, mounth, day, secound],
            "resolution": "year/mounth/day/secound",
            "minValue": <minValue>,
            "maxValue": <maxValue>
        }
    }


WMTS layer:

.. code:: json

    {
        "url": <wmts_capabilities_url>,
        "layer": <wmts_layer>,
        "style": <style>,
        "matrix_set": <matrix_set>,
        "dimensions": {
            <name>: <value>
        }
    }


Authentication
==============

Login
-----

Used to login in the application.

URL: ``.../login``

Parameters (post form):

* ``login``
* ``password``
* ``came_from`` the URL where we will redirect after a success

Result HTTP code::

 * 200 Success: Success with the JSON result as :ref:_developer_webservices_auth_connected.
 * 302 Found: Success -> redirect on came_from.
 * 400 Bad request: Missing login or password.
 * 401 Unauthorised: Wrong login.

Logout
------

Used to log out of the application.

URL: ``.../logout``

Result HTTP code::

 * 200 Success: Success.
 * 404 Not Found: Not login.

User informations
-----------------

Used to get the user informations.

URL: ``.../loginuser``

Result HTTP code::

 * 200 Success: Success.

Annoymous JSON result
`````````````````````

.. code:: json

   {
       "functionality": {
           "<functionnality_name>": ["functionnality_value"],
           ...
       }
   }

.. _developer_webservices_auth_connected:

Connected JSON result
`````````````````````

.. code:: json

   {
       "userneme": "<username>",
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

Parameters (post form):

* ``newPassword``
* ``confirmNewPassword``

Result HTTP code::

 * 200 Success: Success.
 * 400 Bad request: Missing newPassword or confirmNewPassword or the booth password don't match.
 * 401 Unauthorised: Not login.

JSON result
```````````

.. code:: json

   {
       "success": "true"
   }


Generate a new password
-----------------------

Used when the user lost his password.

Parameters (post form):

* ``login``

Result HTTP code::

 * 200 Success: Success.

Success JSON result
```````````````````

.. code:: json

   {
       "success": "true"
   }

Failure JSON result
```````````````````
.. code:: json

   {
       "success": "false"
       "error": "<the error>"
   }


Full Text Search
================

URL: ``.../fulltextsearch``

Parameters
----------

* ``query``: Text to search.
* ``callback``: Name of the callback function.

Result
------

A GeoJSON of a feature collection with the properties:

* ``label``: Text to display.
* ``layer_name``: Layer to display.
* ``params``: :ref:`integrator_fulltext_search_params` to set.


Raster
======

URL: ``.../raster``

Parameters
----------

* ``lon``: The longitude.
* ``lat``: The latitude.
* ``layers``: The raster layers we want to query.
* ``callback``: Function name to do the callback.

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
* ``callback``: Function name to do the callback.

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
``````````

* ``url``: URL to shorten.
* ``email``: Email address to send a message to.
* ``callback``: Function name to do the callback.

Result
``````

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

* ``csv_extension``: File extension, defaults to 'csv'.
* ``csv_encoding``: Character encoding, defaults to 'UTF-8',
* ``name``: File name without extension set in the 'Content-Disposition', defaults to 'export'.

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
