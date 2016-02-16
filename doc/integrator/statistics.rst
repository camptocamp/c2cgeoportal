.. _integrator_statistics:

Statistics
==========

It is sometimes important to understand where time is lost. A statistics module can be
enabled to measure that.

Configuration
-------------

The statistics module can have two different outputs that are both disabled by default.

The first one is the StatsD one. To enable it you must configure the target address for
the StatsD daemon. You can either define the following environment variables:

.. prompt:: bash

    export STATSD_ADDRESS=statsd:8125
    export STATSD_PREFIX=my_app.wsgi

Or add those lines to your ``vars_<instance>.yaml``:

.. code:: yaml

    vars:
        ...
        stats:
            statsd_address: statsd:8125
            statsd_prefix: my_app.wsgi

The second output is an in memory collector that adds two URLs to the application:

* /stats.html
* /stats.json

To enabled it (not recommended for production systems), you can either define the
following environment variable:

.. prompt:: bash

    export STATS_VIEW=1

Or add one line to your ``vars_<instance>.yaml``:

.. code:: yaml

    vars:
        ...
        stats:
            view: true


Add more statistics
-------------------

By default, timing statistics are added for the routes and the SQL queries. If you want to
measures special things in you application, just add code like that:

.. code:: python

    from c2cgeoportal import stats
    ...
        measure = stats.timer()
        ... # The code you want to measure
        measure.stop(["my_feature", "something"])


Or, if you know the key in advance and can use a context, you can write it like that:

.. code:: python

    from c2cgeoportal import stats
    ...
        with stats.timer_context(["my_feature", "something"]):
            ... # The code you want to measure
