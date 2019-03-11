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
you should define two ``OGC servers``. Attributes:

* ``Name``: the name of the OGC Server.
* ``Description``: a description.
* ``URL``: the server URL, empty to use the internal MapServer.
* ``WFS support``: whether WFS is supported by the server.
* ``WFS URL``: the WFS server URL, empty to use the same as the ``URL``.
* ``Type``: the server type used to know which custom attribute will be used.
* ``Image type``: the MIME type of the images (e.g.: ``image/png``).
* ``Single tile``: whether to use the single tile mode (For future use).
* ``Auth``: the kind of authentication to use (For future use).

.. _administrator_administrate_metadata:

Metadata
--------

You can associate metadata to all theme elements (tree items).
The purpose of this metadata is to trigger specific features, mainly UI features.
Each metadata entry has the following attributes:

* ``Item``: the tree item the metadata is associated to.
* ``Name``: the type of ``Metadata`` we want to set (the available names are configured in the ``vars``
  files in ``admin_interface/available_metadata``).
* ``Value``: the value of the metadata entry.
* ``Description``: a description.

To set a metadata entry, create or edit an entry in the Metadata view of the administration UI.
Regarding effect on the referenced tree item on the client side, you will find a description for each sort of metadata in the `NGEO documentation <https://camptocamp.github.io/ngeo/master/apidoc/gmfThemes.GmfMetaData.html>`_.

Functionalities
---------------

``Roles`` and ``Themes`` can have some functionalities. Attributes:

* ``Name``: the type of Metadata we want to set (configured in the ``vars``
  files in ``admin_interface/available_functionalities``).
* ``Value``: the value of the metadata.
* ``Description``: a description.

.. _administrator_administrate_layers:

Layers
------

Layer definition for the ngeo client is considered "version 2",
whereas layer definition for the CGXP client is considered "version 1".
In version 2, we split the layer table into 2 tables: ``layer_wms``,
``layer_wmts``, and we copy the previous layer table in ``layerv1``.
For information on migrating layers from CGXP to ngeo, see
:ref:`integrator_upgrade_application_cgxp_to_ngeo`.

Still using the CGXP client? Then you should maintain both version
of the layers, respectively ``layerv1`` and ``layer_wms``-``layer_wmts``.

And the ``order`` will be moved in the relation of the tree.

All layer type
~~~~~~~~~~~~~~

All the layers in the admin interface have the following attributes:

* ``Name``: the name of the WMS layer/group, or the WMTS layer.
  It is also used by OpenLayers.i18n, to display the name on the layers tree.
* ``Public``: make the layer public, also it is accessible
  through the ``Restriction areas``.
* ``Restrictions area``: the areas through which the user can see the layer.
* ``Related Postgres table``: the related postgres table,
  used by the :ref:`administrator_editing`.
* ``Exclude properties``: the list of attributes (database columns) that should not appear in
  the :ref:`administrator_editing` so that they cannot be modified by the end user.
  For enumerable attributes (foreign key), the column name should end with '_id'.
* ``Parents``: the groups and theme in which the layer is.
* ``Metadata``: Additional metadata.
* ``Dimensions``: the dimensions, if not provided default values are used (v2 only).

WMS layer
~~~~~~~~~
On internal WMS layers we have the following specific attributes:

* ``OGC Server``: the used server.
* ``Layers``: the WMS layers. Can be one layer, one group, a comma separated list of layers.
  In the case of a comma separated list of layers, we will get the legend rule for the
  layer icon on the first layer, and the legend will not be supported we should define a legend metadata.
* ``Style``: the style used, can be empty.
* ``Time mode``: used for the WMS time component.
* ``Time widget``: the component type used for the WMS time.

WMTS layer
~~~~~~~~~~

On WMTS layers we have the following specific attributes:

* ``GetCapabilities URL``: the URL to the WMTS capabilities.
* ``Layer``: the WMTS layer.
* ``Style``: the style used; if not present, we use the default style.
* ``Matrix set``: the matrix set used; if there is only one matrix set
  in the capabilities, it can be empty.

layerv1 (deprecated in v2)
~~~~~~~~~~~~~~~~~~~~~~~~~~

The layers in the admin interface have the following attributes:

* ``Metadata URL``: optional, for WMS, leave it empty to get it from the capabilities.
* ``Visible``: if it is false the layer is just ignored.
* ``Checked``: the layer is checked by default.
* ``Icon``: icon on the layer tree.
* ``KML 3D``: optional, URL to a KML to display it on the Google earth view.
* ``Display legend``: if checked, the legend is displayed on the layer tree.
* ``Legend image``: URL to overwrite the default legend image.
* ``Min/Max resolution``: resolutions between which data are displayed by
  the given layer, used to zoom to visible scale, with WMS if it is empty
  we get the values from the capabilities.
* ``Disclaimer``: optional, copyright of the layer.
* ``Identifier attribute field``: field used to identify a feature from the layer, e.g.: 'name'.
* ``Restrictions area``: the areas through which the user can see the layer.

On ``internal WMS`` layers, we have the following specific attributes:

* ``Image type``: the type of the images.
* ``Style``: the style used, can be empty.
* ``Dimensions``: a JSON string that gives the dimensions,
  e.g.: ``{ "YEAR": "2012" }``, if not provided default values are used.
* ``Legend rule``: the legend rule used to get the layer icon,
  if empty we use the ``Icon``.

On ``external WMS`` layers, we have the following specific attributes:

* ``Base URL``: the base URL of the WMS server.
* ``Image type``: the type of the images.
* ``Style``: the style used, can be empty.
* ``Legend rule``: the legend rule used to get the layer icon,
  if empty we use the ``Icon``.
* ``Single tile``: use the single tile mode.

On ``WMTS`` layers, we have the following specific attributes:

* ``Base URL``: the URL to the WMTS capabilities.
* ``Style``: the style used;, if not present, we use the default style.
* ``Matrix set``: the matrix set used; if there is only one matrix set
  in the capabilities, it can be empty.
* ``WMS server URL``: optional, URL to a WMS server to use for printing
  and querying. The URL to the internal WMS is used if this field is not
  specified.
* ``Query layers``: optional, a comma-separated list of WMS layers
  used for querying.
* ``WMS layers``: optional, a comma-separated list of layers used for
  printing, and for querying if ``Query layers`` is not set.

.. note::

    You can use both ``WMS layers`` and ``Query layers`` if you want that
    different sets of ``WMS layers`` are used for printing and querying.
    If you want to define ``WMS layers`` but no ``Query layers``,
    set it to ``[]``.

Queryable WMTS
~~~~~~~~~~~~~~
To make the WMTS queryable, you should add the following ``Metadata``:

* ``ogcServer`` with the name of the used ``OGC server``,
* ``wmsLayers`` or ``queryLayers`` with the layers to query (groups not supported).

It is possible to give some scale limits for the queryable layers by setting
a ``minResolution`` and/or a ``maxResolution Metadata`` value(s) for the
WMTS layer. These values correspond to the WMTS layer resolution(s) which should
be the zoom limit.

Print WMTS in high quality
~~~~~~~~~~~~~~~~~~~~~~~~~~
To print the layers in high quality, you should add the following ``Metadata``:

* ``ogcServer`` with the name of the used ``OGC server``,
* ``wmsLayers`` or ``printLayers`` with the layers to print.

.. note::

   See also: :ref:`administrator_administrate_metadata`, :ref:`administrator_administrate_ogc_server`.


LayerGroup
----------

Attributes:

* ``Name``: used by OpenLayers.i18n to display the name on the layer tree.
* ``Order``: used to order the layers and groups on the layer tree.
* ``Metadata URL``: optional (deprecated in v2).
* ``Expanded``: is expanded on the layer tree by default (deprecated in v2).
* ``Internal WMS``: if true it can include only ``Internal WMS`` layers,
  if false it can include only ``external WMS`` or ``WMTS`` layers (deprecated in v2).
* ``Group of base layers``: if not ``Internal WMS`` replace radio button by check box (deprecated in v2).

Background layers
-----------------

The background layers are configured in the database, with the layer group named
**background** (by default).
