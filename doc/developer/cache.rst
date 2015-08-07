.. _developer_cache:

Cache management
================

Here we describe the strategy we use to manage the cache.

We have three kinds of services:
 * Without any cache (**no_cache**).
 * Cache related to the application version (**public_cache**).
 * Cache related to the application version and the current role (**private_cache**).

For some service we also set the header ``Vary`` to ``Accept-Language``
to have one cache per language.

Server side
-----------

On the server side we set the ``Cache-Control`` header with a different value
depending on the cache type.

 * **no_cache**: ``no-cache``.
 * **public_cache**: ``max-age=864000, public``.
 * **private_cache**: ``max-age=864000, public`` or ``max-age=864000, private`` if we are logged in.

The ``max-age`` is configurable in a ``vars`` file in the ``default_max_age`` attribute.

Client side
-----------

On the client side we will add some attribute in the URL parameters to
force to have the right version of the cache.
It will be done automatically by the ``route_url`` method.

 * **no_cache**: nothing to add (be sure that the lib does not add custom cache).
 * **public_cache**: add the query param named ``cache_version``.
 * **private_cache**: add the query param named ``cache_version`` and ``role``.

With ``CGXP`` interface you have the variables ``version_params``, ``version_role_params``
and ``version_role_user_params`` that help you to create the right url.

With ``ngeo`` interface you have the ``cache_version`` variable.

Service list
------------

No cache
~~~~~~~~

 * cgxp_index
 * ngeo index
 * mobile index
 * api js
 * xapi js
 * api help
 * xapi help
 * auto login form (loginform403)
 * login
 * logout
 * login change password
 * echo
 * export csv
 * full text search
 * layers/read_many
 * layers/read_one
 * layers/count
 * layers/create
 * layers/update
 * layers/delete
 * WMS/GetMap
 * WMS/GetFeatureInfo
 * WFS/GetFeature
 * WFS all POST
 * PDF report
 * print/report.pdf
 * print/status
 * print/get file
 * profile
 * raster
 * shortener

Public cache
~~~~~~~~~~~~

 * login form
 * layers/enumerate_attribute_values
 * WMS/GetLegendGraphic

Private cache
~~~~~~~~~~~~~

 * cgxp viewer
 * mobile config
 * themes
 * layers/metadata
 * WMS/GetCapabilities
 * WMS/DescribeLayer
 * WFS/GetCapabilities
 * WFS/DescribeFeaturesType
 * print/capabilities.json
