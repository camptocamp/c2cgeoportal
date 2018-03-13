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
commonly named ``c2cgeoportal.map.mako``.

.. note::

    The application's mapfile is a ``.mako`` file because it contains variables.
    These variables are substituted when the ``make`` build command is
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

* The ``MAP`` and all the ``LAYER``s should have a ``PROJECTION``. For
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

    TEMPLATE "fooOnlyForWFSGetFeature"

This is a fake template, but this is required by the querier and for the filter.

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

  Set this to ``auto``. This means that the layer's field type information is obtained from
  the input feature driver (OGC). If the type is not well interpreted (notably if you have a
  wrong operator within your filter), you can define manually your attribute type
  with ``"gml_<attribute>_type" "<type>"`` where ``<type>`` is one of
  these: ``Integer``, ``Long``, ``Real``, ``Character``, ``Date`` or ``Boolean``.

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

The ``gml_include_items``, ``gml_<geometry name>_type`` and ``gml_geometries``
*METADATA* variables should also be defined in the ``LAYER``. For
example::

    "gml_include_items" "all"
    "gml_geometries" "geom"
    "gml_geom_type" "polygon"

``gml_include_items``

  See above.

``gml_geometries``

  This is a string specifying the name used for geometry elements in
  GetFeatureInfo (GML) responses. This property, and ``gml_<name>_type``,
  should be set for the GetFeatureInfo responses to include the features'
  geometries instead of bboxes.


``gml_<geometry name>_type``

  This specifies the type of a geometry column. Specifying this property is
  necessary if geometries, instead of bboxes should be returned in
  GetFeatureInfo (GML) responses. ``<geometry name>`` should be replaced the string set
  with the ``gml_geometries``. For example, if ``geom_geometries`` is set to
  ``the_geom`` then ``gml_the_geom_type`` should be used.
  The possible values are ``point``, ``multipoint``, ``line``, ``multiline``,
  ``polygon``, ``multipolygon``, if you do not set the right type
  for multi geometries only the first will be visible on the map.
  See also `gml_<geometry name>_type
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

A RestrictionArea is used to restricted the layer displaying to a given area.
This area is specified in the administration interface while defining the
``RestrictionArea`` element.

.. warning::

   Using an restriction area on a big layer or defining a too complex area
   may slow down the application.

To define a restricted layer in the Mapfile the ``DATA`` property of the
``LAYER`` should look like this::

    DATA "the_geom FROM
          (SELECT
             geo.*
           FROM
             <schema>.<table> AS geo
           WHERE
             ST_Contains(
               (${mapfile_data_subselect} '<layername>'),
               ST_SetSRID(geo.<the_geom>, 21781)
             )
          ) as foo using unique id using srid=21781"

``<schema>``, ``<table>``, ``<layername>`` and ``<the_geom>`` need to be
replaced as appropriate. ``<table>`` is the name of the PostGIS table including
the geographic data for this layer. ``<the_geom>`` is the name of the table's
geometry column. ``<schema>`` is the name of the schema including the table.
``<layer_name>`` can be either the layer NAME or the layer GROUP, depending on
what is configured in the admin interface for the layer.

.. note:: The DATA example above is developed on several lines to make it
    easily readable in this documentation. However please note that Mapserver
    requires that this directive is contained on a single line.

.. warning:: In some cases you can have geometries that overlap the restriction
    area. Theses features will not be displayed as they are not in the area (ie not
    *contained*). *st_intersects* or other operator could be used instead of the
    *st_contains* operator.

The ``${mapfile_data_subselect}`` variable is defined in the ``CONST_vars.yaml``
configuration file. Its goal is to simplify the writing of the mapfile.
It is defined as follows:

.. code:: sql

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

Without restriction on the RestrictionArea area
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If we do not need to restrict on an area we can use the following
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

Then you do not need to define an area in the admin interface.

The ``${mapfile_data_noarea_subselect}`` is defined as follows::

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

It is required to have the following in the ``VALIDATION`` section of
the ``LAYER``::

    ${mapserver_layer_validation}

This variable is defined in the ``CONST_vars.yaml`` configuration file
as follows:

.. code::

    mapserver_layer_validation =
        "default_role_id" "-1"
        "role_id" "^-?[0-9]*$$"

The mapfile should be a ``.map.mako`` file, for the variable to be
substituted at make execution time.


Variable Substitution
---------------------

It is possible to adapt some values in the mapfile according to the user's role
by using variable substitution. For instance to hide some layer objects
attributes. The list of parameters that support variable substitution is
available `here <http://mapserver.org/cgi/runsub.html#parameters-supported>`_.

To define variables, edit the matching ``MAP``/``LAYER``/``VALIDATION``
section in the MapFile and add::

    "default_s_<variable>" "<default_value>"
    "s_<variable>" "<validation_pattern>"

The ``validation_pattern`` is a regular expression used to validate the
argument. For example if you only want lowercase characters and commas,
use ``^[a-z,]*$``.

Now in ``LAYER`` place ``%s_<variable>%`` where you want to
insert the variable value, but not at the start of a line (to avoid escape issues).

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
interface with for instance the following value for the given role:
``columns=t.private``.

.. note::

   We also be able to use the ``role_id`` and ``user_id`` as
   variable substitution, but they are not avalable for cached query like:
   ``GetCapabilities``, ``GetLegendGraphic``, ``DescribeFeatureType``.

`MapServer documentation <http://mapserver.org/cgi/runsub.html>`_


Legend
------

Legend text configuration
~~~~~~~~~~~~~~~~~~~~~~~~~

Mapserver allows different forms of legends.

- Legend with legend text (normal configuration, f.e. ``[ o ] Placemark``)::

    CLASS
        NAME "Placemark"
        STYLE
            ...
        END
    END

- Legend without legend text (f.e. ``[ o ]`` , often used if there is one single class in the layer )::

    CLASS
        NAME " "
        STYLE
            ...
        END
    END

  You can set the ``legend rule`` in the admin interface to ``%20``, if you want to show the legend icon in the layer tree

- No legend (do not set any ``NAME`` in the ``CLASS``)::

    CLASS
        STYLE
            ...
        END
    END


Performance improvement
-----------------------

Adding an ``EXTENT`` parameter to the ``LAYER`` section may significantly improve the performances
because it saves MapServer from computing the extent of all layer features.

Prepare raster files
~~~~~~~~~~~~~~~~~~~~

To have good performance you should have tiled files with overview, and probably
a tileindex, you can doing these steps:

Convert your rasters in tiled GeoTIFF:

.. code::

  gdal_translate -of GTiff -co "TILED=YES" -co "TFW=YES" <filename_in.tif> <filename_out.tif>

Then build overviews for your rasters

.. code::

  gdaladdo -r average filename.tif 2 4 8 16

You can generate a shapefile indexing all your rasters

.. code::

  gdaltindex filename_index.shp raster/*.tif

Note about ECW
--------------

In general using ECW is not recommended, as MapServer often generates broken
images and has memory leaks with ECW. See this
`MapServer ticket <http://trac.osgeo.org/mapserver/ticket/3245>`_
for example.

If you still want to use it then replace ``SetHandler fcgid-script``
by ``SetHandler cgi-script`` in the ``apache/mapserver.conf.mako``
file. But note that this affects performance.
