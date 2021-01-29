.. _integrator_api:

JavaScript API
==============

Any c2cgeoportal application exposes a JavaScript API. This API can be used in third-party applications,
such as CMS applications.

The API CSS is in the file ``geoportal/<package>_geoportal/static-ngeo/api/api.css``.

You can customize your API by editing the file ``geoportal/vars.yaml`` section ``interfaces_config/api``,
see: `API constants definition <https://camptocamp.github.io/ngeo/master/jsdoc/module-api_src_options.html>`


The API help is in the folder ``geoportal/<package>_geoportal/static/apihelp/``.

In order for a layer to be accessible via API, proceed as follows:

 * Add the layer.
 * Select the 'api' interface.
 * Add the layer to a group which is visible in the API.

.. note::

   A group is visible in the API if it is in a theme whose 'api' interface is checked.
