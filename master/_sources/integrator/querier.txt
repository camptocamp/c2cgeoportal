.. _integrator_querier:

Query builder (Querier)
=======================

In the Query builder interface, instead of the standard text field,
it is possible to display combos providing the available values of
the attributes. The values are automatically retrieved using a
web service that does a ``SELECT distinct(<column>) FROM <table>``.

The web service configuration is done in the ``vars_<project>.yaml`` file:

.. code:: yaml

    layers:
        enum:
            dbsession: "<session name>"
            "<layer_name>":
                dbsession: "<session name>"
                table: "<[schema.]table name>"
                attributes:
                    "<attribute name>":
                        table: "<[schema.]table name>"
                        column_name: "<column name>"
                        separator: ","

``dbsession: "<session name>"`` at the ``enum`` level is a shortcut that
may be used if almost all the layers use the same ``dbsession``. It may be
overridden for each layer. If omitted, the main DB session is used.

``table: "<[schema.]table name>"`` may be used at the layer level as a the default
table where following attributes may be found. It can be overridden at the
attribute level. ``table`` is a mandatory parameter.

If ``column_name`` is not defined, the attribute name is used.

If ``separator`` is defined, the column is considered as a list of values.

Simple example:

.. code:: yaml

    layers
        enum:
            mapserver_layer:
                table: geodata.table
                attributes:
                    type:
                    country:

Make sure that the ``cgxp_querier`` plugin has the attribute ``attributeURLs``
in the ``viewer.js`` file:

.. code: javascript

    {
        ptype: "cgxp_querier",
        attributeURLs: ${queryer_attribute_urls | n},
        ...
    },
