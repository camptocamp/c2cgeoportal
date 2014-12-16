.. _developer_webservices:

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
