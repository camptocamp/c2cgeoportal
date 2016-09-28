.. _administrator_editing:

Editing
=======

This section describes how to set up feature editing in c2cgeoportal
applications.

Just like most administrative tasks setting up editing in a c2cgeoportal
application involves intervening in the database, through the c2cgeoportal
administration interface.

Requirements
------------

To be editable a layer should satisfy the following requirements:

1. It should be accessible with WMS, and correctly configured in the
   mapfile. See :ref:`administrator_mapfile`.
2. Its data should be in a PostGIS table, which should be in the
   application database. The PostGIS table can be in a separate
   schema though, which is even recommended.
3. The PostGIS table should include a primary key with a sequence
   associated. Example::

       db=# \d table;
                            Table "public.table"
           Column   |      Type   |                              Modifiers
       -------------+-------------+----------------------------------------------------------
        id          | integer     | not null default nextval('public.table_id_seq'::regclass)

4. The PostGIS table should include one geometry column only. You
   will get errors if the table has multiple geometry columns, even
   if one of them only is declared in PostGIS' ``geometry_columns``
   table.

5. The PostGIS table's geometry column should be declared in PostGIS'
   ``geometry_columns`` table. c2cgeoportal indeed queries the
   ``geometry_columns`` table to get the information it needs.

   .. note::

       Creating a geometry column and populating ``geometry_columns`` is
       typically done using the `AddGeometryColumn function
       <http://postgis.net/docs/AddGeometryColumn.html>`_.  The
       `Populate_Geometry_Columns function
       <http://postgis.net/docs/Populate_Geometry_Columns.html>`_ can also be
       useful for registering already created geometry columns in
       ``geometry_columns``.

   .. note::

       The following geometry types are supported:
       POINT, LINESTRING, POLYGON
       The following geometry types are partially supported:
       MULTIPOINT, MULTILINESTRING, MULTIPOLYGON


6. If the PostGIS table has a many-to-one relationship to another table
   (typically a dictionary table) there are additional requirements:

   * The name of the foreign key column should end with ``_id`` (e.g.
     ``type_id``). This is not strictly required, but recommended.
   * The relationship's target table should have two columns, a
     primary key column and a text column. The text column must
     be named ``name``.


Adding or making layers editable
--------------------------------

The application's layers are defined in the ``layer`` table, which is managed
by selecting the *Layers* item in the admin interface's menu.

For a *layer* to be editable its ``geoTable`` field should be set. This field
is the name of the PostGIS table containing the layer's geographic data.  It is
string of the form ``[<schemaname>.]<tablename>``.  If ``schemaname`` is
omitted the table is assumed to be in the ``public`` schema.  The label
corresponding to this field is *Related Postgres table* in the admin interface.

.. warning::

    Only layers embedded in a layergroup are detected as editable.

.. warning::

    It is recommended to limit the editing to 30 editable layers per user.


Configuring security
--------------------

Editing the features of a layer implies to write changes in the database. To make
sure that only authorized users may edit a feature, editable layers (including
public layers) must be linked to a restriction area, used itself to specify the
roles of authorized users.

The restriction area should have its ``readwrite`` field set to ``true`` in the
administration interface.

.. note::

    * By default a restriction areas has its ``readwrite`` field set to ``false``.
    * A restriction area whose ``readwrite`` field is ``true`` applies to both
      ``read`` and ``write`` operations.

Binding restriction areas and layers together can be done from either the
``Restriction Area`` objects or the ``Layer`` objects in the admin interface.
Likewise for binding roles and restriction areas.


Enabling `Copy to` functionality
--------------------------------

In the ``edit`` interface, you can give the user the possibility to copy
features from one layer (source layer) to another layer (destination layer).

In the ``admin`` interface, open the ``UI metadatas`` list and add a new record:

    * Name: Select ``copy_to``.
    * Value: Enter the list of choices for destination layer, as mapserver
      layer names, separated by commas.
    * Item: Select the source layer.

Exemple:

    * Name: ``copy_to``
    * Value: ``polygon2,polygon3,polygon4``
    * Item: ``polygon``

.. note::

   * Source and destination layers must have the same geometry type.
   * Only the geometry will be copied, the attributes will not be.
