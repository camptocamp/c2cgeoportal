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
* ``Basis URL``: the server URL.
* ``WFS URL``: the WFS server URL. If empty, the ``Basis URL`` is used.
* ``Server type``: the server type which is used to know which custom attribute will be used.
* ``Image type``: the MIME type of the images (e.g.: ``image/png``).
* ``Authentication type``: the kind of authentication to use.
* ``WFS support``: whether WFS is supported by the server.
* ``Single tile``: whether to use the single tile mode (For future use).

.. _administrator_administrate_metadata:

Metadata
--------

You can associate metadata to all theme elements (tree items).
The purpose of this metadata is to trigger specific features, mainly UI features.
Each metadata entry has the following attributes:

* ``Name``: the type of ``Metadata`` we want to set (the available names are configured in the ``vars``
  files in ``admin_interface/available_metadata``).
* ``Value``: the value of the metadata entry.
* ``Description``: a description.

To set a metadata entry, create or edit an entry in the Metadata view of the administration UI.
Regarding effect on the referenced tree item on the client side, you will find a description for each sort
of metadata in the `NGEO documentation
<https://camptocamp.github.io/ngeo/master/apidoc/gmfThemes.GmfMetaData.html>`_.

.. TODO: the URL should be fixed when the ngeo documentation will be generated.

Functionalities
---------------

``Roles`` and ``Themes`` can have some functionalities. Attributes:

* ``Name``: the type of functionality we want to set (configured in the ``vars``
  files in ``admin_interface/available_functionalities``).
* ``Description``: a description.
* ``Value``: the value of the functionality.

.. _administrator_administrate_layers:

Layers
------

Layer definitions are found in to two tables: ``layer_wms`` and ``layer_wmts``.
The legacy table ``layerv1`` is still present, but only for being able to migration the application,
for information on migrating layers, see :ref:`integrator_upgrade_application_cgxp_to_ngeo`.

All layer type
~~~~~~~~~~~~~~

All the layers in the admin interface have the following attributes:

* ``Name``: the name of the WMS layer/group, or the WMTS layer.
  It is used through the i18n tools to display the name on the layers tree.
* ``Metadata URL``: (deprecated)
* ``Description``: a description.
* ``Public``: makes the layer public. You must use the ``Restriction areas`` to make
  private layer accessible.
* ``Geo table``: the related database table,
  used by the :ref:`administrator_editing`.
* ``Exclude properties``: the list of attributes (database columns) that should not appear in
  the :ref:`administrator_editing` so that they cannot be modified by the end user.
  For enumerable attributes (foreign key), the column name should end with '_id'.
* ``Interfaces``: visible in the checked interfaces.
* ``Restriction areas``: the areas through which the user can see the layer.
* ``Metadata``: Additional metadata.
* ``Dimensions``: the dimensions, if not provided default values are used.

WMS layer
~~~~~~~~~
On internal WMS layers we have the following specific attributes:

* ``OGC Server``: the used server.
* ``WMS layer name``: the WMS layers. Can be one layer, one group, a comma separated list of layers.
  In the case of a coma separated list of layers, we will get the legend rule for the
  layer icon on the first layer, and the legend will not be supported we should define a legend metadata.
* ``Style``: the used style, can be empty.
* ``Time mode``: used for the WMS time component.
* ``Time widget``: the used component type for the WMS time.

WMTS layer
~~~~~~~~~~

On WMTS layers we have the following specific attributes:

* ``GetCapabilities URL``: the URL to the WMTS capabilities.
* ``WMTS layer name``: the WMTS layer.
* ``Style``: the used style, if not present we use the default style.
* ``Matrix set``: the used matrix set, if there is only one matrix set
  in the capabilities it can be empty.
* ``Image type``: the MIME type of the images (e.g.: ``image/png``).

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
To print the layers in high quality, you can define that the image shall be retrieved with a
``GetMap`` on the original WMS server.
To activate this, you should add the following ``Metadata``:

* ``ogcServer`` with the name of the used ``OGC server``,
* ``wmsLayers`` or ``printLayers`` with the layers to print.

.. note::

   See also: :ref:`administrator_administrate_metadata`, :ref:`administrator_administrate_ogc_server`.

LayerGroup
----------

Attributes:

* ``Name``: It is used through the i18n tools to display the name on the layers tree.
* ``Metadata URL``: (deprecated).
* ``Description``: a description.
* ``Expanded``: (deprecated).
* ``Children``: the ordered children elements.
* ``Metadata``: Additional metadata.

Background layers
-----------------

The background layers are configured in the database, with the layer group named
**background** (by default).

Theme
-----

* ``Name``: It is used through the i18n tools to display the name on the layers tree.
* ``Metadata URL``: (deprecated).
* ``Description``: a description.
* ``Public``: makes the layer public. You must use the ``Restriction Roles`` to make
  private theme accessible.
* ``Icon``: the icon URL.
* ``Interfaces``: visible in the checked interfaces.
* ``Restricted Roles``: Restricted to the following roles.
* ``Functionalities``: The linked functionalities.
* ``Children``: the ordered children elements.
* ``Metadata``: Additional metadata.

Restricted area
---------------

A restricted area is an area for which a user must possess a specific role in order to be able
to see (and edit, if applicable) the features within this area.

* ``Name``: a name.
* ``Description``: a description.
* ``Roles``: Restricted to the following roles.
* ``Read/write``: Allows the linked users to change the objects.
* ``Area``: Active in the following area, if not defined it is active everywhere.
