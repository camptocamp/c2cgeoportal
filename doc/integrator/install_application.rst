.. _integrator_install_application:

Install an existing application
===============================

On this page we explain the procedure to build an application from only the code.

If you want to use an existing database, you should ignore all the commands concerning the database.

This guide assumes that:
 - all dependencies described in the :ref:`requirements <integrator_requirements>` are installed,
 - Git is used as revision control.

For specific environments, this page contains some notes to give some help.

.. _integrator_install_application_setup_database:

Set up the database
-------------------

Any c2cgeoportal application requires a PostgreSQL/PostGIS database. The
application works with its own tables, which store users, layers, etc. These
tables are located in a specific schema of the database.

If the application has MapServer layers linked to PostGIS tables, these tables
and the application-specific tables must be in the same database, preferably in
separate schemas. This is required for layer access control (*restricted
layers*), where joining user/role tables to PostGIS layer tables is necessary.

You need a Postgres database >= 9.1 in UTF-8 with the PostGIS >= 2.1 extension.

Create the "pg_trgm" extension to use the "similarity" function within the full-text search.

Create the "unaccent" extension to have accent-insensitive search within the full-text search.

And by default we assume that the ``www-data`` user exists with all rights on the application schema.


.. _integrator_install_application_create_schema:

Create the schemas
~~~~~~~~~~~~~~~~~~

Each application needs two application-specific schemas.
To create them, do:

.. prompt:: bash

    sudo -u postgres psql -c "CREATE SCHEMA <schema_name>;" <db_name>
    sudo -u postgres psql -c "CREATE SCHEMA <schema_name>_static;" <db_name>
    sudo -u postgres psql -c 'GRANT ALL ON SCHEMA <schema_name> TO "www-data"' <db_name>
    sudo -u postgres psql -c 'GRANT ALL ON SCHEMA <schema_name>_static TO "www-data"' <db_name>


Install the application
-----------------------

Windows Specific Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some Python modules cannot currently be installed through the Python Package
Index (PyPI) and they have to be downloaded manually and stored. This is
because these packages use DLLs and binaries which would have to be compiled
using a C compiler.

Furthermore, some changes in the Apache WSGI and MapServer configurations are
required to make c2cgeoportal work on Windows.

Also, between all the different command interfaces available on Windows (cmd,
Cygwin, git mingw), only Windows default cmd interface handle paths correctly
in all stage of the application setup.

Command interface and environment variable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Only use Windows default command interface::

    Start > Run... > cmd

Cygwin and git mingw are not compatible. Powershell is untested.

In addition, you need to add all the resource paths to your system PATH
environment variable, for cygwin, git and node binaries.

Cygwin
^^^^^^

You must install the following packages:

* git


.. _integrator_install_application_install_application:

Install the application
~~~~~~~~~~~~~~~~~~~~~~~

You can build and install the application with the command:

.. prompt:: bash

    ./docker-run make --makefile=<user>.mk build

This previous command will do many things like:

  * adapt the application configuration to your environment,
  * build the JavaScript and CSS resources into compressed files.

Then create the application tables:

.. prompt:: bash

    ./docker-compose-run make --makefile=<user>.mk upgrade-db

Your application should now be available at:
``https://<hostname>/``.

Where the ``<hostname>`` is directly linked to the virtual host.

Add in the ``/var/www/vhosts/<vhost_name>/conf/proxies.conf`` file (create it if not exist):

.. code::

   ProxyPass "/<instance>"  "http://localhost:8080/<instance>"
   ProxyPassReverse "/<instance>"  "http://localhost:8080/<instance>"
   ProxyPreserveHost On
   RequestHeader set X-Forwarded-Proto "https"
   RequestHeader set X-Forwarded-Port "443"
   ProxyRequests Off

The root instance should be at the end.

Migrating to a new server
-------------------------

If you are migrating to a new server, keep in mind that your variable
``DOCKER_WEB_HOST`` must contain the exact host name that browsers should use
to access your site. Consider the following migration scenario:
your current site runs on server ``old-site.customer.ch`` with the visible host name
``gis.customer.ch``. You wish to setup a new server ``new-site.customer.ch``,
install the application and test it, and then switch your DNS so that
``gis.customer.ch`` now points to ``new-site.customer.ch``.
To accomplish this, you must proceed as follows:

  * set ``DOCKER_WEB_HOST`` to ``new-site.customer.ch``
  * install the application on ``new-site.customer.ch`` and test the application
    at ``http://new-site.customer.ch``

  * later, when going live, you must:

    * change ``DOCKER_WEB_HOST`` to ``gis.customer.ch``

    * re-build, re-deploy - but do not test yet!

    * change your DNS so that ``gis.customer.ch`` points to ``new-site.customer.ch``.

    * Now test your new live site.
