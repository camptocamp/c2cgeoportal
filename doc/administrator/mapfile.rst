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

Print
-----

MapFish Print does single tile requests to the WMS server. For that reason we
need to use a relatively large value for the ``MAXSIZE`` parameter (of the
``MAP`` section); 5000 for example.

MapFish Print also supports map rotations. This implies specific requirements:

* The ``MAP`` and all the ``LAYERS`` should have a ``PROJECTION``. For
  example::

      PROJECTION
          "init=epsg:21781"
      END
* When rotating the map (with a non-zero value for ``ANGLE``) there are
  important things to be aware of. Make sure to read the notes for the
  ``ANGLE`` parameter on http://mapserver.org/mapfile/map.html.

MapFish Print uses a resolution of 254 dpi (instead of 72 dpi as used for the
web application on the screen). Using ``LAYER``/``SYMBOLSCALEDENOM`` is
therefore not recommended. ``LABEL``/``MINSIZE`` and ``LABEL``/``MAXSIZE``
should be used when necessary only, as these parameters do not take the ``MAP``
resolution into account.

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
    "wfs_enable_request" "*"

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

To define a restricted layer in the mapfile the ``DATA`` property of the
``LAYER`` should look like this::

    DATA "the_geom from
          (SELECT
             geo.*
           FROM
             <schema>.<table> AS geo
           WHERE
             ST_Contains(
               (${vars:mapfile_data_subselect} '<layername>'),
               ST_SetSRID(geo.<the_geom>, 21781)
             )
          ) as foo using unique id using srid=21781"

``<schema>``, ``<table>``, ``<layername>`` and ``<the_geom>`` need to be
replaced as appropriate. ``<table>`` is the name of the PostGIS table including
the geographic data for this layer. ``<the_geom>`` is the name of the table's
geometry column. ``<schema>`` is the name of the schema including the table.
``layer_name`` is the name of this layer as defined with the ``NAME`` property.

The ``${vars:mapfile_data_subselect}`` variable is defined in the Buildout
configuration file (``CONST_buildout.cfg``). Its goal is to simplify the
writing of the mapfile. It is defined as follows::

    SELECT
      ST_Collect(ra.area)
    FROM
      main.restrictionarea AS ra,
      main.role_restrictionarea AS rra,
      main.layer_restrictionarea AS lra,
      main.treeitem AS la
    WHERE
      rra.role_id = %role_id%
    AND
      rra.restrictionarea_id = ra.id
    AND
      lra.restrictionarea_id = ra.id
    AND
      lra.layer_id = la.id
    AND
      la.name = 

.. note::


    Before c2cgeoportal 0.6 the following ``DATA`` query was given
    in this documentation::

        DATA "geometrie FROM (SELECT geo.geom as geom 
            FROM geodata.table AS geo, ${mapserver_join_tables} 
            WHERE ST_Contains(${mapserver_join_area}, geo.geometrie) 
            AND ${mapserver_join_where} 'layer_name') AS foo 
            USING UNIQUE gid USING srid=-1"

    In most cases this query should continue to work with 0.6 and
    higher, but changing to the new query is recommended.

It is required to have the following in the ``METADATA`` of the ``LAYER``::

    ${mapserver_layer_metadata}

This variable is defined in the Buildout configuration file as*
follows::

    mapserver_layer_metadata =
        "default_role_id" "-1"
        "role_id_validation_pattern" "^-?[0-9]*$$"

The metadata section is needed because MapServer 6  applies a validation
with a pattern for all the variable substitution present in the ``DATA``.

The mapfile should be a ``.map.in`` file, for the Buildout variable to be
substituted at Buildout execution time.


Variable Substitution
---------------------

We can use the substitution to for example hide some attributes
for sub role.

To do that you should edit your MapFile in the ``MAP``/``LAYER``/``METADATA``
section and add::

    "default_s_<variable>" "<default_value>"
    "s_<variable>_validation_pattern" "<validation_pattern>"

The ``validation_pattern`` is a regular expression to validate the argument,
for example if you want only lowercase char and coma it can be ``^[a-z,]*$$``
(the double '$' is needed is we are in a ``.in`` file).

Now in the ``LAYER`` you can use ``%s_<variable>%`` where you want the
value.

Than in the admin interface you can create a Functionality named
``mapserver_substitution`` with the value: ``<variable>=<value>``.

Unfortunately we can't use substitution in the ``MATADATA`` values than
in ours example we can do columns restriction on a ``LAYER``,
with the variable ``columns``, with the defaut visible column:
``name``::

    LAYER
        ...
        DATA "geom FROM (SELECT t.geom, t.type, t.gid, %s_columns% FROM geodata.table as t)  AS foo using unique gid using SRID=21781"
        METADATA
            ...
            "gml_exclude_items" "type,gid"
            "gml_include_items" "all"
            "default_s_columns" "t.name"
            "s_columns_validation_pattern" "^[a-z,._]*$$"
        END
        CLASS
            EXPRESSION ([type]=1)
            ...
        END
        ...
    END

In the admin interface we can allow a role to access to the columns name and private
by liked it to the ``mapserver_substitution`` functionnalities ``columns=t.name``
and ``columns=t.private``.

`MapServer documentation <http://mapserver.org/cgi/runsub.html>`_
