.. _integrator_ngeo:

ngeo
====

Organisation
------------

The main page where we can redefine the header
is in the file: ``<package>/templates/<interface>.html``.

Where `<interface>` is the interface name or "index" for the default interface.

The viewer (map and all related tools)
is define in the file: ``<package>/static-ngeo/js/<interface>.js``.

Where `<interface>` is the interface name or "main" for the default interface.

And finally the image should be placed in the folder is ``<package>/static-ngeo/images/``.

The style sheet file for all the project is ``<package>/static-ngeo/less/<package>.less``.

The style sheet file for one interface is ``<package>/static-ngeo/less/<interface>.less``.

HTML file
=========

In this file you can add some blocks like:

.. code:: html

   <gmf-authentication id="login" class="slide" data-header-title="Login">
   </gmf-authentication>

Witch is used to include a directive.

You can find the available directive in the
`ngeo documentation <http://camptocamp.github.io/ngeo/master/apidoc/>`_
in the sections 'gmf/Directives' and 'ngeo/Directives'.

All the directives should provide an example.

At the end of the file you find something like:

.. code:: javascript

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
====================

In the controler you have some lines like:

.. code:: javascript

   /** @suppress {extraRequire} */
   goog.require('gmf.authenticationDirective');

This is needed to include the javascript of the used directives.
