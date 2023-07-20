.. _integrator_requirements:

Requirements
============

To install a GeoMapFish application, you need to have the following
components installed on your system:

* **Git**
* **Docker** >= 17.05
* **Python** >= 3.8, with ``pip``
* **Apache** >= 2.4 (optional, can be used as a front for SSL)
* **PostgreSQL** >= 9.1/**PostGIS** >= 2.1


Required Python packages
~~~~~~~~~~~~~~~~~~~~~~~~

* ``PyYAML>=3.13``
* ``docker-compose>=1.25.0``

They can be install in your user directory with:

.. code:: bash

   python3 -m pip install --user PyYAML docker-compose

If not yet done, add ``$HOME/.local/bin`` to your ``PATH``; add in your ``~/.bashrc`` file:

.. code:: bash

   PATH=$HOME/.local/bin:$PATH

Required Apache modules
~~~~~~~~~~~~~~~~~~~~~~~

* ``mod_proxy``
* ``mod_proxy_http``


Required PostgreSQL extensions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``postgis``
* ``hstore``
* ``pg_trgm`` (optional)


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

Cygwin comes with its own git package. Configure
Cygwin's git for Windows as follows:

* Open a Cygwin bash
* Run ``git config core.autocrlf true``
