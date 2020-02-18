.. _integrator_api:

JavaScript API
==============

Any c2cgeoportal application exposes a JavaScript API. This API can be used in third-party applications,
like CMS applications.

In the file ``geoportal/demo_geoportal/static-ngeo/api/api.css`` you have the API CSS.

In the file ``geoportal/demo_geoportal/static-ngeo/api/index.js`` you can customize your API with:

.. code:: JavaScript

   // The URL to the themes service.
   config.themesUrl = '<the theme URL>';

   // The projection of the map, for example: 'EPSG:2056'
   config.projection = <the projection>;

   // The resolutions list, for example: [250, 100, 50, 20, 10, 5, 2, 1, 0.5, 0.25, 0.1, 0.05]
   config.resolutions = [<the map resolutions>];

   // The extent restriction, must be in the same projection as `config.projection`.
   // the format is `[minx, miny, maxx, maxy]`, for example: `[420000, 30000, 660000, 350000]`
   // the default is ǹo restriction.
   config.extent = [<the map extent>];

   // The name of the layer to use as background, the layer must be present in the 'background_layers'
   // section of the theme
   config.backgroundLayer = '<the background layer name>';

   // The list of layers (names) that can be queried on mouse click
   config.queryableLayers = [<layer a>, <layer b>, ...];

The API help is in the folder ``geoportal/<package>_geoportal/static/apihelp/``.

In order for a layer to be accessible via API, proceed as follows:

 * Add the layer.
 * Select the 'api' interface.
 * Add the layer to a group which is visible in the API.

.. note::

   A group is visible in the API if it is in a theme whose 'api' interface is checked.
