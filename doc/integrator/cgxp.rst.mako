.. _integrator_cgxp:

CGXP
====

Organisation
------------

The main page where we can redefine the header
is in the file: ``<package>/templates/index.html``.

The viewer (map and all related tools)
is define in the file: ``<package>/templates/viewer.js``.

The sample for the API is in the file:
``<package>/templates/apiviewer.js``.

The style sheet file is: ``<package>/static/css/proj.css``

And finally the image should be placed in the folder:
``<package>/static/images/``


Viewer.js
---------

The ``viewer.js`` template is used to configure the client application.
It creates a
`gxp.Viewer <http://gxp.opengeo.org/master/doc/lib/widgets/Viewer.html>`_
object (``app = new gxp.Viewer({ ... });``) defining the application's UI.
The Viewer config includes three important sections:

``portalConfig``
~~~~~~~~~~~~~~~~

The portal configuration assembles Ext components (containers really),
to describe the application layout.

``tools``
~~~~~~~~~

Most of the tools used in the application are
`cgxp.plugins <http://docs.camptocamp.net/cgxp/${main_version}/lib/plugins.html>`_.

In most cases code examples to add to the ``viewer.js`` file are available.
Don't forget to add the plugin files in your ``jsbuild/app.cfg`` file.
For example, to use the Legend panel, add::

    [app.js]
    ...
    include =
        ...
        CGXP/plugins/Legend.js

``map``
~~~~~~~

See ``map`` section from
`gxp.Viewer documentation <http://gxp.opengeo.org/master/doc/lib/widgets/Viewer.html>`_

``layers``
~~~~~~~~~~

In the ``layers`` section we configure the background layers like this:

.. code-block:: javascript

            {
                source: "olsource",
                type: "OpenLayers.Layer.WMTS",
                group: 'background',
                args: [Ext.applyIf({
                    name: OpenLayers.i18n('plan'),
                    mapserverLayers: 'plan',
                    queryLayers: [{
                        name: 'query_plan',
                        identifierAttribute: 'name',
                        minScaleDenominator: 100,
                        maxScaleDenominator: 1000
                    }],
                    mapserverParams: {'EXTERNAL': true},
                    ref: 'plan',
                    layer: 'plan',
                    group: 'background'
                }, WMTS_OPTIONS)]
            },

with ``WMTS_OPTIONS`` defined like this:

.. code-block:: javascript

    var WMTS_OPTIONS = {
        url: '${'$'}{tile_url}',
        displayInLayerSwitcher: false,
        transitionEffect: 'resize',
        visibility: false,
        requestEncoding: 'REST',
        buffer: 0,
        style: 'default',
        dimensions: ['TIME'],
        params: {
            'time': '2011'
        },
        matrixSet: 'swissgrid',
        maxExtent: new OpenLayers.Bounds(420000, 30000, 900000, 350000),
        projection: new OpenLayers.Projection("EPSG:21781"),
        units: "m",
        formatSuffix: 'png',
        serverResolutions: [250,100,50,20,10,5,2.5,2,1.5,1,0.5,0.25,0.1]
    };

The important points are:

* Booth ``group: 'background'`` are requires by
  `GXP <http://gxp.opengeo.org>`_ (first), and by the
  `MapOpacitySlider <http://docs.camptocamp.net/cgxp/${main_version}/lib/plugins/MapOpacitySlider.html>`_
  (in ``args``).
* ``mapserverLayers`` is used to know the layers to
  `print <http://docs.camptocamp.net/cgxp/${main_version}/lib/plugins/Print.html>`_.
  if it's not present the tiles are used.
* ``queryLayers`` provide information to the
  `GetFeature <http://docs.camptocamp.net/cgxp/${main_version}/lib/plugins/GetFeature.html>`_
  plugin on the background layers. It can also be a coma separated string.
  If it's not present the ``mapserverLayers`` is used.
* ``ref`` is used by the
  `MapOpacitySlider <http://docs.camptocamp.net/cgxp/${main_version}/lib/plugins/MapOpacitySlider.html>`_.
* ``visibility`` should be set to ``false`` to don't download unneeded tiles, the
  `MapOpacitySlider <http://docs.camptocamp.net/cgxp/${main_version}/lib/plugins/MapOpacitySlider.html>`_
  will manage it.
* ``transitionEffect``, ``buffer`` provides good value for performance
  and user experience.

``linked base layers``
......................

It is possible to link a base layer with one or more *detached* base layers.

A *detached* base layer is a base layer that is not listed in the ``MapOpacitySlider``
dropdown list. But this layer can be linked with a normal base layer and will be
displayed or hidden at the same time.

To do so:

* in the normal base layer, add the parameter ``linkedLayers`` with the list of
  *detached* base layers ``ref`` names.
* add the *detached* base layer like any other normal base layer, but with
  ``visibility: false`` and no ``group`` in ``args``

Example:

.. code-block:: javascript

            {
                source: "olsource",
                type: "OpenLayers.Layer.WMTS",
                group: 'background',
                args: [Ext.applyIf({
                  name: 'detached_base_layer_nice_name',
                  ref: 'detached_base_layer',
                  layer: 'detached_base_layer_source_name',
                  transitionEffect: "resize",
                  visibility: false
                }, WMTS_OPTIONS)]
            },
            {
                source: "olsource",
                type: "OpenLayers.Layer.WMTS",
                group: 'background',
                args: [Ext.applyIf({
                    name: OpenLayers.i18n('normal_base_layer'),
                    ref: 'normal_base_layer',
                    layer: 'normal_base_layer_source_name',
                    group: 'background',
                    linkedLayers: ['detached_base_layer']
                }, WMTS_OPTIONS)]
            },
