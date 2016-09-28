.. _developer_documentation_infrastructure:

Documentation infrastructure
============================

c2cgeoportal
------------

The c2cgeoportal documentation is publicly available at
http://docs.camptocamp.net/c2cgeoportal/.

The ``docs.camptocamp.net`` server has an ``@hourly`` cronjob that runs the
``update_online.sh`` script, which is in the ``doc`` directory of c2cgeoportal.

To manually update the online doc you can log onto ``docs.camptocamp.net`` as
``sig``, change directory to
``/var/www/vhosts/docs.camptocamp.net/private/c2cgeoportal/doc`` and run
``update_online.sh`` from there.

Before generating the HTML documentation the ``update_online.sh`` script
updates the documentation source by pulling from
http://github.com/camptocamp/c2cgeoportal. For this we use a `GitHub Deploy Key
<http://help.github.com/deploy-keys/>`_. In case you need to change the deploy
key point your browser to http://github.com/camptocamp/c2cgeoportal, and go the
repository's admin page (``Admin`` button), you should see ``Deploy Keys`` in
the menu, where the ``docs.camptocamp.net`` deploy key should be available.
This deploy key should match the SSH key of the ``sig`` user on
``docs.camptocamp.net``.

.. note::

    The initial ``git clone`` of c2cgeoportal, the GitHub deploy key, and the
    cron configuration are managed by puppet.

CGXP
----

The CGXP documentation is publicly available at
http://docs.camptocamp.net/cgxp/.

The ``docs.camptocamp.net`` server has an ``@hourly`` cronjob that runs the
``update_online.sh`` script, which is in the ``core/src/doc`` directory of
cgxp.

To manually update the online doc you can log onto ``docs.camptocamp.net`` as
``sig``, change directory to
``/var/www/vhosts/docs.camptocamp.net/private/cgxp/core/src/doc`` and run
``update_online.sh`` from there.

.. note::

    The initial ``git clone`` of cgxp, and the cron configuration are managed
    by puppet. Contrary to c2cgeoportal there's no need for a GitHub deploy
    key, as the CGXP repository is public.
