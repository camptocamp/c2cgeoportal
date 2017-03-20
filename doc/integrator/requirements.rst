.. _integrator_requirements:

Requirements
============

To install a GeoMapFish application you need to have the following
components installed on your system:

* **Git** (preferably to other revision control systems)
* **Python** 2.7 (2.5 or 3.x do not work, 2.6 should work but is not supported) with development files (``python-dev``)
* **VirtualEnv** >= 1.7
* Oracle **Java** SE Development Kit 6 or 7
* **Tomcat** >= 6.0
* **Apache** >= 2.2
* **PostgreSQL** >= 9.1/**PostGIS** >= 2.1, with library (``libpq-dev``)
* **MapServer** 7.0 or **QGIS**-mapserver 2.2 and upper
* **MapCache** >= 1.0.0 with memcached support
* **TinyOWS** >= 1.1.0
* **ImageMagick**
* **GCC** GNU Compiler Collection >= 4.6
* **Deploy** >= 0.4
* **libproj** >= 4.7
* **gettext** >= 0.18

For ngeo
~~~~~~~~

* **node** >= 0.10
* **npm** >= 1.3

Required Apache modules
~~~~~~~~~~~~~~~~~~~~~~~

* ``mod_expires``
* ``mod_headers``
* ``mod_proxy``
* ``mod_proxy_http``
* ``mod_rewrite``
* ``mod_wsgi``
* ``mod_mapcache``

Conflicting Apache modules
~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``mod_php*``


Print
~~~~~

The print requires a Tomcat server listening by default on port 8080.
To change it you should overwrite the ``print_url`` vars in ``config.yaml.in``,
default is: ``http://localhost:8080/print-c2cgeoportal-{instanceid}/pdf/``.

And by default the 'webapps' folder is ``/srv/tomcat/tomcat1/webapps``,
to change it set the ``PRINT_OUTPUT`` value in the makefile.

For MapFish Print to function properly it is recommended to increase the default
Java Heap Size for Tomcat (parameter ``-Xmx`` and ``-Xms``). On servers managed
by Camptocamp check the size in the file ``/srv/tomcat/tomcat1/bin/setenv-local.sh``:

  .. code:: make

    export JAVA_XMX="1G"
    export ADD_JAVA_OPTS="-Xms1G"

The above settings set the minimum and maximum heap size to 1GB.

Additional notes for Windows users
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

GeoMapFish can be used under Windows, but you will need to install Cygwin
and some additional stuff for Python.

We assume that Python 2.7 is used.

Once Python is installed, you should add two folders to your ``path`` environment
variable:

* ``C:\path_to_python\Python27``
* ``C:\path_to_python\Python27\Scripts``

Python
^^^^^^

* Install Microsoft Visual C++ Compiler for Python 2.7 (http://aka.ms/vcpython27)
* Be sure to have at least pip >= 9.x in your project . Using virtualenv >= 15 should resolve that.

Cygwin
^^^^^^

* Go to https://cygwin.com/
* In the download section, download the installer corresponding to your system
* Run the downloaded installer
* Choose an install folder not containing any space or weird characters (like parentheses)

When installing Cygwin, please make sure to install the following non-default packages:

* ``make`` from the ``devel`` folder
* ``gettext-devel`` from the ``devel`` folder
* ``wget`` from the ``web`` folder

Cygwin should *always* be run in administrator mode. To configure that:

* Go to the Windows start menu
* Right-click the Cygwin Terminal program icon
* Open its properties
* Under the ``Compatibility`` tab, check the ``Run this program as an administrator``

To avoid file permission problems between Windows and Cygwin, edit Cygwin's
``/etc/fstab`` file to disable ACLs like this:

.. prompt:: bash

    none /cygdrive cygdrive binary,noacl,posix=0,user 0 0

Configure Git
^^^^^^^^^^^^^

Cygwin comes with its own git package. It might be a really good idea to configure
Cygwin's git for Windows. To do so:

* Open a Cygwin bash
* Run ``git config core.autocrlf true``

Print
^^^^^^

If using MapFish Print v3 (thus defining ``PRINT_VERSION ?= 3`` in your
makefile), then you should define the service name of your Tomcat server. In
your makefile, define the following variables:

.. prompt:: bash

    PRINT_TMP = tmp
    TOMCAT_START_COMMAND = net START Tomcat7
    TOMCAT_STOP_COMMAND = net STOP Tomcat7

The first line disables the tmp folder, which is not working on Windows.
The next two lines define the commands to start and stop your Tomcat service
(here it would be ``Tomcat7``). On Windows, these commands differ from the one
used on Linux.
