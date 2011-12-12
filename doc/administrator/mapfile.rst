
.. _mapfile:

=====================
Mapfile configuration
=====================

---------------------------------------------------
WFS GetFeature (QueryBuilder and BBOX Query layers)
---------------------------------------------------

* In the mapfile define responsive ``LAYER`` with::

    TEMPLATE fooOnlyForWMSGetFeatureInfo

* And his ``METADATA``::

    "gml_include_items" "all"
    "gml_types" "auto"

* For the BBOX Query layers all the geometry columns should have the same name, ``geom`` by default.
* In the file ``<package>/templates/viewer.js`` update the block fot the QueryBuilder (``cgxp_querier``),
    update the following attribute::

        featureType: "<query_layer>",

    the ``<query_layer>`` is the layer used by the Query builder.

---------------------------------
WMS GetFeatureInfo (Query layers)
---------------------------------

* In the mapfile define the responsive ``LAYER`` with::

    TEMPLATE fooOnlyForWMSGetFeatureInfo

* And his ``METADATA``::

    "gml_include_items" "all"
    "gml_geom_type" "polygon"
    "gml_geometries" "geom"
 
----------------
Restricted layer
----------------

The restricted layers work only with postgres data.
All layer defined as restricted in the ``MapFile`` should be defined as well in the 
admin interface and vice versa.

To define a restricted layer in the ``MapFile`` we should define the ``DATA`` in the ``LAYER`` 
like (in one line)::

    DATA "geometrie FROM (SELECT geo.geom as geom 
        FROM geodata.table AS geo, ${mapserver_join_tables} 
        WHERE ST_Contains(${mapserver_join_area}, geo.geometrie) 
        AND ${mapserver_join_where} 'layer_name') AS foo 
        USING UNIQUE gid USING srid=-1"

And in the METADATA of the layer::

    ${mapserver_layer_metadata}

The important point is to have ``${mapserver_join_tables}`` in the table list,
have ``ST_Contains(${mapserver_join_area}, geo.geometrie)
AND ${mapserver_join_where} '<layer_name>'`` in the where clause to do the 
restriction. The first part is used to filter on the geometry, the second is to
do the table joining and select the right layer.

The metadata section is needed because ``Mapserver 6`` applies a validation with a pattern
for all the variable substitution present in the ``DATA``.

This should be in a .map.in because it uses template variable that is replaced by 
SQL code in the ``MapFile``.

