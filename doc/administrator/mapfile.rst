.. _administrator_mapfile:

Mapfile configuration
=====================

As mentioned on the index page (:ref:`administrator_guide`), the application
administrator manages the application through the database and via
the application's MapServer mapfile.

The application's mapfile is where WMS and WFS layers are defined.  WMS is used
for the map (``WMS GetMap``), and for the ``point query`` feature (``WMS GetFeatureInfo``).
WFS is used for the ``query`` (box and point), the ``filters``, and the WFS permalink features.

The application's mapfile is located in the ``mapserver`` directory, it is
commonly named ``mapserver.map.tmpl``.

.. note::

    The application's mapfile is a ``.tmpl`` file because it contains variables.
    These variables are substituted at container start.

This section describes how to make layers *printable* and/or *queryable*
and/or *private* (a.k.a *restricted*).

Print
-----

MapFish Print performs single tile requests to the WMS server. For that reason, we
need to use a relatively large value for the ``MAXSIZE`` parameter (of the
``MAP`` section); 5000 for example.

MapFish Print also supports map rotations. This implies specific requirements:

* The ``MAP`` and all the ``LAYER`` definitions should have a ``PROJECTION``. For
  example:

  .. code::

      PROJECTION
          "init=epsg:2056"
      END

* When rotating the map (with a non-zero value for ``ANGLE``) there are
  important things to be aware of. Make sure to read the notes for the
  ``ANGLE`` parameter on https://mapserver.org/mapfile/map.html.

MapFish Print uses a resolution of 254 dpi (instead of 72 dpi as used for the
web application on the screen). Using ``LAYER``/``SYMBOLSCALEDENOM`` is
therefore not recommended. ``LABEL``/``MINSIZE`` and ``LABEL``/``MAXSIZE``
should be used when necessary only, as these parameters do not take the ``MAP``
resolution into account.

.. _administrator_mapfile_wfs_getfeature:

WFS GetFeature
--------------

Layers that you want to use in a query (box and point), in filters, or for WFS permalink features must
support WFS GetFeature.
To support WFS GetFeature a ``LAYER`` should define a template:

.. code::

    TEMPLATE "fooOnlyForWFSGetFeature"

This is a fake template, but this is required by the querier and for the filter.

The ``LAYER`` should also define metadata, with a ``METADATA`` section. For example:

.. code::

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

    The geometry columns of layers involved in ``query`` should have the same name.
    By default the ``filters`` assumes the name is ``geom``.

In contrast to WMS GetFeatureInfo, WFS GetFeature supports ``point query`` as
well as ``box query``. However, it is to be noted that WFS GetFeature may
return features that are not visible at the current resolution of the map.
This is because of a limitation in MapServer, where ``MINSCALE``/``MAXSCALE``
values defined in the layer's classes (``CLASS``) have no effect.

WMS GetFeatureInfo
------------------


To support WMS GetFeatureInfo, a ``LAYER`` should define a template:

.. code::

    TEMPLATE fooOnlyForWMSGetFeatureInfo

Similar to WFS GetFeature, this is a fake template, but it is required.

The ``gml_include_items``, ``gml_<geometry name>_type`` and ``gml_geometries``
*METADATA* variables should also be defined in the ``LAYER``. For example:

.. code::

    "gml_include_items" "all"
    "gml_geometries" "geom"
    "gml_geom_type" "polygon"

``gml_include_items``

  See above.

``gml_geometries``

  This is a string specifying the name used for geometry elements in
  GetFeatureInfo (GML) responses. This property, and ``gml_<name>_type``,
  should be set for the GetFeatureInfo responses to include the features' geometries instead of bboxes.


``gml_<geometry name>_type``

  This specifies the type of a geometry column. Specifying this property is
  necessary if geometries, instead of bboxes, should be returned in
  GetFeatureInfo (GML) responses. ``<geometry name>`` should be replaced by the string set
  with the ``gml_geometries``. For example, if ``geom_geometries`` is set to
  ``the_geom``, then ``gml_the_geom_type`` should be used.
  The possible values are ``point``, ``multipoint``, ``line``, ``multiline``,
  ``polygon``, ``multipolygon``. If you do not set the right type
  for multi geometries, only the first will be visible on the map.
  See also `gml_<geometry name>_type
  <https://mapserver.org/ogc/wms_server.html#index-71>`_.

See the `WMS Server MapFile Documentation <https://mapserver.org/ogc/wms_server.html>`_ for more detail.

.. note::

  A layer with no interrogation template will not be queried by GeoMapFish and can be used to avoid
  performance issue on layers like labels.

Restricted layer
----------------

The restricted layers work only with PostgreSQL data.  All layers defined as restricted in the mapfile
should be defined as well in the administration interface and vice versa.

With a RestrictionArea area
~~~~~~~~~~~~~~~~~~~~~~~~~~~

A RestrictionArea is used to restrict the layer displaying to a given area.
This area is specified in the administration interface while defining the ``RestrictionArea`` element.

.. warning::

   Using a restriction area on a big layer or defining a very complex area
   may slow down the application.

To define a restricted layer in the Mapfile, the ``DATA`` property of the ``LAYER`` should look like this:

.. code:: sql

    DATA "<the_geom> FROM (
        SELECT *
        FROM <schema>.<table>
        WHERE ST_Contains(
           (${MAPSERVER_DATA_SUBSELECT} '<layername>'),
           ST_SetSRID(<the_geom>, <projection>)
         )
    ) as foo USING unique gid USING srid=<projection>"

``<schema>``, ``<table>``, ``<layername>``, ``<projection>`` and ``<the_geom>``
need to be replaced as appropriate. ``<table>`` is the name of the PostGIS table
including the geographic data for this layer. ``<the_geom>`` is the name of the
table's geometry column. ``<schema>`` is the name of the schema including the table.
``<layer_name>`` can be either the layer NAME or the layer GROUP, depending on
what is configured in the administration interface for the layer.

The ``${MAPSERVER_DATA_SUBSELECT}`` is defined as follows:

.. code:: sql

    SELECT
        rra.role_id
    FROM
        <main_schema>.restrictionarea AS ra,
        <main_schema>.role_restrictionarea AS rra,
        <main_schema>.layer_restrictionarea AS lra,
        <main_schema>.treeitem AS la
    WHERE
        rra.restrictionarea_id = ra.id
    AND
        lra.restrictionarea_id = ra.id
    AND
        lra.layer_id = la.id AND la.name =

.. warning::

    In some cases you can have geometries that overlap the restriction
    area. These features will not be displayed as they are not in the area (ie not
    *contained*). *st_intersects* or another operator could be used instead of the
    *st_contains* operator.

It is required to have the following in the ``VALIDATION`` section of the ``LAYER``:

.. code::

   VALIDATION
     # For secured layers
     "default_role_ids" ""
     # Or
     # "default_role_ids" "<id of the anonymous role>"
     "role_ids" "^-?[0-9,]*$"
   END

The ``default_role_ids`` define the restrictions when mapserver is called without any ``roles_ids``.
In this situation, if you have set ``default_role_ids`` to an empty value for this layer, then there is
no access; if you have set ``default_role_ids`` to the anonymous role id, then the access rights of
anonymous users apply.


Without restriction on the RestrictionArea area
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If we do not need to restrict on an area, we can use the following
``DATA`` property of the ``LAYER``::

    DATA "the_geom FROM (
        SELECT
            geo.*
        FROM
            <schema>.<table> AS geo
        WHERE (
            ARRAY[%role_ids%]::integer[] && ARRAY(
                ${MAPSERVER_DATA_NOAREA_SUBSELECT} '<layername>'
            )
        )
    ) AS foo USING unique id USING srid=2056"

Then you do not need to define an area in the admin interface.

The ``${MAPSERVER_DATA_NOAREA_SUBSELECT}`` is defined as follows:

.. code:: sql

    SELECT
        rra.role_id
    FROM
        <main_schema>.restrictionarea AS ra,
        <main_schema>.role_restrictionarea AS rra,
        <main_schema>.layer_restrictionarea AS lra,
        <main_schema>.treeitem AS la
    WHERE
        rra.restrictionarea_id = ra.id
    AND
        lra.restrictionarea_id = ra.id
    AND
        lra.layer_id = la.id
    AND
        la.name =

It is required to have the following in the ``VALIDATION`` section of the ``LAYER``:

.. code::

   VALIDATION
     # For secured layers
     "default_role_ids" "-1"
     # Or
     # "default_role_ids" "<id of the anonymous role>"
     "role_ids" "^-?[0-9,]*$"
   END

The ``default_role_ids`` define the restrictions when mapserver is called without any ``roles_ids``.
In this situation, if you have set ``default_role_ids`` to ``-1`` for this layer, then there is
no access; if you have set ``default_role_ids`` to the anonymous role id, then the access rights of
anonymous users apply.


Filename
~~~~~~~~

The mapfile should be a ``.map.tmpl`` file, for the variable to be substituted at container start.


Variable Substitution
---------------------

It is possible to adapt some values in the mapfile according to the user's role
by using variable substitution, for instance to hide some layer objects
attributes. The list of parameters that support variable substitution is
available `here <https://mapserver.org/cgi/runsub.html#parameters-supported>`_.

To define variables, edit the matching ``MAP``/``LAYER``/``VALIDATION``
section in the MapFile and add:

.. code::

    "default_s_<variable>" "<default_value>"
    "s_<variable>" "<validation_pattern>"

The ``validation_pattern`` is a regular expression used to validate the
argument. For example, if you only want lowercase characters and commas,
use ``^[a-z,]*$``.

Now in ``LAYER`` place ``%s_<variable>%`` where you want to
insert the variable value, but not at the start of a line (to avoid escape issues).

Then in the administration interface, create a ``functionality`` named
``mapserver_substitution`` with the value: ``<variable>=<value>``.

Please note that we cannot use substitution in the ``METADATA`` values.
As a result, if you would like to adapt the list of attributes returned in a
WFS GetFeature or WMS GetFeatureInfo request, you have to adapt the columns
listed in the ``DATA`` section. For instance:

.. code:: sql

    LAYER
        ...
        DATA "geom FROM (SELECT t.geom, t.type, t.gid, %s_columns% FROM geodata.table as t)  AS foo USING unique gid using SRID=2056"
        METADATA
            ...
            "gml_exclude_items" "type,gid"
            "gml_include_items" "all"
        END
        VALIDATION
            "default_s_columns" "t.name"
            "s_columns" "^[a-z,._]*$$"
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

   You can also use variable substitution for the ``role_id`` and ``user_id``,
   but beware that these attributes are not available for cached queries like:
   ``GetCapabilities``, ``GetLegendGraphic``, ``DescribeFeatureType``.

`MapServer documentation <https://mapserver.org/cgi/runsub.html>`_



Performance improvement
-----------------------

Adding an ``EXTENT`` parameter to the ``LAYER`` section may significantly improve performance
because it saves MapServer from computing the extent of all layer features.


.. _administrator_mapfile_perepare_raster:

Prepare raster files
~~~~~~~~~~~~~~~~~~~~

To achieve good performance, you should have tiled files with overviews, and ideally
a tileindex. You can achieve this with these steps:

.. prompt:: bash

   mkdir optimized
   do
       gdal_translate ${file} -co TILED=YES -co COMPRESS=DEFLATE
       gdaladdo -r average  ${file} 2 4 8 16 32
       gdal_translate ${file} optimized/${file} \
           -co TILED=YES -co COMPRESS=JPEG -co PHOTOMETRIC=YCBCR -co COPY_SRC_OVERVIEWS=YES
   done

You can generate a shapefile indexing all your rasters:

.. prompt:: bash

  gdaltindex filename_index.shp optimized/*.tif


Note about ECW
--------------

In general using ECW is not recommended, as MapServer often generates broken
images and has memory leaks with ECW. See this
`MapServer ticket <https://trac.osgeo.org/mapserver/ticket/3245>`_
for example.

If you still want to use it, then replace ``SetHandler fcgid-script``
by ``SetHandler cgi-script`` in the ``apache/mapserver.conf.tmpl``
file. But note that this affects performance.

mappyfile
---------

The tool container contains mappyfile, he can be used to 'Pretty Printing', 'Validate', ...
See the `project documentation <https://mappyfile.readthedocs.io/>`_.

For example to validate the map files run:

.. prompt:: bash

   docker-compose exec tools mappyfile validate --version=7.6 /etc/mapserver/*.map
