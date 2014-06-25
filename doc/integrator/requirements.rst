.. _integrator_requirements:

Requirements
============

To install a GeoMapFish application you need to have the following
components installed on your system:

* **Git** (preferably to other revision control systems)
* **Python** 2.6, 2.7 (2.5 or 3.x are not supported)
* Oracle **Java** SE Development Kit 6 or 7
* **Tomcat**
* **Apache**
* **PostgreSQL** >= 9.1/**PostGIS** 1.5.3 (PostgreSQL 8.x and 9.0 should work
    but some commands used in this guide don't work)
* **MapServer** 6.0.2 and upper (MapServer 6.0.0 and 6.0.1 have some
    issues with WFS) or **QGIS**-mapserver 2.2 and upper
* **ImageMagick**
* **Sencha** Command

Required apache modules
~~~~~~~~~~~~~~~~~~~~~~~

* ``mod_expires``
* ``mod_headers``
* ``mod_proxy``
* ``mod_proxy_http``
* ``mod_rewrite``
* ``mod_wsgi``

Additional notes for Windows users
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For Git look at GitHub's `Set Up Git page
<http://help.github.com/win-set-up-git/>`_. You won't need to set up SSH
keys, so you only need to follow the first section of this page.

Once Git is installed use Git Bash for all the shell commands provided in
this documentation. You'll need to make sure the Turtoise, Python, and Java
folders are defined in your system ``PATH``. For example if you have Python installed under
``C:\Python26`` you can use ``export PATH=$PATH:/c/Python26`` to add Python
to your ``PATH``.

You need to install the ``psycopg2`` Python package in the main Python
environment (e.g. ``C:\Python26``). Use an installer (``.exe``) from the
`Stickpeople Project
<http://www.stickpeople.com/projects/python/win-psycopg/>`_.

When you download and configure Apache be sure that modules ``header_module``,
``expire_module`` and ``rewrite_module`` are uncommented. You must also download
and add modules ``mod_wsgi`` (http://modwsgi.readthedocs.org/) and ``mod_fcgid``
(https://httpd.apache.org/mod_fcgid/).
