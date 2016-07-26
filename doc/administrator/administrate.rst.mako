.. _administrator_administrate:

Administrate a c2cgeoportal application
=======================================

The administration interface is located at ``http://<server>/<project>/admin``.

Authentication for the administration interface is done through the main application interface. Role ``role_admin`` is
required.

.. _administrator_administrate_ogc_server:

OGC Server
----------

This is the description of an OGC server (WMS/WFS).
For one server we try to create only one request when it is possible.

If you want to query the same server to get PNG and JPEG images,
you should define two OGC servers. Attributes:

* ``Name``: the name of the OGC Server.
* ``Description``: a description.
* ``URL``: the server URL, empty to use the internal mapserver.
* ``WFS support``: whether WFS is supported by the server.
* ``WFS URL``: the WFS server URL, empty to use the same as the ``URL``.
* ``Type``: the server type used to know which custom attribute will be used.
* ``Image type``: the MIME type of the images (e.g.: ``image/png``).
* ``Single tile``: whether to use the single tile mode (For future use).
* ``Auth``: the kind of authentication to use (For future use).

.. _administrator_administrate_metadata:

UI Metadata
-----------

All the Theme elements can have some Metadata to trigger some features,
mainly UI features. Attributes:

* ``Item``: the concerned tree item.
* ``Name``: the type of Metadata we want to set (configured in the ``vars``
  files in ``admin_interface/available_metadata``).
* ``Value``: the value of the metadata.
* ``Descritpion``: a description.

Functionalities
---------------

Roles and Themes can have some functionalities. Attributes:

* ``Name``: the type of Metadata we want to set (configured in the ``vars``
  files in ``admin_interface/available_functionalities``).
* ``Value``: the value of the metadata.
* ``Descritpion``: a description.

Layers
------

In the version 2 we split the layer table in 2 tables: ``layer_wms``,
``layer_wmts``, and we copy the previous layer table in ``layerv1``.
There is a tool for migrate the layer from the v1 structure to v2,
see ``.build/venv/bin/themev1tov2``.
The ``layerv1`` steal be used in the cgxp application then you should
maintain the booth version of the layers.

And the ``order`` will be moved in the relation of the tree.

All layer type
~~~~~~~~~~~~~~

All the layers in the admin interface have the following attributes:
 *  ``Name``: the name of the WMS layer/group, or the WMTS layer.
    It also used throw OpenLayers.i18n to display the name on the layers tree.
 *  ``Public``: make the layer public, also it is accessible
    throw the ``Restriction areas``.
 *  ``Restrictions area``: the areas through which the user can see the layer.
 *  ``Related Postgres table``: the related postgres table,
    used by the :ref:`administrator_editing`.
 *  ``Exclude properties``: the list of attributes (database columns) that shouldn't appear in
    the :ref:`administrator_editing` so that they cannot be modified by the end user.
    For enumerable attributes (foreign key), the column name should end with '_id'.
 *  ``Parents``: the groups and theme in which the layer is.
 *  ``UI Metadata``: Additional metadata used by the UI.

Internal WMS layer
~~~~~~~~~~~~~~~~~~
On internal WMS layers we have the following specific attributes:
 *  ``Layers``: the WMS layers.
 *  ``Image type``: the MIME type of the images (e.g.: 'image/png').
 *  ``Style``: the used style, can be empty.
 *  ``Time mode``: used for the WMS time slider.

External WMS layer
~~~~~~~~~~~~~~~~~~
On external WMS layers we have the following specific attributes:
 *  ``Layers``: the WMS layers.
 *  ``Base URL``: the base URL of the WMS server.
 *  ``Image type``: the MIME type of the images (e.g.: 'image/png').
 *  ``Style``: the used style, can be empty.
 *  ``Single tile``: use the single tile mode.
 *  ``Time mode``: used for the WMS time slider.

WMTS layer
~~~~~~~~~~
On WMTS layers we have the following specific attributes:
 *  ``GetCapabilities URL``: the URL to the WMTS capabilities.
 *  ``Layer``: the WMTS layer.
 *  ``Style``: the used style, if not present we use the default style.
 *  ``Matrix set``: the used matrix set, if there's only one matrix set
    in the capabilities it can be empty.
 *  ``WMTS Dimensions``: the dimensions, if not provided default values are used.

layerv1
~~~~~~~

The layers in the admin interface have the following attributes:
 *  ``Metadata URL``: optional, for WMS, leave it empty to get it from the capabilities.
 *  ``Visible``: if it is false the layer is just ignored.
 *  ``Checked``: the layer is checked by default.
 *  ``Icon``: icon on the layer tree.
 *  ``KML 3D``: optional, URL to a KML to display it on the Google earth view.
 *  ``Display legend``: it checked the legend is display on the layer tree.
 *  ``Legend image``: URL to overwrite the default legend image.
 *  ``Min/Max resolution``: resolutions between which data are displayed by
    the given layer, used to zoom to visible scale, with WMS if it is empty
    we get the values from the capabilities.
 *  ``Disclaimer``: optional, copyright of the layer, used by
    `Disclaimer <http://docs.camptocamp.net/cgxp/${main_version}/lib/plugins/Disclaimer.html>`_.
 *  ``Identifier attribute field``: field used to identify a feature from the
    layer, e.g.: 'name', used by
    `FeaturesWindow <http://docs.camptocamp.net/cgxp/${main_version}/lib/plugins/FeaturesWindow.html>`_.
 *  ``Restrictions area``: the areas throw witch the user can see the layer.

On ``internal WMS`` layer we have the following specific attributes:
 *  ``Image type``: the type of the images.
 *  ``Style``: the used style, can be empty.
 *  ``Legend rule``: the legend rule used to get the layer icon,
    if empty we use the ``Icon``.

On ``external WMS`` layer we have the following specific attributes:
 *  ``Base URL``: the base URL of the WMS server.
 *  ``Image type``: the type of the images.
 *  ``Style``: the used style, can be empty.
 *  ``Legend rule``: the legend rule used to get the layer icon,
    if empty we use the ``Icon``.
 *  ``Single tile``: use the single tile mode.

On ``WMTS`` layer we have the following specific attributes:
 *  ``Base URL``: the URL to the WMTS capabilities.
 *  ``Style``: the used style, if not present we use the default style.
 *  ``Dimensions``: a JSON string that gives the dimensions,
    e.g.: ``{ "YEAR": "2012" }``, if not provided default values are used.
 *  ``Matrix set``: the used matrix set, if there's only one matrix set
    in the capabilities it can be empty.
 *  ``WMS server URL``: optional, URL to a WMS server to use for printing
    and querying. The URL to the internal WMS is used if this field is not
    specified.
 *  ``Query layers``: optional, a comma-separated list of WMS layers
    used for querying.
 *  ``WMS layers``: optional, a comma-separated list of layers used for
    printing, and for querying if ``Query layers`` is not set.

.. note::
    You can use both ``WMS layers`` and ``Query layers`` if you want that
    different sets of WMS layers are used for printing and querying.
    If you want to define ``WMS layers`` but no ``Query layers``,
    set it to ``[]``.

LayerGroup
----------

 *  ``Name``: used throw OpenLayers.i18n to display the name on the layers tree.
 *  ``Order``: used to order the layers and group on the layer tree.
 *  ``Metadata URL``: optional.
 *  ``Expanded``: is expanded on the layer tree by default (deprecated in v2).
 *  ``Internal WMS``: if true it can include only ``Internal WMS`` layers,
    if false it can include only ``external WMS`` or ``WMTS`` layers.
 *  ``Group of base layers``: if not ``Internal WMS`` replace radio button by check box (deprecated in v2).

URL
---

In the admin interface we can use in all the URL the following special schema:

* ``static``: to use a static route,

  * ``static:///icon.png`` will get the URL of the ``static`` static route of the project.
  * ``static://c2cgeoportal/icon.png`` will get the URL of the ``static`` static route of ``c2cgeoportal``.
  * ``static://prj:img/icon.png`` will get the URL of the ``img`` static route of ``prj``.

* ``config``: to get the server name from the URL, with the config from the ``vars`` file:

  .. code:: yaml

     servers:
        my_server: http://example.com/test

  ``config://my_server/icon.png`` will be transformed into
  the URL ``http://example.com/test/icon.png``.
