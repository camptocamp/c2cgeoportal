.. _integrator_security:

Security
========

.. _integrator_authentication:
.. include:: authentication.rst
.. _integrator_authentication_oidc:
.. include:: authentication_oidc.rst
.. _integrator_authentication_oauth2:
.. include:: authentication_oauth2.rst
.. include:: https.rst
.. include:: reset_password.rst


Security update
---------------

To be sure that we regularly get the security updates, every night the GeoMapFish Docker images are rebuild.
And every time we do a build we pull the new images to use them.

For project on Kubernetes we also deploy fresh built images every day.

This is good for security but with that we can't guarantee that the result of a new build works exactly
as the previous one.

To avoid incidents on production service, Kubernetes will publish a service only if he start correctly.
For Project on Docker Compose we have to choose ourself. The best is to build the image only on
integration when the result is correct we push it on a repository, and on production we will use the
images from the repository. The other solution is to use fixed tag for the base image, this imply that we
should do a minor update of the application to get the security fix. To do that you should set
in the ``project.yaml`` file the template parameter ``unsafe_long_version`` to ``True`` in the
``template_vars`` section.


Access to WMS GetCapability
---------------------------

Set ``hide_capabilities`` to ``true`` in your ``vars.yaml`` to disable
the WMS GetCapability when accessing the MapServer proxy (mapserverproxy).

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

By default, only the requests coming from the server are allowed. You can change that list by adding an ``vars.authorized_referers``
list in your ``vars.yaml`` file.

This solution is not the most secure (some people have browser extensions that reset the referrer),
but that is the most consistent approach with regard to the different JS frameworks.

Allowed hosts
-------------

For security reason we check the host of the request, to be sure that the request is coming from an authorized domain.

For that we have the following configurations in the ``vars.yaml`` file:

- `vars.authentication.allowed_hosts`: List of hosts that are allowed to access the oauth2 authentication service (same host allowed).

- `vars.shortener.allowed_hosts`: List of hosts that are allowed to be shortened (same host allowed).

- `vars.admin_interface.allowed_hosts`: List of host that are allowed to be redirected by the ogc_server_clear_cache (same host allowed).

- `vars.allowed_hosts`: List of hosts that are allowed to access the application (theme and dynamic.json).
