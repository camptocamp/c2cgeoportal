.. _administrator_administrate:

Administrate a c2cgeoportal application
=======================================

The administration interface is located at « http://<server>/<project>/wsgi/admin ».

Authentication for the administration interface is done through the main application interface. Role ``role_admin`` is
required.

*To Be Done*

Layer
-----

The layers in the admin interface has the following attributes:
 *  ``Name``: the name of the WMS layer/group, or he WMTS layer. 
    It also used throw OpenLayers.i18n to display the name on the layers tree.
 *  ``Order``: used to order the layers and group on the layer tree.
 *  ``Metadata URL``: optional, with WMTS if it's empty it will 
    be get throw the capabilities.
 *  ``Public``: make the layer public, also it is accessible 
    throw the ``Restriction areas``.
 *  ``Visible``: if it's false the layer is just ignored.
 *  ``Checked``: the layer is checked by default.
 *  ``Icon``: icon on the layer tree.
 *  ``KML 3D``: optional, URL to a KML to display it on the Google earth view.
 *  ``Display legend``: it checked the legend is display on the layer tree.
 *  ``Legend image``: URL to overwrite the default legend image.
 *  ``Min/Max resolution``: resolution where the layers has some data, 
    used to zoom to visible scale, with WMS if it's empty we gets the values 
    from the capabilities.
 *  ``Disclaimer``: optional, copyright of the layer, used by 
    `Disclaimer <http://docs.camptocamp.net/cgxp/lib/plugins/Disclaimer.html>`_.
 *  ``Identifier attribute field``: field used to identify a feature from the 
    layer, eg: 'name', used by 
    `FeaturesWindow <http://docs.camptocamp.net/cgxp/lib/plugins/FeaturesWindow.html>`_.
 *  ``Related Postgres table``: the related postgres table, 
    used by the :ref:`administrator_editing`.
 *  ``Restrictions area``: the areas throw witch the user can see the layer.
 *  ``Parents``: the groups and theme in witch the layer is.

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
 *  ``Dimensions``: a json string that gives the dimensions, 
    eg: ``{ "YEAR": "2012" }``, if not provide use default values.
 *  ``Matrix set``: the used matix set, if there only one matrix set 
    in the capabilities it can be empty.
 *  ``WMS server URL``: optional, URL to a WMS server to do 
    the interrogation and the print.
 *  ``WMS layers``: optional, a coma separated list of layers used foforr
    the interrogation and the print.

LayerGroup
----------

 *  ``Name``: used throw OpenLayers.i18n to display the name on the layers tree.
 *  ``Order``: used to order the layers and group on the layer tree.
 *  ``Metadata URL``: optional.
 *  ``Expanded``: is expanded on the layer tree by default.
 *  ``Internal WMS``: if true it can include only ``Internal WMS`` layers, 
    if false it can include only ``external WMS`` or ``WMTS`` layers.
 *  ``Group of base layers``: if not ``Internal WMS`` replace radio button by check box.

Add users
---------
