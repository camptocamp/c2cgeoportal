.. _integrator_security:

Security
========

.. _integrator_authentication:
.. include:: authentication.rst
.. _integrator_authentication_oauth2:
.. include:: authentication_oauth2.rst
.. include:: https.rst
.. include:: reset_password.rst

Access to WMS GetCapability
---------------------------

Set ``hide_capabilities`` to ``true`` in your ``vars.yaml`` to disable
the WMS GetCapability when accessing the Mapserver proxy (mapserverproxy).

Default: ``false``


Access to the admin interface
-----------------------------

To disable the admin interface, set ``enable_admin_interface`` to ``false`` in your ``vars.yaml`` file.

Default: ``true``


Access to services by external servers
--------------------------------------

By default, only localhost can access c2cgeoportal's services.
To permit access to a specific service by an external server, you must set CORS headers (``Access-Control-Allow-Origin``)
in your ``vars.yaml`` file.

Add or modify the structure as follows:

.. code:: yaml

    headers:
        <service_name>:
            access_control_allow_origin: ["<domain1>", "<domain2>", ...]
            access_control_max_age: 3600

A ``"*"`` can be included in ``access_control_allow_origin`` to allow everybody to
access, but no credentials will be passed in this case.

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

Authorized referrers
--------------------

To mitigate `CSRF <https://en.wikipedia.org/wiki/Cross-site_request_forgery>`_
attacks, the server validates the referrer against a list of authorized referrers.

By default, only the requests coming from the server are allowed. You can change that list by adding an ``authorized_referers``
list in your ``vars.yaml`` file.

This solution is not the most secure (some people have browser extensions that reset the referrer),
but that is the most consistent approach with regard to the different JS frameworks.
