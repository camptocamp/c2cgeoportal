.. _integrator_cgxp:

CGXP
====

It still possible to have CGXP interface(s) in parallel of the ngeo interface(s).

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

Use the CGXP interface
----------------------

The special application named ``index.html``, ``viewer.js`` is no more possible then you should do::

    * Do the following renames:

      .. prompt:: bash

         git mv <package>/templates/index.html <package>/templates/desktop.html
         git mv <package>/templates/viewer.js <package>/templates/desktop.js

    * In the ``<package>/templates/desktop.html`` file do the following replacement:

        - <script type="text/javascript" src="${'$'}{request.static_url('<package>:static/build/app.js')}"></script>
        + <script type="text/javascript" src="${'$'}{request.static_url('<package>:static/build/desktop.js')}"></script>
        ...
        - <script type="text/javascript" src="${'$'}{request.route_url('viewer', _query=extra_params)}"></script>
        + <script type="text/javascript" src="${'$'}{request.route_url('desktop.js', _query=extra_params)}"></script>

    * In the ``jsbuild/app.cfg.mako`` file do the following replacement:

        - [app.js]
        + [desktop.js]

To configure the build of the interface you should use the ``CGXP_INTERFACES`` (and the ``NGEO_INTERFACES``)
in your project makefile, e.g.::

  .. code:: make

     CGXP_INTERFACES = desktop edit routing
     NGEO_INTERFACES = mobile

Enable the CGXP check, add in your project vars file::

  .. code::yaml::

     vars:
         ...
         checker:
            ...
            defaults:
                ...
                lang_files: [cgxp]
     update_paths:
     ...
     - checker.defaults.lang_files

Do not have ``check_collector.disabled`` in the ``update_paths`` (and do not readd it during
the next upgrade steps).

Update the interface in your ``<package>/__init__.py`` file:

.. code:: python

  add_interface(config, "<interface>", INTERFACE_TYPE_CGXP)


The OGC proxy is deprecated because with modern browser it is not required to have it.

Then you should remove it from the CGXP ``js`` interface files (``<package>/templates/<interface>.js``):

.. code:: diff

    - OpenLayers.ProxyHost = "${'$'}{request.route_url('ogcproxy') | n}?url=";

The ``externalWFSTypes`` do not exist anymore than you should remove the following line
from the CGXP ``js`` interface files (``<<package>/templates/<interface>.js``)

.. code:: diff

    - externalWFSTypes: ${'$'}{externalWFSTypes | n},

Back to the ngeo interface
--------------------------

Remove the CGXP interface:

.. prompt:: bash

  git rm <package>/templates/<interface>.html
  git rm <package>/templates/<interface>.js

Remove the related section in the ``jsbuild/app.cfg.mako`` file.

Update the interface in your ``<package>/__init__.py`` file
by removing the following line:

.. code:: python

  add_interface(config, "<interface>"[, INTERFACE_TYPE_CGXP])

To add an ngeo interface see :ref:`integrator_ngeo_add`.

If you remove all the cgxp interface, remove the ``vars.checker.defaults.lang_files`` from your
project vars file, and the ``checker.defaults.lang_files`` from your update_paths.

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
Do not forget to add the plugin files in your ``jsbuild/app.cfg`` file.
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
  if it is not present the tiles are used.
* ``queryLayers`` provide information to the
  `GetFeature <http://docs.camptocamp.net/cgxp/${main_version}/lib/plugins/GetFeature.html>`_
  plugin on the background layers. It can also be a coma separated string.
  If it is not present the ``mapserverLayers`` is used.
* ``ref`` is used by the
  `MapOpacitySlider <http://docs.camptocamp.net/cgxp/${main_version}/lib/plugins/MapOpacitySlider.html>`_.
* ``visibility`` should be set to ``false`` to do not download unneeded tiles, the
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
