.. _integrator_querier:

Filter (Querier)
================

Configuration
-------------

In the filter panel, instead of the standard text field,
it is possible to display combos providing the available values of
the attributes. The values are automatically retrieved using a
web service that does a ``SELECT distinct(<column>) FROM <table>``.

The web service configuration is done in the ``vars_<project>.yaml`` file:

.. code:: yaml

    layers:
        enum:
            <layer_name>:
                dbsession: <session name>
                attributes:
                    <attribute name>:
                        table: <[schema.]table name>
                        column_name: <column name>
                        separator: ","

``dbsession: "<session name>"`` at the ``enum.defaults`` level can be used
to specify another DB session than the main DB session.
See :ref:`integrator_multiple_databases` regarding the setup of multiple databases.
If omitted, the main DB session is used.

``table: "<[schema.]table name>"`` may be used at the layer ``defaults`` level as a the default
table where following attributes may be found. It can be overridden at the
attribute level. ``table`` is a mandatory parameter.

If ``column_name`` is not defined, the attribute name is used.

If ``separator`` is defined, the column is considered as a list of values.

Simple example:

.. code:: yaml

    layers
        enum:
            mapserver_layer:
                attributes:
                    type: &layers-enum-mapserver-layer-defaults
                        table: geodata.table
                    country: *layers-enum-mapserver-layer-defaults

.. note::

    If you use cgxp, make sure that the ``cgxp_querier`` plugin has
    the attribute ``attributeURLs`` in the ``viewer.js`` file:

    .. code:: javascript

        {
            ptype: "cgxp_querier",
            attributeURLs: ${queryer_attribute_urls | n},
            ...
        },
