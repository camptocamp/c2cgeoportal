.. _integrator_mobile:

Mobile Applications
===================

Any c2cgeoportal projet created with the ``c2cgeoportal_create`` and
``c2cgeoportal_update`` scaffolds comes with a `Sencha Touch
<http://www.sencha.com/products/touch/>`_ based mobile application.

The mobile application is available at the URLs ``<instance_id>/wsgi/mobile_dev/`` and
``<instance_id>/wsgi/mobile/``. Do not forget the trailing slash! The first URL should be used
during development, as non-minified resources are used. The second URL is for
production. The second URL is for production as well as its alias ``<apache_entry_point>/mobile``.

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

Creating and building a mobile application requires the `Sencha Cmd
<http://www.sencha.com/products/sencha-cmd/download/>`_ tools and `Compass
<http://compass-style.org/>`_ to be installed on the target machine.

On Camptocamp server we just need the Debian packages ``sencha-cmd``
and ``ruby-compass`` (The ``sencha-cmd`` package was created by
the Camptocamp sysadmins).

On Camptocamp servers, in case you have both ``sencha-sdk-tools`` and
``sencha-cmd`` installed, commands are named respectively ``sencha-sdk``
and ``sencha-cmd``. By default the ``sencha-cmd`` command is used, if
it's not the case on your host put the following configuration variables
in your `<package>.mk` file:

.. code:: make

    SENCHA_CMD = <sencha-command>

Replace ``<sencha-command>`` by ``sencha-sdk`` if you want to build the
mobile app using a version of GeoMapFish older than 1.4.

Adding mobile routes and views
------------------------------

The last step involves adding *routes* and *views* specific to the mobile
application. Edit the project's ``__init__.py`` file and add the following
lines before the ``main`` function's return statement:

.. code:: javascript

    # mobile views and routes
    config.add_route('mobile_index_dev', '/mobile_dev/')
    config.add_view('c2cgeoportal.views.entry.Entry',
                    attr='mobile',
                    renderer='<package>:static/mobile/index.html',
                    route_name='mobile_index_dev')
    config.add_route('mobile_config_dev', '/mobile_dev/config.js')
    config.add_view('c2cgeoportal.views.entry.Entry',
                    attr='mobileconfig',
                    renderer='<package>:static/mobile/config.js',
                    route_name='mobile_config_dev')
    config.add_static_view('mobile_dev', '<package>:static/mobile')

    config.add_route('mobile_index_prod', '/mobile/')
    config.add_view('c2cgeoportal.views.entry.Entry',
                    attr='mobile',
                    renderer='<package>:static/mobile/build/production/App/index.html',
                    route_name='mobile_index_prod')
    config.add_route('mobile_config_prod', '/mobile/config.js')
    config.add_view('c2cgeoportal.views.entry.Entry',
                    attr='mobileconfig',
                    renderer='<package>:static/mobile/build/production/App/config.js',
                    route_name='mobile_config_prod')
    config.add_static_view('mobile', '<package>:static/mobile/build/production/App')

Replace ``<package>`` with the project's actual package name.

Now switch to the next section.

Building the mobile application
-------------------------------

The ``CONST_Makefile`` file includes the part ``sencha-touch`` and
``mobile`` that are dedicated to building the mobile application.

For the ``mobile`` part to work Sencha SDK Tools and Compass should be
installed on the build machine. (See above.)

.. note::

    On Windows you will need to override the values of the ``mobile`` part
    ``SENCHA_CMD`` variables as such:

    .. code:: make

        SENCHA_CMD = sencha.bat

    You would add this in ``<package>.mk``, or any make configuration file
    that extends ``<package>.mk``.

Once built the mobile application should be available on ``<instance_id>/wsgi/mobile_dev/`` and
``<instance_id>/wsgi/mobile/`` in the browser.


Configuring the map and the layers
----------------------------------

To change the map configuration and the layers for the mobile application edit
the project's ``static/mobile/config.js`` and modify the config object passed
to the ``OpenLayers.Map`` constructor. The execution of the ``config.js``
script should result in ``App.map`` being set to an ``OpenLayers.Map``
instance.

Theme
~~~~~

The list of themes and layers shown in the mobile application is dynamically
generated. See :ref:`administrator_guide`.

Raster service
--------------

When querying the map (longpress), the c2cgeoportal ``raster`` service can be
used to retrieve data from raster file (elevation, slope, etc...) and display
it in the ``Query view`` above query results.

If the raster service is already configured on the server, you can activate it
in the mobile application by adding the following to the config.js file::

    App.raster = true;

You'll also need to add a template string to each translation object. It needs
to be adapted to the data retrieved from the server:

.. code:: javascript

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

Permalink crosshair
-------------------

A crosshair can be shown on the map when requesting the mobile application. To
do so, the following parameters have to be defined in the called URL:

* ``map_zoom``: map some level
* ``map_x``: x coordinate on which the marker will be placed
* ``map_y``: y coordinate on which the marker will be placed
* ``map_crosshair``: set to a value (e.g. ``map_crosshair=1``)

By default, the OpenLayers default marker will be used.

To use a custom marker, do the following changes in the ``static/mobile/config.js``
file:

* Set ``OpenLayers.ImgPath`` to the path where you custom marker is.
* Define the following new variable::

      App.crosshair_options = {
          'path': OpenLayers.ImgPath+'custom_marker.png',
          'size': [image_width, image_height]
      };

Where ``image_width`` and ``image_height`` are respectively the width and the
height of the crosshair image.

Settings view
-------------

The ``Settings`` view, located in ``app/view/Settings.js``, can be customized
to suit the project needs. The ``Settings.js`` file is part of c2cgeoportal's
``c2cgeoportal_create`` scaffold, it will therefore not be overwritten when
applying the ``c2cgeoportal_update`` scaffold during an update of c2cgeoportal.


If style customization is also required for components in this view, use the
``custom.scss`` file.

Permalink
~~~~~~~~~

If a permalink field is needed, just add the following component in the
Settings view:

.. code:: javascript

    { xtype: 'map_permalink' }

Login/logout
~~~~~~~~~~~~

The mobile application includes a ``Login`` view component that the
``Settings`` view can include as one of its items. This component enables login
and logout. If the user is not authenticated the ``Login`` component adds
a "log in" button, that, when clicked, redirects the user to a login form view.
If the user is authenticated the ``Login`` component adds a welcome message,
and a "log out" button.

Here's an example of a ``Settings`` view that includes a ``Login`` view
component:

.. code:: javascript

    Ext.define("App.view.Settings", {
        extend: 'Ext.Container',
        xtype: 'settingsview',
        requires: [
            // Do not forget this requirement, or Sencha Touch
            // will complain that "widget.login" is an
            // unrecognized alias.
            'App.view.Login'
        ],
        config: {
            items: [{
                xtype: 'toolbar',
                docked: 'top',
                items: [{
                    xtype: 'spacer'
                }, {
                    xtype: 'button',
                    iconCls: 'home',
                    iconMask: true,
                    action: 'home'
                }]
            }, {
                xtype: 'container',
                cls: 'settings',
                items: [{
                    xtype: 'component',
                    html: '<p>Some text</p>'
                }, {
                    // This is the login view component.
                    xtype: 'login'
                }]
            }]
        }
    });

The i18n keys relative to the login/logout functionality are: ``welcomeText``,
``loginLabel``, ``passwordLabel``, ``loginSubmitButtonText``, and
``loginCancelButtonText``. The last four pertain to the login form, they should
be self-explanatory. ``welcomeText`` is the text displayed above the "log out"
button when the user is authenticated, it typically includes the variable
``{username}``, which is changed to the actual username at render time. By
default, ``config.js`` includes the following english translations:

.. code:: javascript

    OpenLayers.Lang.en = {
        ...
        // login/logout
        'loginButtonText': 'Log in',
        'welcomeText': '<p>You are {username}.</p>',
        'logoutButtonText': 'Log out',
        'loginLabel': 'Login',
        'passwordLabel': 'Password',
        'loginSubmitButtonText': 'Submit',
        'loginCancelButtonText': 'Cancel'
    };

For the ``Login`` component to work the ``App.info`` JavaScript variable should
be set. The setting of this variable should be done anywhere in the
``config.js`` file, with this:

.. code:: javascript

    App.info = '${info | n}';

By default ``config.js`` includes it.

Multiple mobile applications
----------------------------

This section discusses the possibility of having multiple mobile applications
within a c2cgeoportal application.

As you will find out by reading the rest of this section creating multiple
mobile applications is a clear violation of the "don't repeat yourself"
principle. It is therefore discouraged; creating multiple *profiles* of the
mobile application should be done through multiple themes. However you may need
multiple mobile applications if you want, for example, different base layers,
and/or a high degree of customization, for each application.

Any c2cgeoportal application includes a mobile application in the
``<package>/static/mobile/`` directory.  The mobile application is created
by the ``c2cgeoportal_create`` and ``c2cgeoportal_update`` scaffolds. To create
another mobile application, the easiest is to copy the existing ``mobile``
directory into a new directory. For example:

.. prompt:: bash

    cd <package>/static
    cp -r mobile mobile2

.. warning::

    It is important to note that the ``c2cgeoportal_update`` scaffold, which is
    used when updating a c2cgeoportal application to a new c2cgeoportal
    version, will update the ``mobile`` directory only. This further means that
    any other mobile application will need to be manually updated (by copying
    files).

Other things need to be duplicated:

* The ``jsbuild`` mobile config file should be duplicated.

  For this copy
  ``jsbuild/mobile.cfg`` into ``jsbuild/mobile2.cfg``, for example. You may
  want to adapt the new config file, based on your needs.

* The ``sencha-touch`` make part should be duplicated.

  For this copy the ``[jsbuild-mobile]`` and ``[mobile]`` sections of
  ``CONST_buildout.cfg``, them into the application's ``buildout.cfg`` file,
  rename them (to ``[jsbuild-mobile2]`` and ``[mobile2]``), and adapt their
  contents so they reference the new mobile directory (``static/mobile2``), and
  the new ``jsbuild`` mobile config file (``jsbuild/mobile2.cfg``).

  You also need to add ``jsbuild-mobile2`` and ``mobile2`` to the list
  of parts that are run by Buildout by default::

      [buildout]
      extends = CONST_buildout.cfg
      parts += jsbuild-mobile mobile jsbuild-mobile2 mobile2

  At this point you should be able to successfully run Buildout again.

* The mobile routes and views should be duplicated.

  For that edit the application's main ``__init__.py`` file and copy the entire
  ``# mobile views and routes`` block, and paste it right below the original.
  Now change the route names, for example from ``mobile_index_dev`` to
  ``mobile_index_dev2``. Change the route URLs, for example from
  ``/mobile_dev/`` to ``/mobile_dev2/``. Change the paths to the templates
  files, for example from
  ``renderer='<package>:static/mobile/index.html'`` to
  ``renderer='<package>:static/mobile2/index.html'``.  Do this for every
  route and view.

  You should be done.
