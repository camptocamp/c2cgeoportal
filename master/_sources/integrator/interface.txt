.. _integrator_interface:

Interfaces
==========

Files
-----

A CGXP interface requires those files::

* ``<package>/template/<interface name>.html``
* ``<package>/template/<interface name>.js``

And an ngeo interface requires those files::

* ``<package>/``
* ``<package>/template/<interface name>.html``
* ``<package>/static-ngeo/js/<interface name>.js``
* ``<package>/static-ngeo/less/<interface name>.less``
* ``<package>/static-ngeo/less/<interface name>-build.less``

Database
--------

The administration interface gives access to an ``interface`` table listing the
available interfaces (or pages) of the application.
The default interfaces are "main", "mobile", "edit" and "routing".

Application init
----------------

The interfaces are added by the following lines in ``<package>/__init__.py``:

.. code:: python

    add_interface(config)
    add_interface(config, 'edit')
    add_interface(config, 'routing')
    add_interface(config, 'mobile', INTERFACE_TYPE_NGEO)


The used method has the following API:

``add_interface(config, interface_name=None, interface_type=INTERFACE_TYPE_CGXP, **kwargs)``:

``config`` is the application configuration object.

``interface_name`` is the name specified in the ``interface`` table,
also used to create the route path.

``interface_type`` may be either ``INTERFACE_TYPE_CGXP``, ``INTERFACE_TYPE_NGEO`` or
``INTERFACE_TYPE_NGEO_CATALOGUE``. Constants available in ``c2cgeoportal``.


Makefile
--------

In the makefile (``<package>.mk``) you can define the variable ``CGXP_INTERFACES`` and
``NGEO_INTERFACES`` that should contain the interfaces lists.

Vars
----

In the ``vars_<package>.yaml`` file:

* ``default_interface`` used to define the default interface.
* ``interfaces`` used to provide the list of interfaces.

JSBuild
-------

For the CGXP interfaces you should have a section in the ``jsbuild/app.cfg.mako`` file
with all the required (plugin) files.
