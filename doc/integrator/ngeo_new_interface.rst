.. _integrator_ngeo_new_interface:

Adding a new user interface
---------------------------

.. note::

    This is not possible in the simple application mode

This section describes how to add a new user interface to be named <interface>
(for example, "new") in a package named ``<package>``.

Makefile
~~~~~~~~
In your project's makefile, add the new interface to ``NGEO_INTERFACES``.
For example, to have two NGEO interfaces called "mobile" and "new", set:

.. code:: makefile

   NGEO_INTERFACES = mobile new

Copy files from template
~~~~~~~~~~~~~~~~~~~~~~~~

If you want a new mobile interface, get the default files as follows:

.. prompt:: bash

  cp CONST_create_template/geoportal/<package>_geoportal/static-ngeo/js/apps/mobile.html.ejs \
    geoportal/<package>_geoportal/static-ngeo/js/apps/<interface>.html.ejs
  cp CONST_create_template/geoportal/<package>_geoportal/static-ngeo/js/apps/Controllermobile.js \
    geoportal/<package>_geoportal/static-ngeo/js/apps/Controller<interface>.js

If you want a new desktop interface, get the default files as follows:

.. prompt:: bash

  cp CONST_create_template/geoportal/<package>_geoportal/static-ngeo/js/apps/desktop.html.ejs \
    geoportal/<package>_geoportal/static-ngeo/js/apps/<interface>.html.ejs
  cp CONST_create_template/geoportal/<package>_geoportal/static-ngeo/js/apps/Controllerdesktop.js \
    geoportal/<package>_geoportal/static-ngeo/js/apps/Controller<interface>.js

Edit interface files
~~~~~~~~~~~~~~~~~~~~
In the file ``geoportal/<package>_geoportal/static-ngeo/js/apps/Controller<interface>.js``,
adapt the following lines:

.. code:: js

   ...
   exports.module = angular.module('App<interface>', [
   ...
   exports.module.controller('<Interface>Controller', exports);
   ...

where  ``<interface>`` (desktop in the original file) is the name of your new interface.

In the file ``geoportal/<package>_geoportal/static-ngeo/static-ngeo/js/apps/<interface>.html.ejs``,
adapt the name of the controller and the referenced css and js files to the new interface name:

.. code::

   ...
   <html lang="{{mainCtrl.lang}}" ng-controller="<Interface>Controller as mainCtrl">
   ...
   <meta name="interface" content="<interface>">
   ...

Add the new interface files to Git:

.. prompt:: bash

  git add geoportal/<package>_geoportal/static-ngeo/js/apps/<interface>.html.ejs
  git add geoportal/<package>_geoportal/static-ngeo/js/apps/Controller<interface>.js

Package file
~~~~~~~~~~~~

Update the interface in your ``geoportal/<package>_geoportal/__init__.py`` file:

.. code:: python

  add_interface(config, "<interface>", INTERFACE_TYPE_NGEO)

The used method has the following API:

.. code:: python

   add_interface(config, interface_name="<interface>", interface_type=INTERFACE_TYPE_NGEO, **kwargs)

where:

* ``config`` is the application configuration object,
* ``interface_name`` is the name specified in the ``interface`` table,
  also used to create the route path,
* ``interface_type`` may be either ``INTERFACE_TYPE_NGEO`` or
  ``INTERFACE_TYPE_NGEO_CATALOGUE``.

Site-specific configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

After rebuilding your project and verifying that the new interface has no technical errors,
some site-specific configuration issues must be considered:

   - set the default theme of the new interface as desired (set ``defaultTheme``
     in ``<interface>.html``)
   - set a meaningful starting zoom level and center coordinates of the new interface,
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

This section describes how to enable the checker for the new interface.

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
