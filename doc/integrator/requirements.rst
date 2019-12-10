.. _integrator_requirements:

Requirements
============

To install a GeoMapFish application, you need to have the following
components installed on your system:

* **Git**
* **Docker** >= 1.12 (>= 17 is recommended)
* **Docker-compose** >= 1.8
* **Python** >= 3.5
* **Python-netifaces**
* **Apache** >= 2.4 (optional, can be used as a front for SSL)
* **PostgreSQL** >= 9.1/**PostGIS** >= 2.1
* **gnupg** (with **dirmngr**) optional


Required Apache modules
~~~~~~~~~~~~~~~~~~~~~~~

* ``mod_proxy``
* ``mod_proxy_http``

Additional notes for Windows users
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
