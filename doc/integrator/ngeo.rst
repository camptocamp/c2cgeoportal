.. _integrator_ngeo:

ngeo
====

Organization
------------

The main page where we can redefine the header is in the file:
``geoportal/<package>_geoportal/static-ngeo/js/apps/<interface>.html.ejs`` and
``geoportal/<package>_geoportal/static-ngeo/js/apps/Controller<interface>.js``
where ``<interface>`` is the interface name.

The style sheet file is ``geoportal/demo_geoportal/static-ngeo/js/apps/sass/<interface>.scss``.

The images used by the application code should be placed in the folder ``geoportal/<package>_geoportal/static-ngeo/images/``.

The images used from the admin interface should be placed in the folder ``geoportal/<package>_geoportal/static/images/``.


HTML file
---------

In this file you can add some blocks like

.. code:: html

   <gmf-authentication id="login" class="slide" data-header-title="Login">
   </gmf-authentication>

to include a directive.

You can find the available directives in the
`ngeo documentation <http://camptocamp.github.io/ngeo/master/apidoc/>`_.

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


Controller (js file)
--------------------

In the controller you have some lines like:

.. code:: javascript

   import gmf<Component>Component from 'gmf/<component>/component.js';

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
   compatible, the resolutions should be the same as in the previous application.

Dynamic.json view
-----------------

To configure the ngeo constants with dynamic or configurable values we have the dynamic view.

This view is configurable in the vars files in the section ``interfaces_config``.
The sub section is the interface name, and after we have:

* ``redirect_interface``: interface to be redirected to if an unexpected device type is used (mobile/desktop).
* ``do_redirect``: directly do the redirect.
* ``constants``: Directly define an ``angular`` constant in the vars file.
* ``dynamic_constants``: Define an ``angular`` constant from a dynamic values.
* ``static``: key: constant name, value: name of the static view that we want to have the URL.
* ``routes``: key: constant name, value:
    ``name``: name of the route witch one we want to have the URL.
    ``params``: view parameters.
    ``dynamic_params``: view parameters from dynamic values.

The dynamic values names are: ``interface``, ``cache_version``, ``lang_urls``, ``fulltextsearch_groups``.

You also have a ``default`` entry from where we can give the base values for ``constants``,
``dynamic_constants``, ``static`` and ``routes``. Values that will be updated with interfaces configuration
(can't be removed with interface configuration).
