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

    sudo -u postgres createdb <db_name> -T template_postgis

with ``<db_name>`` replaced by the actual database name.

To create the application-specific schema use::

    sudo -u postgres psql -c "CREATE SCHEMA <schema_name>;" <db_name>

with ``<db_name>`` and ``<schema_name>`` replaced by the actual database name,
and schema name, respectively.

Create a database user
~~~~~~~~~~~~~~~~~~~~~~

You probably want to create a specific database user for the application. This
can be done with this command, by default ``<db_user>`` is ``www-data``::

    sudo -u postgres createuser -P <db_user>

Give the rights to the user::

    $ sudo -u postgres psql <db_name>
    GRANT ALL ON SCHEMA <schema_name> TO "<db_user>";
    GRANT ALL ON ALL TABLES IN SCHEMA <schema_name> TO "<db_user>";
    \q 

Application
-----------

c2cgeoportal applications are installed from source. This section assumes
that you have local copy on the application source tree (a local clone if
you use Git).

Buildout boostrap 
~~~~~~~~~~~~~~~~~

The `Buildout <http://pypi.python.org/pypi/zc.buildout/1.5.2>`_ tool is used to
build, install, and deploy c2cgeoportal applications.

Prior to using Buildout, its ``boostrap.py`` script should be run at the root
of the application::

  python bootstrap.py --version 1.5.2 --distribute --download-base \
        http://pypi.camptocamp.net/ --setup-source \
        http://pypi.camptocamp.net/distribute_setup.py

This step is done only once for installation/instance of the application.

Install the application
~~~~~~~~~~~~~~~~~~~~~~~

If not already existing, create an application configuration file to adapt
the application to your environment and commit, than create file 
``buildout_$USER.cfg`` that contains::

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
choice or some think like ``<username>-<sub-project>`` in case of parent/children project.

Add it to SVN::

    $ svn add buildout_$USER.cfg: svn commit "add user buildout" buildout_$USER.cfg

Then you can build and install the application with the command::

    $ ./buildout/bin/buildout -c buildout_$USER.cfg

This previous command will do many things like:

  * download and install the project dependencies,

  * adapt the application configuration to your environment,

  * build the javascript and css resources into compressed files,

  * compile the translation files.

Once the application is built and installed, you now have to create and
populate the application tables, and directly set the version (details later)::

    $ buildout/bin/create_db --iniconfig production.ini --populate
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
``apache`` directory, in camptocamp managed hosts it'd in the folder 
``/var/www[/vhost]/<projectname>/conf/`` by using the directive::

    Include /<path_to_your_project>/apache/*.conf

Reload apache configuration and you're done::

    $ sudo apache2ctl graceful

Your application should be available under the url:
``http://<hostname>/<instanceid>/wsgi``.
