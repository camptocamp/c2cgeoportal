.. _integrator_ngeo_new_interface:

Adding a new user interface
---------------------------

This section describes how to add a new user interface to be named <interface>
(for example, "new") in a package named <package> (for example, "demo").

Makefile
~~~~~~~~
In your project's makefile, add the new interface to ``NGEO_INTERFACES``.
For example, to have two NGEO interfaces called "mobile" and "new", set:

.. code:: makefile

   NGEO_INTERFACES = mobile new

Copy files from template
~~~~~~~~~~~~~~~~~~~~~~~~
First, be sure you have all the required files from the templates; if not,
copy them as follows:

.. prompt:: bash

   mkdir <package>/static-ngeo
   cp -r CONST_create_template/<package>/static-ngeo/components <package>/static-ngeo/
   cp -r CONST_create_template/<package>/static-ngeo/images <package>/static-ngeo/
   mkdir <package>/static-ngeo/js
   cp CONST_create_template/<package>/static-ngeo/js/<package>module.js <package>/static-ngeo/js/
   mkdir <package>/static-ngeo/less
   cp CONST_create_template/<package>/static-ngeo/less/<package>.less <package>/static-ngeo/less/
   # Add all the new files to Git
   git add <package>/static-ngeo

Then, if you want a new mobile interface, get the default files as follows:

.. prompt:: bash

  cp CONST_create_template/<package>/templates/mobile.html <package>/templates/<interface>.html
  cp CONST_create_template/<package>/static-ngeo/less/mobile.less <package>/static-ngeo/less/<interface>.less
  cp CONST_create_template/<package>/static-ngeo/js/mobile.js <package>/static-ngeo/js/<interface>.js

If you want a new desktop interface, get the default files as follows:

.. prompt:: bash

  cp CONST_create_template/<package>/templates/desktop.html <package>/templates/<interface>.html
  cp CONST_create_template/<package>/static-ngeo/less/desktop.less <package>/static-ngeo/less/<interface>.less
  cp CONST_create_template/<package>/static-ngeo/js/desktop.js <package>/static-ngeo/js/<interface>.js

Edit interface files
~~~~~~~~~~~~~~~~~~~~
In the file ``<package>/static-ngeo/js/<interface>.js``, adapt the following lines:

.. code:: js

   * This file defines the "<package>_<interface>" Closure namespace, which is be used as
   ...
   goog.provide('<package>.<Interface>Controller');
   goog.provide('<package>_<interface>');
   ...
   geoportal.<Interface>Controller = function($scope, $injector) {
   ...
   ol.inherits(<package>.<Interface>Controller, gmf.AbstractDesktopController);
   ...
   geoportal.module.controller('<Interface>Controller', <package>.<Interface>Controller);

where ``<package>`` is the name of your package, and ``<interface>`` (desktop in the original file) is
the name of your new interface.

In the file ``<package/static-ngeo/templates/<interface>.html``, adapt the name of the controller and the
referenced css and js files to the new interface name:

.. code:: html

   <html lang="{{mainCtrl.lang}}" ng-app="<package>" ng-controller="<Interface>Controller as mainCtrl">

   <link rel="stylesheet" href="${request.static_url('<package>:static-ngeo/build/<interface>.css')}" type="text/css">
   ...
   goog.require('<package>_<interface>');
   ...
   <script src="${request.static_url('<package>:static-ngeo/build/<interface>.js')}"></script>

Add the new interface files to Git:

.. prompt:: bash

  git add <package>/templates/<inferface>.html
  git add <package>/templates/<inferface>.less
  git add <package>/static-ngeo/js/<inferface>.js

Package file
~~~~~~~~~~~~

Update the interface in your ``<package>/__init__.py`` file:

.. code:: python

  add_interface(config, "<interface>", INTERFACE_TYPE_NGEO)

The used method has the following API:

.. code:: python

   add_interface(config, interface_name="<interface>", interface_type=INTERFACE_TYPE_NGEO, **kwargs)

Where ``config`` is the application configuration object,

``interface_name`` is the name specified in the ``interface`` table,
also used to create the route path,

``interface_type`` may be either ``INTERFACE_TYPE_CGXP``, ``INTERFACE_TYPE_NGEO`` or
``INTERFACE_TYPE_NGEO_CATALOGUE``. Constants available in ``c2cgeoportal``.

Site-specific configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~
After rebuilding your project and verifying that the new interface has no technical errors,
some site-specific configuration issues must be considered:

   - if you have V1 configuration and this has not yet been migrated to V2 configuration
     on this DB instance, it must be migrated now (if it is for test purposes, clone the
     DB first): run script ``.build/venv/bin/themev1tov2``
   - set default theme of the new interface to the desired one (set "defaultTheme"
     in ``<interface>.html``)
   - set meaningful starting zoom level and center coordinates of new interface,
     in ``<interface>.js``
   - after rebuilding, to see the changes in the browser, you probably need to clear
     the browser cache and your URL parameters, and maybe in addition wait some minutes
     in order for the server-side to also be completely up-to-date.

Database
~~~~~~~~

The administration interface gives access to an ``interface`` table that lists the
available interfaces (or pages) of the application.
The default interfaces are ``desktop`` and ``mobile``.
Add the name of your interface to the table. This can be done using the admin interface.

Checker
~~~~~~~

This section describes how to Enable the checker for the new interface.

We suggest to add only the main checker in the ``defaults``. It is what is done by default.
In the ``all`` (``vars.checker.all``) section, check all the ngeo interfaces in standard
and debug mode:

.. code:: yaml

   phantomjs_routes:
   - name: <interface>
     params:
       no_redirect: "true"
   - name: <interface>
     param:
       no_redirect: "true"
       debug: "true"

By default, the checker is enabled for the desktop and mobile interfaces.
