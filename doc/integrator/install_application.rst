.. _integrator_install_application:

Install an existing application
===============================

Database
--------

Any c2cgeoportal application requires a PostgreSQL/PostGIS database. The
application works with its own tables, which store users, layers, etc. These
tables are located in a specific schema of the database.

.. note::

    Multiple specific schemas are actually used in a parent/child architecture.

If the application has MapServer layers linked to PostGIS tables, these tables
and the application-specific tables must be in the same database, preferably in
separate schemas. This is required for layer access control (*restricted
layers*), where joining user/role tables to PostGIS layer tables is necessary.

Create the database
~~~~~~~~~~~~~~~~~~~

To create the database you can use::

    $ sudo -u postgres createdb <db_name> -T template_postgis

with ``<db_name>`` replaced by the actual database name.

To create the application-specific schema use::

    $ sudo -u postgres psql -c "CREATE SCHEMA <schema_name>;" <db_name>

with ``<db_name>`` and ``<schema_name>`` replaced by the actual database name,
and schema name, respectively.

Create a database user
~~~~~~~~~~~~~~~~~~~~~~

You probably want to create a specific database user for the application. This
can be done with this command, by default ``<db_user>`` is ``www-data``, 
already exists on camptocamp servers::

    $ sudo -u postgres createuser -P <db_user>

Give the rights to the user::

    $ sudo -u postgres psql <db_name>
    GRANT ALL ON SCHEMA <schema_name> TO "<db_user>";
    GRANT ALL ON ALL TABLES IN SCHEMA <schema_name> TO "<db_user>";
    \q 

Application
-----------

System requirements
~~~~~~~~~~~~~~~~~~~

To install a c2cgeoportal application you need to have the following installed
on your system:

* Subversion (or whatever VCS is used for the application)
* Git
* Python 2.7 or 2.6 (2.5 is not supported)
* Oracle Java SE Development Kit 6 or 7

Additional notes for Windows users:

    For Subversion install `Turtoise SVN <http://turtoisesvn.net>`_.

    For Git look at GitHub's `Set Up Git page
    <http://help.github.com/win-set-up-git/>`_. You won't need to set up SSH
    keys, so you only need to follow the firt section of this page.

    Once Git is installed use Git Bash for all the shell commands provided in
    this documentation. You'll need to make sure the Turtoise, Python, and Java
    folders are on the ``PATH``. For example if you have Python installed under
    ``C:\Python26`` you can use ``export PATH=$PATH:/c/Python26`` to add Python
    to your ``PATH``.

    You need to install the ``psycopg2`` Python package in the main Python
    environment (e.g. ``C:\Python26``). Use an installer (``.exe``) from the
    `Stickpeople Project
    <http://www.stickpeople.com/projects/python/win-psycopg/>`_.

Get the application source tree
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


The Git commands to get the code from a remote repository is named ``clone``::

    git clone <url_to_the_remote_repository> <local_folder>

If you still use SVN::

    svn co https://project.camptocamp.com/svn/<my_project>/trunk <my_project>

We also have to download the ``submodule`` dependencies
(two levels in our case)::

    git submodule update --init
    git submodule foreach git submodule update --init

.. note::
   We don't use the ``--recursive`` because we wouldn't have the third level 
   of submodule who ass son unneeded dependencies and duplicate code 
   like OpenLayers.

.. important::
   the git command don't respect all the unix rights, than it you checkout 
   your project in a common folder like ``/var/www/<vhost>/private`` it 
   will be fully writable only for you. To fix that you can do in your project
   ``chmod -R g+w .``.

Buildout boostrap 
~~~~~~~~~~~~~~~~~

The `Buildout <http://pypi.python.org/pypi/zc.buildout/1.5.2>`_ tool is used to
build, install, and deploy c2cgeoportal applications.

Prior to using Buildout, its ``boostrap.py`` script should be run at the root
of the application::

  $ python bootstrap.py --version 1.5.2 --distribute --download-base \
        http://pypi.camptocamp.net/ --setup-source \
        http://pypi.camptocamp.net/distribute_setup.py

This step is done only once for installation/instance of the application.

Install the application
~~~~~~~~~~~~~~~~~~~~~~~

If not already existing, create a ``buildout_<user>.cfg`` file, 
that will contain your application special
configuration::

    [buildout]
    extends = buildout.cfg
    extensions -= buildout.dumppickedversions

    [vars]
    instanceid = <instanceid>

    [jsbuild]
    compress = False

    [cssbuild]
    compress = false

The ``<instanceid>`` should be unique on the server, the username is a good 
choice or something like ``<username>-<sub-project>`` in case of parent/children project.

Add it to Git::

    $ git add buildout_<user>.cfg; git commit -m "add user buildout"

Or to SVN::

    $ svn add buildout_<user>.cfg; svn commit -m "add user buildout"

Then you can build and install the application with the command::

    $ ./buildout/bin/buildout -c buildout_<user>.cfg

This previous command will do many things like:

  * download and install the project dependencies,

  * adapt the application configuration to your environment,

  * build the javascript and css resources into compressed files,

  * compile the translation files.

Once the application is built and installed, you now have to create and
populate the application tables, and directly set the version (details later)::

    $ ./buildout/bin/create_db --iniconfig production.ini --populate
    $ ./buildout/bin/manage_db -c production.ini -n <package_name> version_control \
    `./buildout/bin/manage_db -c production.ini -n <package_name> version`

A c2cgeoportal application makes use of ``sqlalchemy-migrate`` to version
control a database. It relies on a **repository** in source code which contains
upgrade scripts that are used to keep the database up to date with the
latest repository version.

After having created the application tables with the previous command,
the current database version correspond to the latest version available in
the repository, which can be obtained with::

    $ ./buildout/bin/manage_db -c production.ini -n <package_name> version
    <current_version>
    $

Now that we know the latest version of the repository (= current version of the
database), we need to actually put the database under version control.
A dedicated table is used by sqlalchemy-migrate to store the current version
of the database. This table should be named ``version_<package_name>``.

So let's create this table and set the current version of the database
(obtained from the previous command)::

    $ ./buildout/bin/manage_db -c production.ini -n <package_name> version_control <current_version>

The database is now under version control, you can check that the current
database version is correct with the command::

    $ ./buildout/bin/manage_db -c production.ini -n <package_name> db_version

Note that future schema upgrades will only be done via change scripts from the
repository, and they will automatically increment the ``db_version``.

Your application is now fully set up and the last thing to do is to configure
apache so that it will serve your WSGI c2cgeoportal application. So you just
have to include the application apache configuration available in the
``apache`` directory. On servers managed by Camptocamp, add a ``.conf`` file in
``/var/www[/vhost]/<projectname>/conf/`` with the following content::

    Include /<path_to_your_project>/apache/*.conf

Reload apache configuration and you're done::

    $ sudo apache2ctl graceful

Your application should be available at:
``http://<hostname>/<instanceid>/wsgi``.
