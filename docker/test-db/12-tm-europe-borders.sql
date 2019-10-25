
CREATE SCHEMA "data";
CREATE TABLE "data"."europe_borders" (gid serial,
"fips" varchar(2),
"iso2" varchar(2),
"iso3" varchar(3),
"un" int4,
"name" varchar(50),
"area" numeric,
"pop2005" numeric,
"region" int4,
"subregion" int4,
"lon" numeric,
"lat" numeric);
ALTER TABLE "data"."europe_borders" ADD PRIMARY KEY (gid);
SELECT AddGeometryColumn('data','europe_borders','geom','4326','MULTIPOLYGON',2);
