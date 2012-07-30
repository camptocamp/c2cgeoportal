.. _developper_bootstrap:

Bootstrap c2cgeoportal
=====================

This chapter explain how is it possible to create a new application
directly from the c2cgeoportal sources, this is used to create the first
application of a project, this is not necessary to create a new
child of an existing project.

Checkout and build c2cgeoportal
-------------------------------

Installing c2cgeoportal is done using Buildout.

Clone c2cgeoportal::

    git clone git@github.com:camptocamp/c2cgeoportal.git
    cd c2cgeoportal
    git submodule update --init

Bootstrap Buildout::

    python bootstrap.py --version 1.5.2 --distribute --download-base \
        http://pypi.camptocamp.net/distribute-0.6.22_fix-issue-227/ --setup-source \
        http://pypi.camptocamp.net/distribute-0.6.22_fix-issue-227/distribute_setup.py

Build c2cgeoportal::

    ./buildout/bin/buildout

Now you are ready to start to use the
:ref:`integrator_create_application`
tutorial from `Organisation of a project`

.. note::

    The above command downloads the latest *final* ``c2cgeoportal`` package from
    http://pypi.camptocamp.net/internal-pypi/index/.

    To install a development package of c2cgeoportal you can edit buildout.cfg
    and set ``prefer-final`` to ``false``.
