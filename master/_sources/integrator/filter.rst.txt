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
            defaults: &layers-enum-defaults
                dbsession: "<session name>"
            "<layer_name>":
                dbsession: "<session name>"
                defaults: &layers-enum-table-defaults
                    table: "<[schema.]table name>"
                attributes:
                    "<attribute name>":
                        table: "<[schema.]table name>"
                        column_name: "<column name>"
                        separator: ","
                    <<: *layers-enum-table-defaults
                <<: *layers-enum-defaults

``dbsession: "<session name>"`` at the ``enum.defaults`` level is a shortcut that
may be used if almost all the layers use the same ``dbsession``. It may be
overridden for each layer. If omitted, the main DB session is used.

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

    .. code: javascript

        {
            ptype: "cgxp_querier",
            attributeURLs: ${queryer_attribute_urls | n},
            ...
        },

Using DB sessions
-----------------

As explained above, it is possible to get the attributes lists including
for layers whose data are hosted in external databases, using the
``dbsession: "<session name>"`` parameter.

Such `DB session objects <http://docs.sqlalchemy.org/en/rel_1_0/orm/session_basics.html#getting-a-session>`_
must be listed in the ``DBSessions`` dictionary created in c2cgeoportal
models file. Its default value is:

.. code:: python

    DBSessions = {
        "dbsession": DBSession,
    }

``DBSession`` being the session object linked to the default database.

You may add your own DB session objects in the application's ``models.py`` file.
For instance:

.. code:: python

    from c2cgeoportal.models import DBSessions
    DBSessions['some_db_session_name'] = SomeDbSessionObject
