CREATE SCHEMA main;
ALTER USER "www-data" PASSWORD 'www-data';
GRANT SELECT ON spatial_ref_sys TO "www-data";
GRANT ALL ON SCHEMA main TO "www-data";
GRANT ALL ON geometry_columns TO "www-data";
