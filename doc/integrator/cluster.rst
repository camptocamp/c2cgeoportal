.. _integrator_cluster:

Create a cluster
================

A cluster is a configuration where several servers are used to serve the application.

Deploying data from integration to production may be done by
`cloning the main integration schema <https://wiki.postgresql.org/wiki/Clone_schema>`_;
a customized version of the script, applicable for c2cgeoportal, is available in
``scripts/CONST_clone_schema.sql``.

For the next steps, it is important to know if your main goal is the scalability
or the robustness of the application.

In general, scalability is more important, because the main cause of
down time is too much traffic.

To have better DB performance, one can setup multiple Postgres servers in a
`master/slave <https://wiki.postgresql.org/wiki/Binary_Replication_Tutorial>`_
configuration. To enable this feature on GeoMapFish, you must add this to your ``vars.yaml``:

.. code:: yaml

    dbhost_slave: my_db_slave_hostname

Then, all the GET and OPTIONS requests will use one of the slave Postgres instances and the
rest will use the master instance.
It is assumed, here, that the views handling the GET and OPTIONS queries do not cause write
operations to the database (not supported by slave instances). If it is not the case in your
application (bad practice), add entries to ``db_chooser/master`` in your ``vars.yaml``.
For forcing the use of a slave for a POST/PUT/DELETE, add entries to the ``db_chooser/slave``
configuration.

To have more than one slave instance and to have an automatic election of a new
master in case of failure, you must setup a high availability proxy (HAProxy, for example).
This is out of the scope of this document. If you do not care about failover, you can use one
DNS entry with multiple IP entries for the slaves.
