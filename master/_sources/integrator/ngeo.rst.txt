.. _integrator_ngeo:

ngeo
====

Organisation
------------

The main page where we can redefine the header
is in the file: ``<package>/templates/<interface>.html``.

Where ``<interface>`` is the interface name or "index" for the default interface.

The viewer (map and all related tools)
is define in the file: ``<package>/static-ngeo/js/<interface>.js``.

Where ``<interface>`` is the interface name or "main" for the default interface.

And finally the image should be placed in the folder is ``<package>/static-ngeo/images/``.

The style sheet file for all the project is ``<package>/static-ngeo/less/<package>.less``.

The style sheet file for one interface is ``<package>/static-ngeo/less/<interface>.less``.

HTML file
---------

In this file you can add some blocks like:

.. code:: html

   <gmf-authentication id="login" class="slide" data-header-title="Login">
   </gmf-authentication>

Witch is used to include a directive.

You can find the available directive in the
`ngeo documentation <http://camptocamp.github.io/ngeo/master/apidoc/>`_
in the sections ``gmf/Directives`` and ``ngeo/Directives``.

All the directives should provide an example.

The controller (js file) is commonly named ``mainCtrl``. So you can use a value
from the controller by doing this (here, the controller is the DesktopController):

.. code:: html

    <html lang="{{desktopCtrl.lang}}" ng-app="mydemo" ng-controller="DesktopController as mainCtrl">
      <head>
      ...
      </head>
      <body>
      ...
      <gmf-mydirective gmf-mydirective-variableproperty="mainCtrl.open"
                       gmf-mydirective-staticproperty="::mainCtrl.map">
      <gmf-mydirective>
      ...
      </body>
    </html>

The js constants of the application are defined at the end of the file:

.. code:: html

    <script>
      (function() {
         var module = angular.module('<package>');
         var serverVars = {
             /**
              * Here the i18n is configured
              */
           serviceUrls: {
             /**
              * Here you configure the services URL
              */
           }
         };
         module.constant('serverVars', serverVars);
       })();
    </script>


Controller (js file)
--------------------

In the controler you have some lines like:

.. code:: javascript

   /** @suppress {extraRequire} */
   goog.require('gmf.authenticationDirective');

This is needed to include the javascript of the used directives.

The map configuration will be here:

.. code:: javascript

   goog.base(
         this, {
           srid: 21781,
           mapViewConfig: {
             center: [632464, 185457],
             zoom: 3,
             resolutions: [250, 100, 50, 20, 10, 5, 2, 1, 0.5, 0.25, 0.1, 0.05]
           }
         },
         $scope, $injector);

.. note::

   The resolutions should be the same as in the previus CGXP application to have
   backward compatible permalinks.

Background layers
-----------------

The background layers are configured in the database, with the layer group named
**background** (by default).

WMTS Layers
-----------

To make the WMTS queryable you should add those ``Metadata``:

* ``ogcServer`` with the name of the used ``OGC server``,
* ``layers`` or ``queryLayers`` with the layers to query (groups not supported).

To print the layers in the high quality you you should add those ``Metadata``:

* ``ogcServer`` with the name of the used ``OGC server``,
* ``layers`` or ``printLayers`` with the layers to print.

.. note::

   See also: :ref:`administrator_administrate_metadata`, :ref:`administrator_administrate_ogc_server`.

.. _integrator_ngeo_add:

Add a new interface
-------------------

Be sure you have all the required files:

.. prompt:: bash

   mkdir demo/static-ngeo
   cp -r CONST_create_template/demo/static-ngeo/components demo/static-ngeo/
   cp -r CONST_create_template/demo/static-ngeo/images demo/static-ngeo/
   mkdir demo/static-ngeo/js
   cp CONST_create_template/demo/static-ngeo/js/<package>module.js demo/static-ngeo/js/
   mkdir demo/static-ngeo/less
   cp CONST_create_template/demo/static-ngeo/less/<package>.less demo/static-ngeo/less/
   # Add all the new files to Git
   git add demo/static-ngeo

Get the default interface files, for the mobile:

.. prompt:: bash

  cp CONST_create_template/<package>/templates/mobile.html <package>/templates/<inferface>.html
  cp CONST_create_template/<package>/static-ngeo/less/mobile.less <package>/templates/<inferface>.less
  cp CONST_create_template/<package>/static-ngeo/js/mobile.js <package>/static-ngeo/js/<inferface>.js

Get the default interface files, for the desktop:

.. prompt:: bash

  cp CONST_create_template/<package>/templates/desktop.html <package>/templates/<inferface>.html
  cp CONST_create_template/<package>/static-ngeo/less/desktop.less <package>/templates/<inferface>.less
  cp CONST_create_template/<package>/static-ngeo/js/desktop.js <package>/static-ngeo/js/<inferface>.js

Add them to Git:

.. prompt:: bash

  git add <package>/templates/<inferface>.html
  git add <package>/templates/<inferface>.less
  git add <package>/static-ngeo/js/<inferface>.js

Update the interface in your ``<package>/__init__.py`` file:

.. code:: python

  add_interface(config, "<interface>", INTERFACE_TYPE_NGEO)

The used method has the following API:

.. code:: python

   add_interface(config, interface_name="desktop", interface_type=INTERFACE_TYPE_CGXP, **kwargs)

Where ``config`` is the application configuration object,

``interface_name`` is the name specified in the ``interface`` table,
also used to create the route path,

``interface_type`` may be either ``INTERFACE_TYPE_CGXP``, ``INTERFACE_TYPE_NGEO`` or
``INTERFACE_TYPE_NGEO_CATALOGUE``. Constants available in ``c2cgeoportal``.

Database
--------

The administration interface gives access to an ``interface`` table that lists the
available interfaces (or pages) of the application.
The default interfaces are ``desktop`` add ``mobile``.

Checker
-------

Enable the checker for the new interface.

We suggest to add only the main checker in the ``defaults`` it is what is done by default.

And in the ``all`` (``vars.checker.all``) check all the ngeo interface in standard and debug mode:

.. code:: yaml

   phantomjs_routes:
   - name: <interface>
     param:
       no_redirect: true
   - name: <interface>
     param:
       no_redirect: true
       debug: true

By default it is done for the desktop and mobile interface.
