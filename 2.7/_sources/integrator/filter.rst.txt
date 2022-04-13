.. _integrator_querier:

Filter (Querier)
================

Filterable layers
-----------------

Per default, layers are not filterable.
If you wish to provide filter functionality for some layers, proceed as follows:

* For each layer you want to be filtrable create a functionality record with ``filterable_layers`` as name
  and the layer name as value.
* In any role (anonymous, registered, intranet or any other role) check the corresponding functionality records.

.. note::

    Ngeo offers the filter functionality only for single layers, not for grouped layers.


Available attributes and operators in filters
---------------------------------------------

All attributes defined as "exported" in the layer of your map server will be automatically available as
filterable attribute. If the type, and so the operator on the attribute, is not adequate for
filtering, you should adapt the type in your layer definition.
See :ref:`administrator_mapfile_wfs_getfeature` for more information (MapServer only).


Enumerate available attributes for a layer
------------------------------------------

Project Configuration file
~~~~~~~~~~~~~~~~~~~~~~~~~~

In the filter panel, instead of the standard text field, it is possible to display combos providing the
available values of the attributes. The values are automatically retrieved using a web service that does a
``SELECT distinct(<column>) FROM <table>``.

The web service configuration is done in the ``vars.yaml`` file:

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

If ``separator`` is defined, the column is treated as a list of values.

Example:

.. code:: yaml

    layers
        enum:
            mapserver_layer:
                attributes:
                    type: &layers-enum-mapserver-layer-defaults
                        table: geodata.table
                    country: *layers-enum-mapserver-layer-defaults


Administration interface
~~~~~~~~~~~~~~~~~~~~~~~~

You can add some additional configuration in the administration interface as follows.

It is possible to define enumerated or directed attributes, to WMS layers only, via metadata.
The metadata to define is ``enumeratedAttributes`` or ``directedFilterAttributes``.

For enumerated attributes, the value is a single string or a list of attributes (that we defined earlier
in the ``vars.yaml`` file) separated with a comma.

For directed attributes, it is a single string or a list of attributes defined in the mapfile
(columns and aliases from the selected table).

The difference is that enumerated attributes are configurable (like pointing to a specific database table),
while directed attributes are ready-to-use values that come directly from the mapfile configuration.

Client-side documentation related to the ``enumeratedAttributes`` and ``directedFilterAttributes`` metadata
is available here: :ngeo_doc:`gmfThemes.GmfMetaData </apidoc/gmfThemes.GmfMetaData.html>`.

Using DB sessions
~~~~~~~~~~~~~~~~~

It is possible to get attribute lists also
for a layer whose data is hosted in an external database, using the
``dbsession: "<session name>"`` parameter.

See :ref:`integrator_multiple_databases` for more information.
