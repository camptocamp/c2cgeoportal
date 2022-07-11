.. _integrator_c2cwsgiutils:

C2C WSGI Utils
==============

 ``c2cwsgiutils`` is a framework assisting in development, integration and administration of WSGI applications.
``c2cgeoportal`` uses ``c2cwsgiutils``.
See its `documentation <https://github.com/camptocamp/c2cwsgiutils/#camptocamp-wsgi-utilities>`__.

The entry point URL is ``<application main URL>/c2c``, where you will have a dashboard with the
``c2cwsgiutils`` and ``c2cgeoportal`` services.

The ``invalidate`` view is protected with the same authentication, see below.

.. _integrator_c2cwsgiutils_auth:

Authentication
--------------

To have basic authentication of those tools (and on tile generation) you can set
``C2C_SECRET`` in the ``env.project`` file to have single password without brute force protection.

You can also activate the authentication on GitHub with OAuth2, the configuration is in the
``env.project`` file:

* Verify that the ``C2C_AUTH_GITHUB_REPOSITORY`` is correctly configured.
* By default, the ``C2C_AUTH_GITHUB_ACCESS_TYPE`` is set to admin then only admins users of the previously
  defined repository have access.
* You should ask Camptocamp for a new secret and set it in ``C2C_AUTH_GITHUB_CLIENT_SECRET``.
  It will be defined in the GitHub organizations settings, on 'Developer settings', 'OAuth Apps',
  'Geoservicies` application, 'Generate a new client secret',
  the URL should also be configured in the redirect proxy.
* Define the ``C2C_AUTH_GITHUB_SECRET`` randomly.


If you want to be independent you should:

* Verify that the ``C2C_AUTH_GITHUB_REPOSITORY`` is correctly configured.
* By default, the ``C2C_AUTH_GITHUB_ACCESS_TYPE`` is set to admin then only admins users of the previously
  defined repository have access.
* Create an OAuth Apps on GitHub: GitHub organizations settings, on 'Developer settings', 'OAuth Apps',
  'New OAuth App`, fill the form, reopen the application, 'Generate a new client secret',
  ``C2C_AUTH_GITHUB_CLIENT_ID`` and ``C2C_AUTH_GITHUB_CLIENT_SECRET`` should be configured with the
  obtain information.
* Define the ``C2C_AUTH_GITHUB_SECRET`` randomly.


For more information see
`C2C WSGI Utils Readme <https://github.com/camptocamp/c2cwsgiutils#general-config>`_.
