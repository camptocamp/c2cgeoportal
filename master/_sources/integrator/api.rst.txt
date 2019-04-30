.. _integrator_api:

JavaScript API
==============

Any c2cgeoportal application exposes a JavaScript API. This API can be used in third-party applications,
like CMS applications.

In the file ``geoportal/demo_geoportal/static-ngeo/api/api.css`` you have the API CSS.

In the file ``geoportal/demo_geoportal/static-ngeo/api/index.js`` you can customize your API with:

.. code:: JavaScript

   config.themesUrl = '<the theme URL>';
   config.projection = <the projection>;
   config.resolutions = [<the map resolutions>];
   config.extent = [<the map extent>];
   config.backgroundLayer = '<the background layer name>';

The API help is in the folder ``geoportal/<package>_geoportal/static-ngeo/api/apihelp/``.
