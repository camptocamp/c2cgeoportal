.. _developer_webservices:

=========================
Webservices documentation
=========================


Theme webservice
================

Parameters
----------

* ``version``: ``1`` or ``2 ``, API version, default is ``1``.
* ``group``: get only one group, used to get the base layers.
* ``catalog``: ``true`` or ``false``, different error reporting for catalog mode, default is ``false``.
* ``min_levels``: minimum number of group levels that's required, default is ``1``.
* ``role``: role name, not used by the server but it's required for the cache management.


Result in v2
------------

Main for themes:

.. code:: json

    {
        items: [<themes>],
        errors: [<errors>]
    }


Main for group:

.. code:: json

    {
        group: <group>,
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


Full Text Search
================


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


Digital Elevation Model
=======================

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

Parameters
----------

* ``url``: URL to shorten.
* ``email``: Email address to send a message to.
* ``callback``: Function name to do the callback.

Result
------

.. code:: json

    {
        "short_url": <the short URL>
    }


Echo
====

This service returns a file containing data submitted in the POST request as the "file" field.
This is used to be able to get the data in the client from a file select by the user.

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

Parameters
----------

* ``csv_extension``: File extension, defaults to 'csv'.
* ``csv_encoding``: Character encoding, defaults to 'UTF-8',
* ``name``: File name without extension set in the 'Content-Disposition', defaults to 'export'.

Result
------

The 'Content-Type' header is 'text/csv',
and the data contains the given 'csv' data.
