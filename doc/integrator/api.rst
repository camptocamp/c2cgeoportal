.. _integrator_api:

JavaScript API
==============

Any c2cgeoportal application exposes a JavaScript API. This API can be used in third-party applications,
like CMS applications.

In the file ``geoportal/demo_geoportal/static-ngeo/api/api.css`` you have the API CSS.

In the file ``geoportal/demo_geoportal/static-ngeo/api/index.js`` you can customize your API with:

.. code:: JavaScript

   constants.themesUrl: '<the theme URL>';
   constants.projection: <the projection>;
   constants.supportedProjections: [<the projection>, <another projection>];
   constants.resolutions: [<the map resolutions>];
   constants.extent: [<the map extent>];
   constants.backgroundLayer: '<the background layer name>';

The API help is in the folder ``geoportal/<package>_geoportal/static-ngeo/api/apihelp/``.
