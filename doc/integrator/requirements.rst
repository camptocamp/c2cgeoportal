.. _integrator_requirements:

Requirements
============

To install a GeoMapFish application you need to have the following
components installed on your system:

* **Git** (preferably to other revision control systems)
* **Python** 2.6, 2.7 (2.5 or 3.x are not supported) with development files (``python-dev``)
* **VirtualEnv** >= 1.7
* Oracle **Java** SE Development Kit 6 or 7
* **Tomcat** >= 6.0
* **Apache** >= 2.2
* **PostgreSQL** >= 9.1/**PostGIS** >= 2.1, with library (``libpq-dev``)
* **MapServer** 7.0 or **QGIS**-mapserver 2.2 and upper
* **MapCache** >= 1.0.0
* **TinyOWS** >= 1.1.0
* **ImageMagick**
* **GCC** GNU Compiler Collection >= 4.6
* **Deploy** >= 0.4
* **libproj** >= 4.7
* **gettext** >= 0.18

For CGXP
~~~~~~~~

* **Sencha** Command
* **Compass**

For ngeo
~~~~~~~~

* **node** >= 0.10
* **npm** >= 1.3

Required apache modules
~~~~~~~~~~~~~~~~~~~~~~~

* ``mod_expires``
* ``mod_headers``
* ``mod_proxy``
* ``mod_proxy_http``
* ``mod_rewrite``
* ``mod_wsgi``
* ``mod_mapcache``

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
