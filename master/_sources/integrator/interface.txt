.. _integrator_interface:

Interfaces
----------

The administration interface gives access to an ``interface`` table listing the
available interfaces (or pages) of the application.
The default interfaces are "main", "mobile", "edit" and "routing".

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
