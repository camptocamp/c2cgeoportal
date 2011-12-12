.. _administrator_install:

Install the application
=======================

Boostrap the application
------------------------

c2cgeoportal applications are installed from source. This section, and the rest
of this chapter, assume that you have local copy on the application source tree
(a local clone if you use Git).

The `Buildout <http://pypi.python.org/pypi/zc.buildout/1.5.2>`_ tool is used to
build, install, and deploy c2cgeoportal applications.

Prior to using Buildout its ``boostrap.py`` script should be run at the root
of the application::

  python bootstrap.py --version 1.5.2 --distribute --download-base \
        http://pypi.camptocamp.net/ --setup-source \
        http://pypi.camptocamp.net/distribute_setup.py

This step is done only once for installation/instance of the application.

Install the application
-----------------------

**To be complete**.

Install:
    
    ./buildout/bin/buildout -c buildout_$user.cfg

