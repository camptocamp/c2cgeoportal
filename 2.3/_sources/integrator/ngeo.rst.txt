.. _integrator_ngeo:

ngeo
====

Organisation
------------

The main page where we can redefine the header
is in the file: ``<package>/templates/<interface>.html``,
where ``<interface>`` is the interface name or "index" for the default interface.

The viewer (map and all related tools)
is defined in the file: ``<package>/static-ngeo/js/<interface>.js``,
where ``<interface>`` is the interface name or "main" for the default interface.

Finally, the image should be placed in the folder ``<package>/static-ngeo/images/``.

The style sheet file for the whole project is ``<package>/static-ngeo/less/<package>.less``.

The style sheet file for a specific interface is ``<package>/static-ngeo/less/<interface>.less``.

HTML file
---------

In this file you can add some blocks like

.. code:: html

   <gmf-authentication id="login" class="slide" data-header-title="Login">
   </gmf-authentication>

to include a directive.

You can find the available directives in the
`ngeo documentation <http://camptocamp.github.io/ngeo/master/apidoc/>`_
in the sections ``gmf/Directives`` and ``ngeo/Directives``.

The controller (``js`` file) is commonly named ``mainCtrl``. So you can use a value
from the controller by doing the following (here, the controller is the ``DesktopController``):

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

The ``js`` constants of the application are defined at the end of the file:

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

In the controller you have some lines like:

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

   If you previously had a CGXP application and want to keep your permalinks
   compatible, the resolutions should be the same as in the previous
   application.
