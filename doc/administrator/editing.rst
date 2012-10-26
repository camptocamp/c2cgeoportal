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

4. The PostGIS table's geometry column should be declared in PostGIS'
   ``geometry_columns`` table, which is typically done using PostGIS'
   `AddGeometryColumn function
   <http://postgis.refractions.net/docs/AddGeometryColumn.html>`_. c2cgeoportal
   indeed queries the ``geometry_columns`` to get the information it needs
   about the geometry columns.
5. If the PostGIS table has a many-to-one relationship to another table
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
    
Configuring security
--------------------

In most cases editable layers are private, i.e. their ``public`` fields are set
to ``false``. This means that some security configuration is required. Layer
security is configured in the ``restrictionarea`` table, which is managed by
selecting the ``Restriction Areas`` item in the admin interface.

For a layer to be actually editable in the editing interface it should have at
least one associated *restriction area*, and this restriction area should have
its ``readwrite`` field set to ``true``.

Some notes:

* By default a restriction areas has its ``readwrite`` fields set to ``false``.
* A restriction area whose ``readwrite`` field is ``true`` applies to both
  ``read`` and ``write`` operations.

Binding restriction areas and layers together can be done from either the
``Restriction Area`` objects or the ``Layer`` objects in the admin interface.
Likewise for binding roles and restriction areas.
