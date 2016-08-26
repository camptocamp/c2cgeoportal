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

For the next steps it is important to figure out if the main goal is the scalability
or the robustness of the application.

In general the scalability is more important because the main cause of
down time is due of too much traffic.

In this case the first thing to do is to separate the services:

 * PostgreSQL / PostGIS
 * Print
 * WSGI application
 * MapServer / MapCache / Memcached

To have better DB performances, one can setup multiple Postgres servers in a
`master/slave <https://wiki.postgresql.org/wiki/Binary_Replication_Tutorial>`_
configuration. To enable this feature on GeoMapFish, you must add this to your
``vars_<project>.yaml``:

.. code:: yaml

    dbhost_slave: my_db_slave_hostname
    sqlalchemy_slave:
        url: postgresql://{dbuser}:{dbpassword}@{dbhost_slave}:{dbport}/{db}

Add in your project Makefile ``<package>.mk``:

.. code:: makefile

   CONFIG_VARS += sqlalchemy_slave.url

Then, all the GET and OPTIONS requests will use one of the slave Postgres instances and the
rest will use the master instance.
It is assumed, here, that the views handling the GET and OPTIONS queries don't cause write
operations to the database (not supported by slave instances). If it is not the case in your
application (bad practice), add entries to ``db_chooser/master`` in your ``vars_<project>.yaml``.
For forcing the use of a slave for a POST/PUT/DELETE, add entries to the ``db_chooser/slave``
configuration.

For having more than one instance of slave and having an automatic election of a new
master in case of failure, you must setup an high availability proxy (HAProxy, for example).
This is out of the scope of this document. If you don't care about failover, you can use one
DNS entry with multiple IP entries for the slaves.
