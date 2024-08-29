.. _integrator_interface:

Introduction
------------

This chapter describes how to integrate a new ``custom`` interface in a c2cgeoportal application.

``custom`` means that the interface can be based on other frontend than ngeo event if at the end of this
document we will speak about how to integrate a ngeo as custom interface with a simple build chain.

Review
------

In the c2cgeoportal application we have by default 3 interfaces: desktop, mobile and iframe.

c2cgeoportal provide different things around the interface but they are not hard linked:

- The interface in the admin interface is a way to define the layers visible in the interface.
- The ``interfaces_config`` in the ``vars.yaml`` is a way to define the interface configuration.
- The ``interface`` in the ``vars.yaml`` is a way to configure the interfaces route in c2cgeoportal: ``/``,
  ``/theme/<theme>``, ``/<interface>`` and ``/<interface>/theme/<theme_name>``.

Configuration
-------------

Here we will describe how to add a new ``custom`` interface in a c2cgeoportal application,
for that we should add a new entry in the ``interface_config`` with the ``type`` set to ``custom``.

.. code:: yaml

    vars:
      interfaces_config:
        custom:
          type: custom
          name: my_interface

We can also add an optional ``file`` attribute in the config to specify the file that should be used for the interface,
with relative (from ``/etc/static-frontend``) or absolute file name.

Interface integration
---------------------

To publish the interfaces que should provide the interfaces files (HTML, CSS, JavaScript, images, ...) in
the ``/etc/static-frontend/`` directory.

The interface files should be in a directory named with the interface name suffixed by ``.html``.

Note that this folder is also available on the ``/static-frontend/`` endpoint with cache headers without
any cash bustering, then the files (other than the interfaces HTML files) should contains an hash.

If you need cache bustering you should put your files in the ``geoportal/geomapfish_geoportal/static/``
directory (``/etc/geomapfish/static`` in the container).

The interface HTML file is considered as mako template and he can use the following variables:
- ``request``: the Pyramid request object.
- ``dynamicUrl``: the URL to get the interface configuration.
- ``interface``: the interface name.
- ``staticFrontend``: the URL to the static frontend directory.
- ``staticCashBuster``: the URL to the static cash buster directory.

For that you should create a Docker image that provide a ``/etc/static-frontend/`` volume (``VOLUME /etc/static-frontend``).

And include it in the ``docker-compose.yaml`` file with something like:

.. code:: yaml

    services:
      my_interface:
        image: my_interface
        user: www-data

      geoportal:
        volumes_from:
          - my_interface:ro

Ngeo integration
----------------

TODO
