.. _integrator_querier:

Query builder (Querier)
=======================

In the Query builder interface, instead of the standard text field,
it is possible to display combos providing the available values of
the attributes. The values are automatically retrieved using a
web service that does a ``SELECT dinstinct(<column>) FROM <table>``.

The web service configuration is done in the ``config.yaml.in`` file:

.. code:: yaml

    layers_enum:
        dbsession: "<session name>"
        "<layer_name>":
            dbsession: "<session name>"
            table: "<[schema.]table name>"
            attributes:
                "<attribute name>":
                    table: "<[schema.]table name>"
                    column_name: "<column name>"
                    separator: ","

The ``dbsession: "<session name>"`` in the ``layers_enum`` is just a shortcut
if almost of the session are similar in the layers. If the dbsession isn't
defined we use the main DB session.

The ``table: "<[schema.]table name>"`` in the layer is just a shortcut
if almost of the attribute of the layer are in the same table.
Each attributes requires a table.

If the ``column_name`` isn't defined we use the attribute name.

If the ``separator`` is defined we consider the column as a list of values.

Simple example:

.. code:: yaml

    layers_enum:
        mapserver_layer:
            table: geodata.table
            attributes:
                type:
                country:

Make sure that the ``cgxp_querier`` plugin has the attribute ``attributeURLs``
the ``viewer.js``:

.. code: javascript

    {
        ptype: "cgxp_querier",
        attributeURLs: ${queryer_attribute_urls | n},
        ...
    },
