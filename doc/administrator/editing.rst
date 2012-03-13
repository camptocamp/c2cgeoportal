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
   schema though, which is actually recommended.

Adding or making layers editable
--------------------------------

The application's layers are defined in the ``layer`` table, which is managed
by selecting the *Layers* item in the admin interface's menu.

For a *layer* to editable its ``geoTable`` field should be set. This field is the
name of the PostGIS table containing the layer's geographic data.  It is string
of this form: ``[<schemaname>.]<tablename>``.  If ``schemaname`` is omitted
the table is assumed to be in the ``public`` schema.

TODO: add screenshot

Configuring security
--------------------

In most cases editable layers are private, i.e. their ``public`` fields are set
to ``false``. This means that some security configuration is required. Security
is configured in the ``restrictionarea`` table, which is managed by selecting
``Restriction Areas`` in the admin interface's menu.

For a layer to be actually editable through the editing user interface it
should have at least one associated *restriction area*, and this restriction
area's ``mode`` should be either ``write`` or ``both``.

TODO: add screenshot

.. note::

    There are three possible modes for a restriction area: ``read``, ``write``
    or ``both``. Mode ``read`` means that the restriction area applies to read
    operations. Mode ``write`` means that the restriction area applies to write
    operations. Mode ``both`` means that the restriction area applies to both
    read and write operation.

Binding restriction areas and layers together can be done from either the
``Restriction Area`` objects or the ``Layer`` objects in the admin interface.
Likewise for binding roles and restriction areas.
