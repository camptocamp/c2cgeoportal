.. _integrator_cluster:

Create a cluster
================

A cluster is a configuration where several servers are used to serve the application
in production.

Creating a cluster implies to separate the database and the application to
make sure that the data are the same on all servers.

A possibility is to have the same database for all servers (integration, production).
A single schema for static data is shared, whereas a dedicated main schema will
be used for each server.

Deploying data from integration to production may be done by
`cloning the main integration schema <https://wiki.postgresql.org/wiki/Clone_schema>`_.

For the next steps it's important to figure out if the main goal is the scalability
or the robustness of the application.

In general the scalability is more important because the main cause of
down time is due of too much traffic.

In this case the first thing to do is to separate the services:

 * PostgreSQL / PostGIS
 * Print
 * WSGI application
 * MapServer / MapCache / Memcached
