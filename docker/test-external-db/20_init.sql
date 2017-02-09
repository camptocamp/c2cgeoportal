CREATE SCHEMA main;
ALTER USER "www-data" PASSWORD 'www-data';
GRANT SELECT ON spatial_ref_sys TO "www-data";
GRANT ALL ON SCHEMA main TO "www-data";
CREATE TABLE main.test (
    id serial PRIMARY KEY,
    type varchar
);
ALTER TABLE main.test OWNER TO "www-data";
INSERT INTO main.test (type) VALUES ('train');
INSERT INTO main.test (type) VALUES ('train');
INSERT INTO main.test (type) VALUES ('car');
