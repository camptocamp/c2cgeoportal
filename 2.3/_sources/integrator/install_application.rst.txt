.. _integrator_install_application:

Install an existing application
===============================

On this page we explain all the procedures to build an application from
only the code.

For example If you want to use an existing database you should ignore
all the commands concerning the database.

This guide considers that:
 - We use a server manages by Camptocamp, meaning:
    - all dependencies described in the
      :ref:`requirements <integrator_requirements>` are installed,
    - Postgres has a GIS template ``template_postgis`` and a user ``www-data``,
    - Apache uses the user ``www-data``.
 - Use Git as revision control.

For the others system there is some notes to give some help.

Set up the database
-------------------

Any c2cgeoportal application requires a PostgreSQL/PostGIS database. The
application works with its own tables, which store users, layers, etc. These
tables are located in a specific schema of the database.

.. note::

    Multiple specific schemas are actually used in a parent/child architecture.

If the application has MapServer layers linked to PostGIS tables, these tables
and the application-specific tables must be in the same database, preferably in
separate schemas. This is required for layer access control (*restricted
layers*), where joining user/role tables to PostGIS layer tables is necessary.

.. _integrator_install_application_create_database:

Create the database
~~~~~~~~~~~~~~~~~~~

To create the database you can use:

.. prompt:: bash

    sudo -u postgres createdb <db_name> -T template_postgis

with ``<db_name>`` replaced by the actual database name.

.. note::

   if you do not have the template_postgis you can use:

   with Postgres >= 9.1 and PostGIS >= 2.1:

   .. prompt:: bash

       sudo -u postgres createdb -E UTF8 -T template0 <db_name>
       sudo -u postgres psql -c "CREATE EXTENSION postgis;" <db_name>

   with older versions:

   .. prompt:: bash

       sudo -u postgres createdb -E UTF8 -T template0 <db_name>
       sudo -u postgres psql -d <db_name> -f /usr/share/postgresql/9.1/contrib/postgis-2.1/postgis.sql
       sudo -u postgres psql -d <db_name> -f /usr/share/postgresql/9.1/contrib/postgis-2.1/spatial_ref_sys.sql

   Note that the path of the postgis scripts and the template name can
   differ on your host.

Create the "pg_trgm" extension to use the "similarity" function within the
full-text search:

.. prompt:: bash

  sudo -u postgres psql -c "CREATE EXTENSION pg_trgm" <db_name>

.. _integrator_install_application_create_schema:

Create the schema
~~~~~~~~~~~~~~~~~

Each parent or child needs two application-specific schemas,
then to create it use:

.. prompt:: bash

    sudo -u postgres psql -c "CREATE SCHEMA <schema_name>;" <db_name>
    sudo -u postgres psql -c "CREATE SCHEMA <schema_name>_static;" <db_name>

with ``<db_name>`` and ``<schema_name>`` replaced by the actual database name,
and schema name ('main' by default), respectively.

.. _integrator_install_application_create_user:

Create a database user
~~~~~~~~~~~~~~~~~~~~~~

We use a specific user for the application, ``www-data`` by default.

.. note::

   It the user does not already exist in your database, create it first:

   .. prompt:: bash

        sudo -u postgres createuser -P <db_user>

Give the rights to the user:

.. prompt:: bash

    sudo -u postgres psql -c 'GRANT SELECT ON TABLE spatial_ref_sys TO "www-data"' <db_name>
    sudo -u postgres psql -c 'GRANT ALL ON TABLE geometry_columns TO "www-data"' <db_name>
    sudo -u postgres psql -c 'GRANT ALL ON SCHEMA <schema_name> TO "www-data"' <db_name>
    sudo -u postgres psql -c 'GRANT ALL ON SCHEMA <schema_name>_static TO "www-data"' <db_name>

.. note::

   If you do not use the www-data user for Apache replace it by the right user.


Install the application
-----------------------

Get the application source tree
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If Git is used for the application use the following command to get the
application source tree:

.. prompt:: bash

    git clone git@github.com:camptocamp/<project>.git
    cd <project>


Non Apt/Dpkg based OS Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For example Windows or RedHat.

Disable the package checking:

In the ``<package>.mk`` add::

    TEST_PACKAGES = FALSE

Windows Specific Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some Python modules cannot currently be installed through the Python Package
Index (PyPI) and they have to be downloaded manually and stored. This is
because these packages use DLLs and binaries which would have to be compiled
using a C compiler.

Furthermore, some changes in the apache WSGI and MapServer configurations are
required to make c2cgeoportal work on Windows.

Also, between all the different command interfaces available on Windows (cmd,
Cygwin, git mingw), only Windows default cmd interface handle paths correctly
in all stage of the application setup.

Command interface and environment variable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Only use Windows default command interface::

    Start > Run... > cmd

Cygwin and git mingw are not compatible. Powershell is untested.

Complementarily you need to add all the resource paths to your system PATH
environment variable, for cygwin, git and node binaries.

Cygwin
^^^^^^

You must install the following packages:

* make
* git
* gettext-devel

Python Wheels
^^^^^^^^^^^^^

You should create a "wheels" folder at the root folder of your project.

Then, go to http://www.lfd.uci.edu/~gohlke/pythonlibs/, search and download the
following packages:

* Psycopg2
* Shapely
* Pillow
* Pyproj

If your project is configured for Windows, then ``make`` will expect this folder
to exist and to contain these wheels.

mapserver/mapserver.map.mako
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You must specify the path to the MapServer's EPSG file by uncommenting and adapting
this line under ``MAP`` (use regular slash ``/``) ::

    PROJ_LIB" "C:/PATH/TO/ms4w/proj/nad"

<project>.mk
^^^^^^^^^^^^

The following configuration override must be added to your ``<project>.mk``::

    # Sets that is we use Windows
    OPERATING_SYSTEM ?= WINDOWS
    # Path to cygwin
    CYGWIN_PATH ?= c:/path/to/cygwin

RedHat Specific Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Specific settings are required when the c2cgeoportal application is to be run
on RedHat Enterprise Linux (RHEL) 6.

.. note::

    First of all, note that, with RHEL, you cannot install the c2cgeoportal
    application in your homedir. If you do so, you will get the following error
    in the Apache logs::

        (13)Permission denied: access to /~elemoine/ denied

    So always install the application in an Apache-accessible directory. On
    Camptocamp *puppetized* servers you will typically install the application
    in ``/var/www/vhosts/<vhost>/private/dev/<username>/``, where ``<vhost>``
    is the name of the Apache virtual host, and ``<username>`` is your Unix
    login name.


apache/application.wsgi.mako
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Ensure that the regular expression used in ``apache/application.wsgi.mako`` to modify the ``sys.path``
matches the system directories containing python packages. If you are installing from scratch, this should
already be the case; otherwise look at ``scaffolds/create/apache/application.wsgi.mako`` for an example.


.. _integrator_install_application_install_application:

Install the application
~~~~~~~~~~~~~~~~~~~~~~~

Then you can build and install the application with the command:

.. prompt:: bash

    make --makefile=<user>.mk docker-build

Create the application tables, and directly set the version (details later):

.. prompt:: bash

    ./docker-run make --makefile=<user>.mk upgrade-db

For non Docker installation:

.. prompt:: bash

    FINALISE=TRUE make --makefile=<user>.mk build

This previous command will do many things like:

  * download and install the project dependencies,

  * adapt the application configuration to your environment,

  * build the javascript and css resources into compressed files,

Your application should be available at:
``http://<hostname>/``.

Where the ``<hostname>`` is directly linked to the virtual host.

Migrating to a new server
-------------------------

If you are migrating to a new server, keep in mind that your variable
``VISIBLE_WEB_HOST`` must contain the exact host name that browsers should use
to access your site. Consider the following migration scenario:
your current site runs on server ``old-site.customer.ch`` with the visible host name
``gis.customer.ch``. You wish to setup a new server ``new-site.customer.ch``,
install the application and test it, and then switch your DNS so that
``gis.customer.ch`` now points to ``new-site.customer.ch``.
To accomplish this, you must proceed as follows:

  * set ``VISIBLE_WEB_HOST`` to ``new-site.customer.ch``
  * install the application on ``new-site.customer.ch`` and test the application
    at ``http://new-site.customer.ch``

  * later, when going live, you must:

    * change ``VISIBLE_WEB_HOST`` to ``gis.customer.ch``

    * re-build, re-deploy - but do not test yet!

    * change your DNS so that ``gis.customer.ch`` points to ``new-site.customer.ch``.

    * Now test your new live site.
