.. _integrator_deploy:

Deploy the application
======================

Important notes
---------------

When we deploy an application we:

* Deploy the application code (copy, and specific build).
* Copy the geodata files usually in /var/sig/...
* Copy the database.
* Add the Apache configuration

Copying the database may be critical since it may result in losing data.
For instance if the target database contains user-edited data such as:

1. features modified in the editing interface,
2. shortened URLs,
3. new passwords.


Preserving user-created data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To prevent data modified by the users (such as editable layers features or
short permalinks) from being lost when redeploying the DataBase, such data
must be saved in dedicated schemas that won't be replaced.

For that we should have 4 different schemas:

* one for the application data that should be deployed (``<schema>``),
* one for the application data that shouldn't be deployed (``<schema>_static``),
* one for the readonly geodata that should be deployed,
* one for the editable geodata that shouldn't be deployed.

We should configure the deploy tool to deploy only the
wanted schema, by setting the following configuration in the
``[databases]`` section of the ``deploy/deploy.cfg.in`` file::

    names = ${vars:db}.${vars:schema},${vars:db}.<readonly_geodata_schema>
    use_schema = true

And use deploy version >= 0.3.3.


Shortened URLs
~~~~~~~~~~~~~~

We put the short URL table in a separate schema postfixed with ``_static``
then the deploy configuration set in the previous point also fix this case.


New passwords
~~~~~~~~~~~~~

We are able to replicate the password,
see :ref:`integrator_password_replication`.


Administration interface
~~~~~~~~~~~~~~~~~~~~~~~~

All configurations done in the administration interface of the development
host are deployed to the production host as well. As a result it is not
necessary (and not recommended) to make changes in the production
administration interface.


Deploy configuration
--------------------

The first time you want do deploy an application the configuration
should be set up in file ``deploy/deploy.cfg[.in]``.

The deploy tool has four parts:

* ``[files]`` to deploy the GeoTIFF, ShapeFiles and so on.
* ``[databases]`` to deploy the database.
* ``[code]`` to deploy the application.
* ``[apache]`` to build the apache config.

An other important section is the ``[remote_hosts]`` where we
configure the demo and production hosts.

All the configuration option can be found in ``/etc/deploy/deploy.cfg``.

Get help with the command line ``deploy --help``.


Buildout configuration
----------------------

To use specific parameter values on the ``$TARGET`` server (for instance for
``host``), create dedicated ``buildout_$TARGET.cfg`` files that will contain
those values. The deploy tool will then automatically detect those files and
use them when running the buildout command on the ``$TARGET`` server.

For instance a buildout configuration file for the ``prod`` server would be
named ``buildout_prod.cfg`` and look like::

     [buildout]
     extends = buildout.cfg

     [vars]
     host = <prod hostname>
     apache-entry-point = /

If you have more than one instance on a domain name you can define
``apache-entry-point`` with something like ``/a_name/``. The trailing ``/``
is required in the ``apache-entry-point`` but not in the URL, than
`http://host/a_name` will work.


Prepare destination host
------------------------

On the destination host we just need that the schema postfixed with
``_static`` already exists.


Easy deploy (experimental)
--------------------------

First of all be sure that the application on the source server work well!

Connect to your server using your SSH agent:

.. prompt:: bash

   ssh -A <dev_server>

Go into your project directory:

.. prompt:: bash

   cd /var/www/<your_vhost>/private/<your_project>

Deploy your project:

.. prompt:: bash

   ./buildout/bin/c2ctool deploy <host>

Where ``<host>`` is your destination host that you configured in the
``deploy/deploy.cfg`` file, e.g. ``demo``, ``prod``.


To deploy from dev to demo
--------------------------

Build on the dev server:

.. prompt:: bash

  ssh -A <dev_server> # SSH agent forward is needed
  cd /var/www/<your_vhost>/private/<your_project>
  git pull origin master # update the code
  rm -rf buildout/parts/modwsgi # to prevent rights error
  ./buildout/bin/buildout -c buildout_main.cfg # configure c2cgeoportal

**Test on the dev server**

Deploy to the demo server:

.. prompt:: bash

  rm -rf buildout/parts/modwsgi # to prevent rights error
  cd deploy
  sudo -u deploy deploy -r deploy.cfg demo
  ./buildout/bin/buildout -c buildout_main.cfg # to make dev working again

**Test on the demo server**


To deploy from demo to prod
---------------------------

**Test on the demo server**

Deploy on the prod server:

.. prompt:: bash

  ssh -A <demo_server> # SSH agent forward is needed
  cd /var/www/<your_vhost>/private/<your_project>
  cd deploy
  sudo -u deploy deploy -r deploy.cfg prod

**Test on the prod server**
