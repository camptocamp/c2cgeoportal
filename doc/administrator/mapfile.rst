.. _administrator_mapfile:

Mapfile configuration
=====================

As mentioned on the index page (:ref:`administrator_guide`) the application
administrator manages the application through the database, and the
application's MapServer mapfile.

The application's MapServer mapfile is where WMS and WFS layers are defined.
WMS is used for the map (``WMS GetMap``), and for the ``point query`` feature
(``WMS GetFeatureInfo``). WFS is used for the ``box query`` and ``query
builder`` features (``WFS GetFeature``).

The application's mapfile is located in the ``mapserver`` directory, it is
commonly named ``c2cgeoportal.map.in``.

.. note::

    The application's mapfile is a ``.in`` file because it contains variables.
    These variables are substituted when the ``buildout`` install command is
    executed.

This section provides information on how to configure *private layers* (a.k.a
*restricted layers*), and layers involved in ``point query``, ``box query``,
``query builder`` features.

WFS GetFeature
--------------

Layers involved in the ``box query`` and ``query builder`` features must
support WFS GetFeature.

To support WFS GetFeature a ``LAYER`` should define a template::

    TEMPLATE fooOnlyForWFSGetFeature

This is a fake template, but this is required.

And it should have the following ``METADATA``::

    "gml_include_items" "all"
    "gml_types" "auto"

.. warning::

    The geometry columns of layers involved in ``box query`` should have
    the same name, ``geom`` by default.

.. note::

    The query builder works with one layer only. The name of the ``LAYER`` in
    the mapfile and the name passed in the ``featureType`` property to the
    querier CGXP plugin (``cgxp_querier``) must match.

WMS GetFeatureInfo
------------------

Layers involved in the ``point query`` feature must support WMS GetFeatureInfo.

To support WMS GetFeatureInfo a ``LAYER`` should define a template::

    TEMPLATE fooOnlyForWMSGetFeatureInfo

As for WFS GetFeature, this is a fake template, but it is required.

And it should have the following ``METADATA``::

    "gml_include_items" "all"
    "gml_geom_type" "polygon"
    "gml_geometries" "geom"
 
Restricted layer
----------------

The restricted layers work only with postgres data.  All layer defined as
restricted in the mapfile should be defined as well in the admin interface
and vice versa.

To define a restricted layer in the mapfile we should define the ``DATA``
in the ``LAYER`` like (in one line)::

    DATA "geometrie FROM (SELECT geo.geom as geom 
        FROM geodata.table AS geo, ${mapserver_join_tables} 
        WHERE ST_Contains(${mapserver_join_area}, geo.geometrie) 
        AND ${mapserver_join_where} 'layer_name') AS foo 
        USING UNIQUE gid USING srid=-1"

And in the METADATA of the layer::

    ${mapserver_layer_metadata}

The important point is to have ``${mapserver_join_tables}`` in the table list,
have ``ST_Contains(${mapserver_join_area}, geo.geometrie) AND
${mapserver_join_where} '<layer_name>'`` in the where clause to do the
restriction. The first part is used to filter on the geometry, the second is to
do the table joining and select the right layer.

The metadata section is needed because MapServer 6  applies a validation
with a pattern for all the variable substitution present in the ``DATA``.

This should be in a .map.in because it uses template variable that is replaced
by SQL code in the mapfile.


Recommended
-----------

To have a good print and screen result it's not recommand to use
LAYER/SYMBOLSCALEDENOM. LABEL/MINSIZE and LABEL/MAXSIZE should be use only 
when necessary.

