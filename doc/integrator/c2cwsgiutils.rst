.. _integrator_c2cwsgiutils:

c2cwsgiutils
============

c2cwsgiutils is a framework assisting in development, integration and administration of WSGI applications.
c2cgeoportal uses c2cwsgiutils.
See its `documentation <https://github.com/camptocamp/c2cwsgiutils/#camptocamp-wsgi-utilities>`__.

The entry point URL is ``<application main URL>/c2c``, where you will have a dashboard with the
c2cwsgiutils and c2cgeoportal services.

To use the protected tools, you should at least set C2C_SECRET to a secret password in the file `env.default`.

The ``invalidate`` view is also protected with this secret.
