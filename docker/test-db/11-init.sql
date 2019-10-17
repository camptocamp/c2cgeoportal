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

CREATE TABLE geodata.testpointtime (
    id serial PRIMARY KEY,
    name varchar,
    time timestamp with time zone,
    geom geometry(POINT, 21781)
);
