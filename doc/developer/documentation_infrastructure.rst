.. _developer_documentation_infrastructure:

Documentation infrastructure
============================

The c2cgeoportal documentation is publicly available at
http://docs.camptocamp.net/c2cgeoportal/.

The ``docs.camptocamp.net`` server has an ``@hourly`` cronjob that runs the
``update_online.sh`` script, which is in the ``doc`` directory of c2cgeoportal.

To manually update the online doc you can log onto ``docs.camptocamp.net`` as
``sig``, change directory to
``/var/www/docs.camptocamp.com/private/c2cgeoportal/doc`` and run
``update_online.sh`` from there.

Before generating the HTML documentation the ``update_online.sh`` script
updates the documentation source by pulling from
http://github.com/camptocamp/c2cgeoportal. For this we use a `GitHub Deploy Key
<http://help.github.com/deploy-keys/>`_.

.. note::

    The initial ``git clone`` of c2cgeoportal, the GitHub deploy key, and the
    cron configuration are managed by puppet.
