.. _integrator_upgrade_application:

Upgrading a GeoMapFish application
==================================

.. warning::

    From version 1.6 we use Alembic instead of sqlachemy-migrate for database migration.
    Then to upgrade to GeoMapFish 1.6, integrators must start from the very last release
    of 1.5 since the upgrades to 1.5 are no longer available with the new tool.

Using the c2ctool command
-------------------------

The ``c2ctool`` is a tool to facilitate the common operations around GeoMapFish.


Easy updating an application code
---------------------------------

.. prompt:: bash

   make -f <makefile> update
   make -f <makefile> build

Where ``<makefile>`` is your user make file (``<user>.mk``).


Easy upgrading an application
-----------------------------

Verify that you have in your ``project.yaml.mako`` file the following ``template_vars``: ``package``, ``srid``, ``extent``, ``mobile_application_title``, ``apache_vhost``, for example:

.. code:: yaml

   ...
   template_vars:
       package: ${package}
       srid: ${srid}
       extent: 489246, 78873, 837119, 296543
       mobile_application_title: Mobile application
       apache_vhost: demo_geomapfish

In the ``setup.py`` be sure not to specify a ``c2cgeoportal`` version,
because it will prevent the installation of the new ``c2cgeoportal`` egg.

Then run (for Linux):

.. prompt:: bash

   .build/venv/bin/c2ctool upgrade <makefile> <target_version>

Where ``<makefile>`` is your user make file (``<user>.mk``),
``<target_version>`` is the version that you wish to upgrade to
(for the development version it should be 'master').

And follow the instructions.


.. note:: For Windows:

    If you are using Windows, you will have to execute some steps prior
    to the instructions hereunder:

    * Uninstall manually the old c2cgeoportal egg:

        ``.build/venv/Scripts/pip uninstall c2cgeoportal-win``

    * Clean / remove the generated files:

        ``make -f <makefile> clean``

    * Change the version in ``setup.py`` and ``CONST_requirements_windows.txt``
      to the version you wish to install.
    * Build your application:

        ``make -f <makefile> build``

    *  Put your modifications under git revision:

        ``git add setup.py``

        ``git add CONST_requirements_windows.txt``

        ``git commit -m "Upgrade c2cgeoportal version"``

        ``git push <remote> <branch>``

    * Follow the Windows instructions hereunder, note that you will have to use
      ``.build\venv\Scripts\...`` instead of ``.build\venv\bin\...`` in all given
      commands

    And, run:

    .. prompt:: bash

       .build/venv/Scripts/c2ctool upgrade --windows <makefile> \
            <target_version>


Easy upgrading an application from 1.5 to 1.6
---------------------------------------------

.. warning::

    Make sure that your database uses PostGIS 2. To migrate
    a PostGIS 1.5 database to PostGIS 2, please follow the
    `instructions <upgrade_application.html#migrating-database-to-postgis-2-x>`_.

Before upgrading your project, it is recommended to create a new
branch and to push it to the remote repository:

.. prompt:: bash

   git checkout -b 1.6
   git push origin 1.6

Create a ``project.yaml.mako`` file that contains:

.. code::

   project_folder: <folder>
   project_package: <package>
   host: <host>
   checker_path: /${instanceid}/wsgi/check_collector?
   template_vars:
        srid: <srid>
        mobile_application_title: 'Geoportal Mobile Application'

Where ``<folder>`` is the last element of the folder e.g. for
``/home/user/c2cgeoportal`` it will be ``c2cgeoportal``,

the ``<package>`` is the package name,

the ``<host>`` is the host to use for the Apache VirtualHost,

and the ``<srid>`` is the SRID of the project (e.g. 21781).


Add ``/project.yaml`` and ``/.build`` to the ``.gitignore`` file.

Get the right version of the egg:

.. prompt:: bash

   mkdir .build
   virtualenv --setuptools --no-site-packages .build/venv
   .build/venv/bin/pip install \
        --index-url http://pypi.camptocamp.net/pypi \
        'pip>=7' 'setuptools>=12'
   .build/venv/bin/pip install \
        --index-url http://pypi.camptocamp.net/pypi \
        --trusted-host pypi.camptocamp.net \
        --find-links http://pypi.camptocamp.net/internal-pypi/index/c2cgeoportal \
        https://github.com/camptocamp/pyramid_closure/archive/819bc43420b3cd924d8698c5a9606592c19dbb15.zip#egg=pyramid_closure \
        https://github.com/Pylons/pyramid/archive/1e02bbfc0df09259bf207112acf019c8dba44a90.zip#egg=pyramid \
        c2cgeoportal==<egg_version>

Where ``<egg_version>`` can be *1.6.0* for the first stable version.

Get the new required files from the c2cgeoportal templates:

.. prompt:: bash

   .build/venv/bin/pcreate --interactive -s c2cgeoportal_create \
        /tmp/<project> package=<package> srid=-1
   .build/venv/bin/pcreate --interactive -s c2cgeoportal_update \
        /tmp/<project> package=<package>
   cp /tmp/<project>/CONST_Makefile \
        /tmp/<project>/CONST_requirements_windows.txt \
        /tmp/<project>/CONST_dev-requirements.txt \
        /tmp/<project>/CONST_requirements.txt \
        /tmp/<project>/CONST_packages.yaml \
        /tmp/<project>/CONST_versions.txt \
        /tmp/<project>/CONST_vars.yaml \
        /tmp/<project>/<package>.mk \
        /tmp/<project>/vars_<package>.yaml .
   mkdir -p print/WEB-INF/classes
   cp /tmp/<project>/print/WEB-INF/classes/logback.xml.mako print/WEB-INF/classes
   rm -rf /tmp/<project>

Create your own ``<user>.mk``:

.. code::

   INSTANCE_ID = <instanceid>
   DEVELOPMENT = TRUE

   include <package>.mk

In the ``setup.py`` file make sure that ``c2cgeoportal`` is listed in the ``install_requires`` parameter.

Add all your new files in git and commit them:

.. prompt:: bash

   git add project.yaml.mako CONST_* <package>.mk \
        vars_<package>.yaml <user>.mk .gitignore
   git rm project.yaml
   git commit -m "Initialize the upgrade to 1.6"

Start the c2ctool upgrade:

.. prompt:: bash

   rm -rf .build/*
   make -f <makefile> project.yaml .build/requirements.timestamp
   .build/venv/bin/c2ctool upgrade <makefile> <target_version>

Where ``<makefile>`` is your user make file (``<user>.mk``),
``<target_version>`` is the version that you wish to upgrade to
(for the development version it should be 'master').

And follow the instructions.


Upgrading CGXP (advanced version)
---------------------------------

To upgrade CGXP to a release tag (like 1.3.0) use the following:

.. prompt:: bash

    cd <package>/static/lib/cgxp
    git fetch
    git checkout <tag>
    git submodule sync
    git submodule update --init

``<package>`` is to be replaced by the name of your application package name,
``<tag>`` is the name of the release (in Git we use a tag),

To upgrade CGXP to a version branch (like 1.3) use the following:

.. prompt:: bash

    cd <package>/static/lib/cgxp
    git fetch
    git checkout <branch>
    git pull origin <branch>
    git submodule sync
    git submodule update --init

``<package>`` is to be replaced by the name of your application package name,
``<branch>`` is the name of the version (in Git we use a branch).

If the application code is under Git you also need to update the application
to reference the new commit for the cgxp submodule:

.. prompt:: bash

    cd -
    git add <package>/static/lib/cgxp

.. warning::

    We have a major issue here for applications under SVN. When SVN, as
    opposed to Git, is used for the application the version of CGXP is
    not fixed in the application. This means that each installation of
    an application may work with a different version of CGXP.

Do manual migration steps based on what's in the
`CHANGELOG <https://github.com/camptocamp/cgxp/blob/master/CHANGELOG.rst>`_.


Upgrading c2cgeoportal (advanced version)
-----------------------------------------

Upgrading an application to a new release of c2cgeoportal requires several
steps:

1. It's good to start an upgrade in a clean repository, then:

   * See what's not commited:

     .. prompt:: bash

        git status

   * Reset non commited changes:

     .. prompt:: bash

        git reset --hard

   * Remove all untracked files and directories:

     .. prompt:: bash

        git clean -f -d

2. Now, to update the application's other dependencies,
   get the ``versions`` file:

   .. prompt:: bash

       wget https://raw.github.com/camptocamp/c2cgeoportal/<version>/c2cgeoportal/scaffolds/update/CONST_versions.txt -O CONST_versions.txt
       wget https://raw.github.com/camptocamp/c2cgeoportal/<version>/c2cgeoportal/scaffolds/update/CONST_requirements.txt -O CONST_requirements.txt

   Replace ``<version>`` by a version number (branch) or release number (tag).
   To get the last dev version, replace ``<version>`` by ``master``.

   For example to get the ``versions`` file of version 1.6, type:

   .. prompt:: bash

       wget https://raw.github.com/camptocamp/c2cgeoportal/1.6/c2cgeoportal/scaffolds/update/CONST_versions.txt -O CONST_versions.txt
       wget https://raw.github.com/camptocamp/c2cgeoportal/1.6/c2cgeoportal/scaffolds/update/CONST_requirements.txt -O CONST_requirements.txt

3. Execute ``make`` to get the new ``c2cgeoportal`` version:

   .. prompt:: bash

        make -f <user>.mk build

4. Apply the ``c2cgeoportal_update`` scaffold:

   .. prompt:: bash

       .build/venv/bin/pcreate --interactive -s c2cgeoportal_update ../<project> package=<package>

   .. note::

      Don't add any '/' after the project name.

   .. note::

      ``<package>`` is to be replaced by the name of the application module.
      See above for more information.

   .. note:: For Windows:

      The ``$PROJECT/static/mobile/touch.tar.gz`` archive must be uncompressed and then removed.

      If it's not present, proceed as follows:

      * Get Sencha Touch at http://cdn.sencha.io/touch/sencha-touch-2.3.1-gpl.zip.
      * Unzip it.
      * Open a terminal and go to the folder where you have unzipped Sencha Touch.
      * Run ``sencha generate app TempApp C:/tmp/TempApp``.
      * Copy the ``C:/tmp/TempApp/touch`` to your project in the folder ``<package>/static/mobile/touch``.
      * Remove the generated app (``C:/tmp/TempApp``).

5. Do manual migration steps based on what's in the ``CONST_CHANGELOG.txt``
   file.

6. Execute ``make`` to rebuild and install the application:

   .. prompt:: bash

        make -f <user>.mk build

7. Upgrade the database using the ``alembic`` script:

   .. prompt:: bash

       .build/venv/bin/alembic upgrade head
       .build/venv/bin/alembic -c alembic_static.ini upgrade head


8. Add the new files in the repository:

    Get informations on the status of the repository:

    .. prompt:: bash

        git status

    Add the new files:

    .. prompt:: bash

        git add <file1> <file2> ...


Migrating database to Postgis 2.x
---------------------------------

When migrating the database from Postgis 1.x to 2.x using the postgis_restore.pl
script, the table ``<schema_name>.layer`` (and related index and foreign key)
will cause some problem because the name is conflicting with an existing table
with the same name in the Postgis topology schema.

The easiest workaroud is to rename the table, index and foreign key before
creating the Postgres dump and reimporting the data with postgis_restore.pl.
Then renaming them back after the restoration.

First rename all the conflicting items:

   .. code:: sql

      ALTER INDEX <schema_name>.layer_pkey RENAME TO layertmp_pkey;
      ALTER TABLE <schema_name>.layer ADD CONSTRAINT layertmp_id_fkey FOREIGN KEY (id) REFERENCES <schema_name>.treeitem(id);
      ALTER TABLE <schema_name>.layer DROP CONSTRAINT layer_id_fkey;
      ALTER TABLE <schema_name>.layer RENAME TO layertmp;

.. note::
  We can't rename a foreign key, we have to create a new one before removing the
  old one.

Then you can create the database dump and run postgis_restore.pl to restore
it in your Postgis 2.x database (exemple using Postgres 9.1, Postgis 2.1):

    .. prompt:: bash

       sudo -u postgres createdb -T template_postgis <database_name>
       perl /usr/share/Postgresql/9.1/contrib/Postgis-2.1/postgis_restore.pl -v <dump_name>.dump | sudo -u postgres psql <database_name>

.. note::
  If you dont have a template_postgis database, you need to add Postgis support
  manually, refer to :ref:`integrator_install_application_create_database`.

Once restored, set the original names back:

   .. code:: sql

      ALTER TABLE <schema_name>.layertmp RENAME TO layer;
      ALTER INDEX <schema_name>.layertmp_pkey RENAME TO layer_pkey;
      ALTER TABLE <schema_name>.layer ADD CONSTRAINT layer_id_fkey FOREIGN KEY (id) REFERENCES <schema_name>.treeitem(id);
      ALTER TABLE <schema_name>.layer DROP CONSTRAINT layertmp_id_fkey;

Edition
+++++++

If you migrate editable tables, you need to modify the geometry data types to
match Postgis 2 new Typmod.

Example for a layer with ``Point`` geometries and a 21781 projection:

   .. code:: sql

      ALTER TABLE my_table ALTER COLUMN geom SET DATA TYPE geometry(Point, 21781);

To help doing it on several tables at once, here is a function and an example
of usage:

   .. code:: sql

      CREATE OR REPLACE FUNCTION migrategeomtopostgis2(_tablename text, _geomcolumn text, _geomtype text, _srid int) RETURNS void AS $$
      DECLARE
      _cleangeomtype text;
      BEGIN
      _cleangeomtype := initcap(lower(_geomtype));
      EXECUTE ' ALTER TABLE ' || _tablename || ' ALTER COLUMN ' || _geomcolumn || ' SET DATA TYPE geometry(' || _cleangeomtype || ', ' || _srid || ')';
      EXECUTE ' ALTER TABLE ' || _tablename || ' DROP CONSTRAINT IF EXISTS enforce_dims_' || _geomcolumn;
      EXECUTE ' ALTER TABLE ' || _tablename || ' DROP CONSTRAINT IF EXISTS enforce_geotype_' || _geomcolumn;
      EXECUTE ' ALTER TABLE ' || _tablename || ' DROP CONSTRAINT IF EXISTS enforce_srid_' || _geomcolumn;
      END
      $$
      LANGUAGE PLPGSQL;

      select migrategeomtopostgis2(f_table_schema || '.' || f_table_name, f_geometry_column, type, srid) from geometry_columns where f_table_schema IN ('schema1','schema2','schema3');

Where ``schemaX`` are the names of the schemas where the tables you want to
convert are.

You need to create the ``migrategeomtopostgis2`` function first (simply copy
and input the function definition above in your terminal), then execute the
``select`` (adapted to your need).

If the following constraints do not exist, ``enforce_dims_<geometry_column>``,
``enforce_geotype_<geometry_column>`` or ``enforce_srid_<geometry_column>``,
the query will output some ``NOTICE``, which may mean you have used other
names for your constraints, so you should have a look at the corresponding
tables and remove the constraints manually.

If you have created views depending on the modified table, you need to drop
and recreate all the related views.

Here are some helper queries to generate .sql files containing the views DROP
and CREATE SQL queries:

   .. code:: sql

      copy ( select 'CREATE OR REPLACE VIEW ' || schemaname || '.' || viewname || ' AS ' || regexp_replace(definition,E'[\\n\\r]+', ' ', 'g') from pg_catalog.pg_views where schemaname IN ('schema1','schema2','schema3') ) to '/tmp/view_create.sql';
      copy ( select 'DROP VIEW ' || schemaname || '.' || viewname || ' CASCADE;' from pg_catalog.pg_views where schemaname IN ('schema1','schema2','schema3') ) to '/tmp/view_drop.sql';


Test and commit
---------------

* After the upgrade process is done, do a final build of the application:

  .. prompt:: bash

    make -f <user>.mk build

* Test your application.

* Test the checker at `http://<application base>/wsgi/check_collector?type=all`.

* Commit your changes:

  .. prompt:: bash

    git commit -am "Upgrade to GeoMapFish <release>"
