.. _integrator_security:

Security
========

.. include:: authentication.rst
.. include:: https.rst
.. include:: reset_password.rst

Access to WMS GetCapability
----------------------------------

Set ``hide_capabilities`` to ``true`` in your ``vars_<project>.yaml`` to disable
the WMS GetCapability when accessing the Mapserver proxy (mapserverproxy).

Default: ``false``

Access to the admin interface
------------------------------------

To disable the admin interface, set ``enable_admin_interface`` to ``false``
in your ``vars_<project>.yaml`` file.

Default: ``true``

Access to the OGC proxy
------------------------------

To enable the OGC proxy, set ``ogcproxy_enable`` to ``true`` in your
``vars_<project>.yaml`` file.

Default: ``false``

And adding the ``papyrus_ogcproxy`` package in the ``install_requires`` of the ``setup.py`` file.

In the ``viewer.js`` files you should also add the ``OpenLayers.ProxyHost`` configuration:

.. code:: javascript

   OpenLayers.ProxyHost = "${request.route_url('ogcproxy') | n}?url=";

Working without this proxy implies that all external WMS services (from the database and from the WMS browser) should
have the CORS headers (`enable-cors.org <http://enable-cors.org/server.html>`_).

Access to services by external servers
--------------------------------------

By default, only localhost can access c2c's services.
To permit access to a specific service by an external server, you must set headers CORS (Access-Control-Allow-Origin) in your ``vars_<project>.yaml`` file.

Add or modify the structure like that:

.. code:: yaml

    headers:
        <service_name>:
            access_control_allow_origin: ["<domain1>", "<domain2>", ...]
            access_control_max_age: 3600

A ``"*"`` can be included in ``access_control_allow_origin`` to allow everybody to
access, but no credentials will be passed in the case.

Available services are:

Entry:

- index
- config
- api

Services:

- themes
- login
- mapserver
- print
- profile
- raster
- layers
- login
- error

Authorized referers
-------------------

To mitigate `CSRF <https://en.wikipedia.org/wiki/Cross-site_request_forgery>`_
attacks, the server validates the referer against a list of authorized referers.

By default, only the pages coming from the server are allowed. You can change
that list by adding an ``authorized_referers`` list in your
``vars_<project>.yaml`` file.

This solution is not the most secure (some people have browser extensions that
reset the referer), but that is the easiest to implement with all our different
JS frameworks.
