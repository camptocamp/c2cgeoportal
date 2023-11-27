.. _administrator_editing:

Editing
=======

This section explains how to configure the edit function in c2cgeoportal.

Just like most administrative tasks, setting up editing in a c2cgeoportal application involves intervening
in the database, through the c2cgeoportal administration interface.

Requirements
------------

To be editable, a layer should satisfy the following requirements:

1. It should be accessible with WMS, and correctly configured in the
   mapfile. See :ref:`administrator_mapfile`.
2. Its data should be in a PostGIS table, which should be in the
   application database. The PostGIS table can be in a separate
   schema though, which is in fact recommended.
3. The PostGIS table should include a primary key with a sequence
   associated. The name of the primary key attribute must be ``id``. Example::

       db=# \d table;
                            Table "public.table"
           Column   |      Type   |                              Modifiers
       -------------+-------------+----------------------------------------------------------
        id          | integer     | not null default nextval('public.table_id_seq'::regclass)

4. The PostGIS table should include one geometry column only. You
   will get errors if the table has multiple geometry columns.

5. The following geometry types are fully supported: ``POINT``, ``LINESTRING``, ``POLYGON``.
   The following geometry types are partially supported:
   ``MULTIPOINT``, ``MULTILINESTRING``, ``MULTIPOLYGON``.

6. If the PostGIS table has a many-to-one relationship to another table,
   (typically a dictionary table) there are additional requirements:

   * The name of the foreign key column should end with ``_id`` (e.g.
     ``type_id``). This is not strictly required, but recommended.
   * The relationship's target table should have at least two columns, a
     primary key column and a text column. By default the used text column is the column named ``name``.
     The default order column is the text column. Another text column and a order column can be specified
     by the ``editingEnumerations`` layer metadata. Example:

.. code:: json

   {
       "type_id": {
           "value": "value_column",
           "order_by": "order_column"
       }
   }

7. The supported column types are:

      * ``integer``
      * ``numeric``
      * ``character varying``
      * ``text``
      * ``boolean``
      * ``date``
      * ``time without time zone``
      * ``timestamp without time zone``

   Note that the following types will not working correctly with the timezone:

      * ``time with time zone``
      * ``timestamp with time zone``


.. _administrator_editing_editable:

Adding or making layers editable
--------------------------------

The application's layers are defined in the ``layer`` table, which is managed
by selecting the *Layers* item in the admin interface's menu.

For a *layer* to be editable its ``geoTable`` field should be set. This field
is the name of the PostGIS table containing the layer's geographic data.  It is
a string of the form ``[<schemaname>.]<tablename>``.  If ``schemaname`` is
omitted, the table is assumed to be in the ``public`` schema.  The label
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

Binding restriction areas and layers together can be done from the ``Layer`` objects in the admin interface.
Likewise for binding from the ``Restriction areas``.

Edit views
----------

To be able to edit PostgreSQL views a primary key must be manually configured.
Add a layer metadata ``geotablePrimaryKey`` with value the name of the column to use as primary key.
That column must be of type ``Integer``.

Example: ``geotablePrimaryKey``: ``id``

Enable snapping
---------------

To be able to snap while editing, the ``snappingConfig`` must be set on the layer metadata.
The value is a ``json`` object containing the following optional properties:

* activated (boolean): whether snapping is activated by default (default: true);
* edge (boolean): whether to allow snapping on edges or not;
* vertex (boolean): whether to allow snapping on vertices or not;
* tolerance (number): the pixel tolerance.

Managing attributes
-------------------

To exclude some attributes from the editing form, list them as a comma-separated string
(with no blank spaces) in the ``Exclude properties`` field of the WMS/WMTS layer forms
in the admin interface.

To make some attributes readonly, add a ``readonlyAttributes`` metadata in the same form,
also as a comma-separated list of attributes.
