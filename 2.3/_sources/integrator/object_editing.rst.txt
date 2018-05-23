.. _integrator_objectediting:

ObjectEditing
=============

This section describes how to set up editing for one feature at a time in
c2cgeoportal applications.
It is accessed via a URL defining the feature and the layer to edit, and
opens an object-editing interface which centers on the feature. The feature
can then be edited and saved.

Requirements
------------

This feature is available only in NGEO.
The layer has to be editable (see :ref:`administrator_editing`).
The user has to have the right to edit it (already logged in or using login
via URL, see :ref:`integrator_urllogin`).

Access via URL
--------------

The following parameters can be set in the URL and allow to use the
ObjectEditing interface available under /oeedit :

    * objectediting_geomtype: MultiPolygon
    * objectediting_layer: the layer ID from the Admin Interface
    * objectediting_theme: the theme name (untranslated) from the Admin Interface
    * objectediting_property: the key for searching the feature in the database
    * objectediting_id: the value of the key for searching the feature in
      the database. If not found, a new feature with this value will be created.

Features
--------

    * Access a feature via a URL, center on it if it exists.
    * Editing of this one feature (only one).
        * No tool chosen: Change the feature
        * Plus-tool chosen: Add new parts to the feature (supports
          multi-point, multi-line, multi-polygon)
        * Minus-tool chosen: Remove parts from the feature
        * Triangle-tool chosen: Draw a fixed-sized by clicking on the map
        * Copy from: Copy a geometry from another layer. The layer needs WFS
          and a copyable Metadata.
        * Cut from: Cut the feature with a geometry from another layer. The
          layer needs WFS and a copyable Metadata.
    * FeatureQuery showing a FeatureWindow
