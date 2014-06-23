.. _administrator_mapfile:

Mapfile configuration
=====================

As mentioned on the index page (:ref:`administrator_guide`) the application
administrator manages the application through the database, and the
application's MapServer mapfile.

The application's mapfile is where WMS and WFS layers are defined.  WMS is used
for the map (``WMS GetMap``), and for the ``point query`` feature (``WMS
GetFeatureInfo``). WFS is used for the ``box query`` and ``query builder``
features (``WFS GetFeature``).

The application's mapfile is located in the ``mapserver`` directory, it is
commonly named ``c2cgeoportal.map.in``.

.. note::

    The application's mapfile is a ``.in`` file because it contains variables.
    These variables are substituted when the ``buildout`` install command is
    executed.

This section describes how to make layers *printable* and/or *queryable*
and/or *private* (a.k.a *restricted*).

.. warning::

    Please note that, because of c2cgeoportal's caching system, each time you
    update the mapfile configuration, you have to reload apache.

    (on debian system, you can do: ``sudo /usr/sbin/apache2ctl graceful``).

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

Layers involved in the ``box query`` and ``query builder`` features should
support WFS GetFeature. To support WFS GetFeature a ``LAYER`` should define
a template::

    TEMPLATE fooOnlyForWFSGetFeature

This is a fake template, but this is required.

The ``LAYER`` should also define metadata, with a ``METADATA`` section. For
example::

    "gml_include_items" "all"
    "gml_types" "auto"
    "gml_featureid" "id"
    "wfs_enable_request" "*"

``gml_include_items``

  This is a comma-delimited list of attribute names, it specifies the list of
  attributes that should be returned in GML responses. ``all`` means that all
  the attributes of the layer should be returned.

``gml_types``

  Always set this to ``auto``. This means that the layer's field type
  information is obtained from the input feature driver (OGC).

``gml_featureid``

  References the name of layer's primary key column. Setting this is mandatory
  for ``GetFeature`` request including ``ogc:FeatureId`` filters. Always set
  it. (This is required for the :ref:`integrator_api`.)

``wfs_enable_request``

  Space separated list of requests to enable. Use ``*``.

.. warning::

    The geometry columns of layers involved in ``box query`` should have the
    same name. By default the WFS GetFeatue CGXP plugin
    (``cgxp_wfsgetfeature``) assumes the name is ``geom``, but the plugin
    can be configured to use a different name.

In contrast to WMS GetFeatureInfo, WFS GetFeature supports ``point query`` as
well as ``box query`` (i.e. drawing a box and getting information about the
features with that box). However, it is to be noted that WFS GetFeature may
return features that are not visible at the current resolution of the map.
This is because a limitation in MapServer, where ``MINSCALE``/``MAXSCALE``
values defined in the layer's classes (``CLASS``) have no effect.

WMS GetFeatureInfo
------------------

Layers involved in the ``point query`` feature should support WMS
GetFeatureInfo.

To support WMS GetFeatureInfo a ``LAYER`` should define a template::

    TEMPLATE fooOnlyForWMSGetFeatureInfo

As for WFS GetFeature, this is a fake template, but it is required.

The ``gml_include_items``, ``gml_[geometry name]_type`` and ``gml_geometries``
*METADATA* variables should also be defined in the ``LAYER``. For
example::

    "gml_include_items" "all"
    "gml_geometries" "geom"
    "gml_geom_type" "polygon"

``gml_include_items``

  See above.

``gml_geometries``

  This is a string specifying the name used for geometry elements in
  GetFeatureInfo (GML) responses. This property, and ``gml_[name]_type``,
  should be set for the GetFeatureInfo responses to include the features'
  geometries instead of bboxes.


``gml_[geometry name]_type``

  This specifies the type of a geometry column. Specifying this property is
  necessary if geometries, instead of bboxes should be returned in
  GetFeatureInfo (GML) responses. ``[geometry name]`` should be replaced the string set
  with the ``gml_geometries``. For example, if ``geom_geometries`` is set to
  ``the_geom`` then ``gml_the_geom_type`` should be used.
  The possible values are ``point``, ``multipoint``, ``line``, ``multiline``,
  ``polygon``, ``multipolygon``, if you don't set the right type
  for multi geometries only the first will be visible on the map.
  See also `gml_[geometry name]_type
  <http://mapserver.org/ogc/wms_server.html#index-71>`_.

See the `WMS Server MapFile Documentation
<http://mapserver.org/ogc/wms_server.html>`_ for more detail.

Restricted layer
----------------

The restricted layers work only with postgres data.  All layer defined as
restricted in the mapfile should be defined as well in the admin interface
and vice versa.

With a RestrictionArea area
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To define a restricted layer in the mapfile the ``DATA`` property of the
``LAYER`` should look like this::

    DATA "the_geom FROM
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
``<layer_name>`` can be either the layer NAME or the layer GROUP, depending on
what's configured in the admin interface for the layer.

.. note:: The DATA example above is developed on several lines to make it
    easily readable in this documentation. However please note that Mapserver
    requires that this directive is contained on a single line.

.. warning:: In some cases you can have geometries that overlap the restriction
	area. Theses features won't be displayed as they are not in the area (ie not
	*contained*). *st_intersects* or other operator could be used instead of the
	*st_contains* operator.

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

        DATA "geometry FROM (SELECT geo.geom as geom
            FROM geodata.table AS geo, ${mapserver_join_tables}
            WHERE ST_Contains(${mapserver_join_area}, geo.geometry)
            AND ${mapserver_join_where} 'layer_name') AS foo
            USING UNIQUE gid USING srid=-1"

    In most cases this query should continue to work with 0.6 and
    higher, but changing to the new query is recommended.

Without restriction on the RestrictionArea area
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If we don't need to restrict on an area we can use the following
``DATA`` property of the ``LAYER``::

    DATA "the_geom FROM (
        SELECT
            geo.*
        FROM
            <schema>.<table> AS geo
        WHERE (
            %role_id% IN (
                ${mapfile_data_noarea_subselect} '<layername>'
            )
        )
    ) AS foo USING UNIQUE id USING srid=21781"

Then you don't need to define an area in the admin interface.

The ``${vars:mapfile_data_noarea_subselect}`` is defined as follows::

    SELECT
        rra.role_id
    FROM
        main.restrictionarea AS ra,
        main.role_restrictionarea AS rra,
        main.layer_restrictionarea AS lra,
        main.treeitem AS la
    WHERE
        rra.restrictionarea_id = ra.id
    AND
        lra.restrictionarea_id = ra.id
    AND
        lra.layer_id = la.id
    AND
        la.name =

Metadata and filename
~~~~~~~~~~~~~~~~~~~~~

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

It is possible to adapt some values in the mapfile according to the user's role
by using variable substitution. For instance to hide some layer objects
attributes. The list of parameters that support variable substitution is
available `here <http://mapserver.org/cgi/runsub.html#parameters-supported>`_.

To define variables, edit the matching ``MAP``/``LAYER``/``METADATA``
section in the mapfile and add::

    "default_s_<variable>" "<default_value>"
    "s_<variable>_validation_pattern" "<validation_pattern>"

The ``validation_pattern`` is a regular expression used to validate the
argument. For example if you only want lowercase characters and commas,
use ``^[a-z,]*$$`` (the double '$' is needed since we are
in a ``.in`` file).

.. note::
 
     For MapServer above 6.0, you must place the value and the pattern definition
     in a VALIDATION section instead of the METADATA block::

        VALIDATION
            "default_s_<variable>" "<default_value>"
            "s_<variable>" "<validation_pattern>"
        END

     VALIDATION block can be used within a CLASS, a LAYER or a WEB block.

Now in ``LAYER`` place ``%s_<variable>%`` where you want to
insert the variable value.

Then in the administration interface, create a ``functionality`` named
``mapserver_substitution`` with the value: ``<variable>=<value>``.

Please note that we cannot use substitution in the ``MATADATA`` values.
As a result, if you would like to adapt the list of attributes returned in a
WFS GetFeature or WMS GetFeatureInfo request, you have to adapt the columns
listed in the ``DATA`` section. For instance::

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

Then add a ``mapserver_substitution`` functionality in the administration
interface with for instance the following value for tthee given role:
``columns=t.private``.

`MapServer documentation <http://mapserver.org/cgi/runsub.html>`_

Note about ECW
--------------

In general using ECW is not recommended, as MapServer often generates broken
images and has memory leaks with ECW. See this
`MapServer ticket <http://trac.osgeo.org/mapserver/ticket/3245>`_
for example.

If you still want to use it then replace ``SetHandler fcgid-script``
by ``SetHandler cgi-script`` in the ``apache/mapserver.conf.in``
file. But note that this affects performance.
