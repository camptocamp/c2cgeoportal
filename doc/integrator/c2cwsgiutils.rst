.. _integrator_c2cwsgiutils:

c2cwsgiutils
============

c2cgeoportal uses c2cwsgiutils. You can use functionalities from c2cwsgiutils to assist in integration tasks.
See its `documentation <https://github.com/camptocamp/c2cwsgiutils/#camptocamp-wsgi-utilities>`__.

The entry point URL is ``<application main URL>/c2c`` And here we will have a dashboard with the
c2cwsgiutils and c2cgeoportal services.

To use the protected tools you should at least set C2C_SECRET to a sectet password in the file `.env.mako`.

Now the invalidate view is also protected with this secret.
