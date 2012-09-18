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

Infrastructure
--------------

Creating and building a mobile application requires the `Sencha SDK Tools
<http://www.sencha.com/products/sdk-tools/>`_ and `Compass
<http://compass-style.org/>`_ to be installed on the target machine.

The ``sencha`` and ``compass`` commands should be available on the ``PATH``,
and the ``SENCHA_SDK_TOOLS_*`` environment variable should be set as
appropriate. On Camptocamp servers this should be all set for you.

Here's an example of setting ``PATH`` and ``SENCHA_SDK_TOOLS_2_0_0_BETA3``::

    export PATH=${HOME}/.gem/ruby/1.8/bin:${PATH}
    export PATH=/opt/SenchaSDKTools-2.0.0-beta3/:${PATH}
    export SENCHA_SDK_TOOLS_2_0_0_BETA3=/opt/SenchaSDKTools-2.0.0-beta3/

Adding a mobile app to a project
--------------------------------

To be able to add a mobile app to a c2cgeoportal project this project should be
able to version 0.8 of c2cgeoportal or better. See
:ref:`integrator_update_application` to know how to upgrade a project.

Adding the Sencha Touch SDK
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Any c2cgeoportal 0.8 project includes a ``static/mobile`` directory containing
a Sencha Touch mobile application. This directory actually misses a major
component of the Sencha Touch application: the Sencha Touch SDK. So you need to
manually add the Sencha Touch SDK to the ``static/mobile`` directory.  For that
you will (1) download the Sencha Touch SDK (version 2.0.1.1), (2) dearchive it
at any location (``/tmp/``), (3) create a temporary Sencha Touch application,
and (4) copy the ``skd`` directory from that temporary Sencha Touch application
to your project's ``static/mobile`` dir. For example::

    $ cd /tmp/
    $ wget http://cdn.sencha.io/touch/sencha-touch-2.0.1.1-gpl.zip
    $ unzip sencha-touch-2.0.1.1-gpl.zip
    $ sencha generate app TempApp /tmp/TempApp
    $ cp -r /tmp/Temp/sdk <path/to/c2cgeoportal/project/module>/static/mobile/

You can now version-control this ``sdk`` directory.

Adding missing files
~~~~~~~~~~~~~~~~~~~~

You can skip this section if your project has been created using c2cgeoportal
0.8 or better. If you project was created using an older c2cgeoportal, and if
you've just upgraded your project to c2cgeoportal 0.8, then you need to follow
the below instructions.

Upgrading the project to c2cgeoportal 0.8 will create a ``static/mobile``
directory in the project. But this directory does not include all the necessary
files, as some files are provided by the ``c2cgeoportal_create`` scaffold
(which is not applied for updates). The easiest way to get all the necessary
files involves creating a temporary c2cgeoportal project of the same name as
the target project, and copying the missing files from there::

   $ cd <project_name>
   $ ./buildout/bin/pcreate -s c2cgeoportal_create \
           /tmp/<project_name> package=<package_name>
   $ cp /tmp/<project_name>/<package_name>/static/mobile/config.js \
        <package_name>/static/mobile/
   $ cp /tmp/<project_name>/jsbuild/mobile.cfg jsbuild/
   $ rm -rf /tmp/<project_name>

Adding mobile routes and views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

For the ``mobile`` part to work Sencha SDK Tools and Compass should be
installed on the build machine. (See above.)

.. note::

    On Windows you will need to override the values of the `mobile` part's
    `compass_cmd` and `sencha_cmd` variables as such::

        [mobile]
        compass_cmd = compass.bat
        sencha_cmd = sencha.bat

    You would add this in `buildout.cfg`, or any Buildout configuration file
    that extends `buildout.cfg`.


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
feature type then it will be sent in the (WFS GetFeature) map query.

.. note::

    The ``WFSTypes`` config option can be used for the base layers as well.
    In this case, the given feature types should also correspond to queriable
    layers in the mapfile.

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

Raster service
--------------

When querying the map (longpress), the c2cgeoportal ``raster`` service can be
used to retrieve data from raster file (elevation, slope, etc...) and display
it in the ``Query view`` above query results.

If the raster service is already configured on the server, you can activate it
in the mobile application by adding the following to the config.js file::

    App.raster = true;

You'll also need to add a template string to each translation object. It needs
to be adapted to the data retrieved from the server::

    OpenLayers.Lang.fr = {
        [...]
        'rasterTpl': [
            '<div class="coordinates">',
                '<p>X : {x} - Y : {y}</p>',
                '<p>Altitude terrain : {mnt} m</p>',
                '<p>Altitude surface : {mns} m</p>',
            '</div>'
        ].join(''),
        [...]
    };

In the example above ``mns`` and ``mnt`` are the keys used in the server
config for the ``raster web services``.
