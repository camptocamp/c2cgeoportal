.. _integrator_mobile:

Mobile Applications
===================

*New in 0.8.*

Any c2cgeoportal projet created with the ``c2cgeoportal_create`` and
``c2cgeoportal_update`` scaffolds comes with a `Sencha Touch
<http://www.sencha.com/products/touch/>`_ based mobile application.

The mobile application is available at the URLs ``/mobile_dev/`` and
``/mobile/``. Do not forget the trailing slash! The first URL should be used
during development, as non-minified resources are used. The second URL is for
production.

This application includes the following features:

* Map with zoom buttons.
* Geolocation.
* Base layer selector.
* Overlay selector.
* Text search.
* Map queries (long-press on the map).

Current limitations:

* The overlays only are queryable.
* Non-WMS overlays are not supported.
* For map queries it is assumed that there a 1:1 relationship between WMS
  layers and WFS feature types, which is not the case if a WMS layer is
  actually a group in the mapfile.

For map queries (long-press) to work a `specific OpenLayers commit
<https://github.com/openlayers/openlayers/commit/f5aae88a3141dc94863791e500253b8a89ccd7ce>`_
is required. Commit `444ba16
<https://github.com/camptocamp/cgxp/commit/444ba161fa67cdb503479da12dda71a82a70f310>`_
of CGXP includes this OpenLayers commit. So make sure your c2cgeoportal
application uses this commit (or better) of CGXP.

Adding a mobile app to an existing project
------------------------------------------

To add a mobile application to an existing c2cgeoportal project you first need
to upgrade the project to at least version 0.8 of c2cgeoportal (see the
:ref:`integrator_update_application` section).

Upgrading the project to c2cgeoportal 0.8 will create a ``static/mobile``
directory in the project. But this directory does not include all the necessary
files, as some files are provided by the ``c2cgeoportal_create`` scaffold
(which is not applied for updates). The easiest way to get all the necessary
files involves creating a temporary project of the same name as the target
project, and copying the missing files from there::

   $ cd <project_name>
   $ ./buildout/bin/pcreate -s c2cgeoportal_create \
           /tmp/<project_name> package=<package_name>
   $ cp /tmp/<project_name>/<package_name>/static/mobile/config.js \
        <package_name>/static/mobile/
   $ cp /tmp/<project_name>/jsbuild/mobile.cfg jsbuild/
   $ rm -rf /tmp/<project_name>

The last step involves adding *routes* and *views* specific to the mobile
application. Edit the project's ``__init__.py`` file and add the following
lines before the ``main`` function's return statement::

    # mobile views and routes
    config.add_route('mobile_index_dev', '/mobile_dev/')
    config.add_view('c2cgeoportal.views.mobile.index',
                    renderer='<package_name>:static/mobile/index.html',
                    route_name='mobile_index_dev')
    config.add_route('mobile_config_dev', '/mobile_dev/config.js')
    config.add_view('c2cgeoportal.views.mobile.config',
                    renderer='<package_name>:static/mobile/config.js',
                    route_name='mobile_config_dev')
    config.add_static_view('mobile_dev', '<package_name>:static/mobile')

    config.add_route('mobile_index_prod', '/mobile/')
    config.add_view('c2cgeoportal.views.mobile.index',
                    renderer='<package_name>:static/mobile/build/production/index.html',
                    route_name='mobile_index_prod')
    config.add_route('mobile_config_prod', '/mobile/config.js')
    config.add_view('c2cgeoportal.views.mobile.config',
                    renderer='<package_name>:static/mobile/build/production/config.js',
                    route_name='mobile_config_prod')
    config.add_static_view('mobile', '<package_name>:static/mobile/build/production')

Replace ``<package_name>`` with the project's actual package name.

Now switch to the next section.

Building the mobile application
-------------------------------

The ``CONST_buildout.cfg`` file includes the parts ``jsbuild-mobile`` and
``mobile`` that are dedicated to building the mobile application. These parts
are not executed by default.  To change that edit ``buildout.cfg`` and add the
following line to the ``[buildout]`` section::

    parts += jsbuild-mobile mobile

For the ``mobile`` part to work `Sencha SDK Tools
<http://www.sencha.com/products/sdk-tools/>`_ and `Compass
<http://compass-style.org/>`_ should be installed.

.. note::

    On Windows you will need to override the values of the `mobile` part's
    `compass_cmd` and `sencha_cmd` variables as such::

        [mobile]
        compass_cmd = compass.bat
        sencha_cmd = sencha.bat

    You would add this in `buildout.cfg`, or any Buildout configuration file
    that extends `buildout.cfg`.


The ``sencha`` and ``compass`` commands should be available on the ``PATH``,
and the ``SENCHA_SDK_TOOLS_*`` environment variable should be set as
appropriate. On Camptocamp servers this should be all set for you.

Here's an example of setting ``PATH`` and ``SENCHA_SDK_TOOLS_2_0_0_BETA3``::

    export PATH=${HOME}/.gem/ruby/1.8/bin:${PATH}
    export PATH=/opt/SenchaSDKTools-2.0.0-beta3/:${PATH}
    export SENCHA_SDK_TOOLS_2_0_0_BETA3=/opt/SenchaSDKTools-2.0.0-beta3/

Once built the mobile application should be available on ``/mobile_dev/`` and
``/mobile/`` in the browser, where ``/`` is the root of the WSGI application.

Configuring the map and the layers
----------------------------------

By default the mobile application includes three OSM layers, and
a camptocamp.org WMS layer. The OSM layers are base layers. The camptocamp.org
WMS layer is an overlay. To change the map configuration and the layers for the
mobile application edit the project's ``static/mobile/config.js`` and modify
the config object passed to the ``OpenLayers.Map`` constructor. The execution
of the ``config.js`` script should result in ``App.map`` being set to an
``OpenLayers.Map`` instance.

In addition to the regular options for ``OpenLayers.Layer.WMS`` two specific
options can be defined: ``allLayers`` and ``WFSTypes``. The ``allLayers``
option is an array of possible WMS layers, this is used by the overlay
selector. The ``WFSTypes`` option is an array of corresponding feature types,
it is used by the map querier. If a layer is visible and it has a corresponding
feature type then it will sent in the (WFS GetFeature) map query.

For example::

    new OpenLayers.Layer.WMS(
        'overlay',
        App.wmsUrl,
        {
            // layers to display at startup
            layers: ['npa', 'v_poi_admin'],
            transparent: true
        },
        {
            singleTile: true,
            // list of available layers
            allLayers: ['npa', 'v_poi_admin', 'v_poi_transport', 'v_poi_culture'],
            // list of queriable layers
            WFSTypes: ['npa', 'v_poi_admin', 'v_poi_transport', 'v_poi_culture']
        }
    )

.. note::

    See above to know about current limitations.

One thing you will certainly need to change is the mobile build profile for
OpenLayers. The file to edit is ``jsbuild/mobile.cfg``. For example you will
replace ``OpenLayers/Layer/OSM.js`` by ``OpenLayers/Layer/WMTS.js`` if the base
layers are all WMTS layers. You will also replace
``proj4js/lib/projCode/merc.js`` by ``EPSG21781.js`` if the map uses the Swiss
projection.

UI strings translations
-----------------------

The overlay selector uses the layer names (as defined in the ``allLayers``
array of overlays) as translation keys. To add your translations edit
``static/mobile/config.js`` and populate the ``OpenLayers.Lang.<code>`` objects
as necessary.
