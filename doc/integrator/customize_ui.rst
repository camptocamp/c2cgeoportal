.. _integrator_customize_ui:

Customize the UI
================

Interfaces
----------

The administration interface gives access to an ``interface`` table listing the
available interfaces (or pages) of the application.
The default interfaces are "main", "mobile", "edit" and "routing".

The interfaces are added by the following lines in ``<package>/__init__.py``:

.. code:: python

    add_interface(config)
    add_interface(config, 'edit')
    add_interface(config, 'routing')
    add_interface(config, 'mobile', INTERFACE_TYPE_SENCHA_TOUCH)


The used method has the following API:

``add_interface(config, interface_name=None, interface_type=INTERFACE_TYPE_CGXP, **kwargs)``:

``config`` is the application configuration object.

``interface_name`` is the name specified in the ``interface`` table,
also used to create the route path.

``interface_type`` may be either ``INTERFACE_TYPE_CGXP``,
``INTERFACE_TYPE_SENCHA_TOUCH``, ``INTERFACE_TYPE_NGEO`` or
``INTERFACE_TYPE_NGEO_CATALOGUE``. Constants available in ``c2cgeoportal``.


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
`cgxp.plugins <http://docs.camptocamp.net/cgxp/1.6/lib/plugins.html>`_.

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
        url: '${tile_url}',
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
  `MapOpacitySlider <http://docs.camptocamp.net/cgxp/1.6/lib/plugins/MapOpacitySlider.html>`_
  (in ``args``).
* ``mapserverLayers`` is used to know the layers to
  `print <http://docs.camptocamp.net/cgxp/1.6/lib/plugins/Print.html>`_.
  if it's not present the tiles are used.
* ``queryLayers`` provide information to the
  `GetFeature <http://docs.camptocamp.net/cgxp/1.6/lib/plugins/GetFeature.html>`_
  plugin on the background layers. It can also be a coma separated string.
  If it's not present the ``mapserverLayers`` is used.
* ``ref`` is used by the
  `MapOpacitySlider <http://docs.camptocamp.net/cgxp/1.6/lib/plugins/MapOpacitySlider.html>`_.
* ``visibility`` should be set to ``false`` to don't download unneeded tiles, the
  `MapOpacitySlider <http://docs.camptocamp.net/cgxp/1.6/lib/plugins/MapOpacitySlider.html>`_
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

Sub domain
----------

If you want to optimize the parallelization of static resource download you
can use sub domain to do that you should define in the ``vars_<project>.yaml``
something like this:

.. code:: yaml

    # The used sub domain for the static resources
    subdommains: ['s1', 's2', 's3', 's4']

Those sub domain should obviously be define in the DNS and in the Apache
vhost. If the application is served on deferent URL and you want to use
the sub domain on only one of them you can define in the ``vars_<project>.yaml``
the following:

.. code:: yaml

    # The URL template used to generate the sub domain URL
    # %(sub)s will be replaced by the sub domain value.
    subdomain_url_template: http://%(sub)s.{host}


Advanced configuration examples
-------------------------------

We can use the ``functionalities`` or the ``vars_<project>.yaml`` to configure the
interface. For instance:

Activate CGXP plugin using an ``authorized_plugins`` functionality:

.. code:: javascript

   % if 'my_plugin' in functionality['authorized_plugins']:
   {
       // plugin configuration
   },
   % endif


Configure the ``querier`` layer using the ``vars_<project>.yaml``,
Add in ``vars_<project>.yaml``:

.. code:: yaml

    viewer:
        feature_types:
        - layer_1
        - layer_2

Add in your project Makefile ``<package>.mk``:

.. code:: makefile

   CONFIG_VARS += viewer

And in ``viewer.js``:

.. code:: javascript

    <%
    from json import dumps
    %>
    % if len(request.registry.settings['viewer']['feature_types']) > 0:
    {
        ptype: "cgxp_querier",
        // plugin configuration
        featureTypes: ${dumps(request.registry.settings['viewer']['feature_types']) | n}
    },
    % endif
