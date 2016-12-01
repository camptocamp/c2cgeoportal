.. _integrator_deploy:

=============================
Infrastructure and Deployment
=============================

Infrastructure
==============

There are three kinds of environments available for GeoMapFish applications
in Camptocamp's infrastructure:

* A user environment for the personal tests and development.
* A shared environment where more than one user should be able to build
  the application.
* A production environment.

User environment
~~~~~~~~~~~~~~~~

Located in the home directory of a user, who is the only one that may access it.

Shared environement
~~~~~~~~~~~~~~~~~~~

Located in ``/var/www/vhost/<project_vhost>/private/<project>``.

Only user ``sigdev`` may access this environment.  Developers must then prefix
all the commands on this environment by ``sudo -u sigdev``.

To be able to access to GitHub you should use the https protocol.

For instance to update the application:

.. prompt:: bash

    sudo -u sigdev make -f demo.mk update
    sudo -u sigdev make -f demo.mk build

.. note::

   If you need to access to GitHub by using the ssh protocol you
   should add the sigdev key located in ``/var/sig/.ssh/id_rsa.pub``
   as a deploy key of your project (GitHub repo > settings > Deploy keys).


Production environment
~~~~~~~~~~~~~~~~~~~~~~

To deploy the application to the production environment,
one must use the ``deploy`` tool from a clean shared environment.

See below.


Deployment
==========

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
``[databases]`` section of the ``deploy/deploy.cfg.mako`` file::

    names = ${db}.${schema},${db}.<readonly_geodata_schema>
    use_schema = true


Shortened URLs
~~~~~~~~~~~~~~

We put the short URL table in a separate schema postfixed with ``_static``
then the deploy configuration set in the previous point also fix this case.


Administration interface
~~~~~~~~~~~~~~~~~~~~~~~~

All configurations done in the administration interface of the development
host are deployed to the production host as well. As a result it is not
necessary (and not recommended) to make changes in the production
administration interface.


Deploy configuration
--------------------

The first time you want do deploy an application the configuration
should be set up in file ``deploy/deploy.cfg[.mako]``.

The deploy tool has four parts:

* ``[files]`` to deploy the GeoTIFF, ShapeFiles and so on.
* ``[databases]`` to deploy the database.
* ``[code]`` to deploy the application.
* ``[apache]`` to build the apache config.

An other important section is the ``[remote_hosts]`` where we
configure the demo and production hosts.

All the configuration option can be found in ``/etc/deploy/deploy.cfg``.

Get help with the command line ``deploy --help``.


Make configuration
-------------------

To use specific parameter values on the ``<target>`` server (for instance for
``host``), create dedicated ``<target>.mk`` files that will contain
those values. The deploy tool will then automatically detect those files and
use them when running the make command on the ``<target>`` server.

For instance a makefile for the ``prod`` server would be
named ``prod.mk`` and look like:

.. code:: make

    INSTANCE_ID = main
    VARS_FILE = vars_main.yaml

    include <project>.mk

If you have more than one instance on a domain name you can define
``apache_entry_point`` with something like ``/a_name/``. The trailing ``/``
is required in the ``apache_entry_point`` but not in the URL, than
`http://host/a_name` will work.


Prepare destination host
------------------------

On the destination host we just need that the schema postfixed with
``_static`` already exists.


Do the deploy
-------------

First of all be sure that the application on the source server work well!

Connect to your server using your SSH agent:

.. prompt:: bash

   ssh -A <dev_server>

Go into your project directory:

.. prompt:: bash

   cd /var/www/vhost/<project_vhost>/private/<project>

Deploy your project:

.. prompt:: bash

   .build/venv/bin/c2ctool deploy <host>

Where ``<host>`` is your destination host that you configured in the
``deploy/deploy.cfg`` file, e.g. ``demo``, ``prod``.


To deploy from dev to demo (advanced version)
---------------------------------------------

Build on the dev server:

.. prompt:: bash

  ssh -A <dev_server> # SSH agent forward is needed
  cd /var/www/vhost/<project_vhost>/private/<project>
  git pull origin master # update the code
  make -f main.mk build # configure c2cgeoportal

**Test on the dev server**

Deploy to the demo server:

.. prompt:: bash

  cd deploy
  sudo -u deploy deploy -r deploy.cfg demo

**Test on the demo server**


To deploy from demo to prod (advanced version)
----------------------------------------------

**Test on the demo server**

Deploy on the prod server:

.. prompt:: bash

  ssh -A <demo_server> # SSH agent forward is needed
  cd /var/www/vhost/<project_vhost>/private/<project>
  cd deploy
  sudo -u deploy deploy -r deploy.cfg prod

**Test on the prod server**
