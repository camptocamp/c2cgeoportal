.. _vector_tiles:

Vector tiles
============

To serve vector tiles you need to define a grid under key ``vector_tiles`` in ``geoportal/vars.yaml``, example:

.. code:: yaml

    vars:
      vector_tiles:
        srid: 2056
        extent: [2420000, 1030000, 2900000, 1350000]
        resolutions: [4000, 2000, 1000, 500, 250, 100, 50, 20, 10, 5, 2.5, 1, 0.5, 0.25, 0.1, 0.05]

You also need to define at least one "Vector Tiles" layer in admin interface with the following required attributes:

name
   Name of the layer

style
   URL to some Mapbox Style file, examples:
   - https://example.com/mystyle.json
   - static:///mb_styles/osm_landuse.json

sql
   PostGIS SQL query template with ``{envelope}`` parameter.

For example, for considered table:

.. code:: sql

   CREATE TABLE geodata.osm_landuse (
       fid integer NOT NULL,
       osm_id bigint,
       name character varying(48),
       type character varying(16),
       geom public.geometry(Polygon,2056)
   );

Here is an example SQL query template:

.. code:: sql

    SELECT ST_AsMVT(q, 'osm_landuse') FROM (
        SELECT
            fid,
            osm_id,
            name,
            type,
            ST_AsMVTGeom("geom", {envelope}) as geom
        FROM geodata.osm_landuse
        WHERE ST_Intersects("geom", {envelope})
    ) AS q

Then your vector tiles will be accessible, for example in local development mode, through:

https://localhost:8484/vector_tiles/{layer_name}/{z}/{x}/{y}.pbf
