.. _integrator_security:

Security
========

Enable / Disable WMS GetCapability
----------------------------------

Set ``hide_capabilities`` to ``true`` in your ``vars_<project>.yaml`` to disable
the WMS GetCapability when accessing the Mapserver proxy (mapserverproxy).

Default: ``false``

Enable / Disable the admin interface
------------------------------------

To disable the admin interface, set ``enable_admin_interface`` to ``false``
in your ``vars_<project>.yaml`` file.

Default: ``true``

Enable / Disable the OGC proxy
------------------------------

To disable the OGC proxy, set ``ogcproxy_enable`` to ``false`` in your
``vars_<project>.yaml`` file.

Default: ``true``

In the ``viewer.js`` files you should also remove the ``OpenLayers.ProxyHost`` configuration.

This implies that all external WMS services (from the database and from the WMS browser) should
have the CORS headers (`enable-cors.org <http://enable-cors.org/server.html>`_).

Access to services by external servers
--------------------------------------

By default, only localhost can access c2c's services.
To permit access to a specific service by an external server, you must set headers CORS (Access-Control-Allow-Origin) in your ``vars_<project>.yaml`` file.

Add or modify the structure like that:

.. code:: yaml

    headers:
        <service_name>:
            access-control-allow-origin: "<domain1>, <domain2>, ..."
