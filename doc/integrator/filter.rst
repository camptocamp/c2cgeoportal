.. _integrator_querier:

Filter (Querier)
================

Filterable layers (public)
--------------------------
Per default, layers are not filterable.
If you wish to provide the filter functionality, proceed as follows:

* Verify your project vars file to make sure that the functionality ``filterable_layers``
  is made available in your project template files:

  - If you have a custom definition for ``functionalities.available_in_templates``
    or ``admin_interface.available_functionalities``, then ensure that the value
    ``filterable_layers`` is contained in both of these.

  - Alternatively, you can add these two paths in the ``update_paths`` variable to use
    the definition provided by ``CONST_vars.yaml`` (and keep the inheritance) instead of replacing it.

* If you wish to provide layers for filtering independently of user authorization (in particular,
  for not-logged-in users), add the layer names as follows to your project vars file:

.. code:: yaml

    functionalities:
        anonymous:
            filterable_layers:
            - my_layer_name_1
            - my_layer_name_2

Filterable layers (private)
---------------------------
* If you wish to provide layers for filtering only for specific user roles, define this in the
  admin interface as follows:

  - Add a functionality ``filterable_layers``; as value provide the GeoMapFish layer name (not the WMS layer name).

  - Edit the role that shall be able to use this filter, and activate the corresponding
    functionality checkbox.

* Note that if there are functionalities associated to a role, then users with this role will
  not have access to any of the "anonymous" functionalities. Instead, you will need to activate
  all functionalities that this role shall be able to use in the admin interface or, for
  functionalities that all registered users shall have access to, via the
  ``functionalities.registered`` variable of your vars file.

Available attributes and operators in filters
---------------------------------------------

All attributes defined as "exported" in the layer of your map server will be automatically available as
filterable attribute. If the type, and so the operator on the attribute, is not adequate for
filtering, you should adapt the type in your layer definition.
See :ref:`administrator_mapfile_wfs_getfeature` for more information (MapServer only).

Enumerate available attributes for a layer
------------------------------------------

Step 1: Project Configuration file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

Step 2: Administration interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can add some additional configuration in the administration interface as follows.

It is possible to define enumerated or directed attributes, to wms layers only, via metadata.
The metadata to look at is ``enumeratedAttributes`` or ``directedFilterAttributes``.

For enumerated attributes, the value is a single string or a list of attributes (that we defined earlier
in the ``vars.yaml`` file) separated with a comma.

For directed attributes, it is a single string or a list of attributes defined in the mapfile
(columns and aliases from the selected table).

The difference is that enumerated attributes are configurable (like pointing to a specific database table),
while directed attributes are ready-to-use values that come directly from the mapfile configuration.

Client-side documentation related to the enumeratedAttributes and directedFilterAttributes metadata is available here:
`gmfThemes.GmfMetaData <https://camptocamp.github.io/ngeo/master/apidoc/gmfThemes.GmfMetaData.html>`_

Using DB sessions
~~~~~~~~~~~~~~~~~

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
