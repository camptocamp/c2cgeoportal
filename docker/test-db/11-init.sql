CREATE SCHEMA main;
CREATE SCHEMA main_static;
CREATE SCHEMA geodata;

CREATE TABLE geodata.testpoint (
    id serial PRIMARY KEY,
    name varchar,
    city varchar,
    country varchar,
    geom geometry(POINT, 21781)
);
