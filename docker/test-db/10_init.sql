CREATE EXTENSION IF NOT EXISTS postgis;

CREATE SCHEMA main;
CREATE SCHEMA main_static;
CREATE SCHEMA geodata;
ALTER USER "www-data" PASSWORD 'www-data';
GRANT SELECT ON spatial_ref_sys TO "www-data";
GRANT ALL ON SCHEMA main TO "www-data";
GRANT ALL ON SCHEMA main_static TO "www-data";
GRANT ALL ON SCHEMA geodata TO "www-data";
GRANT ALL ON geometry_columns TO "www-data";
CREATE TABLE geodata.testpoint (
    id serial PRIMARY KEY,
    name varchar,
    city varchar,
    country varchar,
    geom geometry(POINT, 21781)
);
ALTER TABLE geodata.testpoint OWNER TO "www-data";
