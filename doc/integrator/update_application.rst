.. _integrator_update_application:

Updating a GeoMapFish application
=================================

.. warning::

    From version 1.6 we use Alembic instead of sqlachemy-migrate for database migration.
    Than to upgrade to GeoMapFish 1.6, integrators must start from the very last release
    of 1.5 since the upgrades to 1.5 are no longer available with the new tool.

User the easy c2c tool (experimantal)
-------------------------------------

The ``c2ctool`` is a tool to facilitate the common operations around GeoMapFish,
to use it from a c2cgeoportal 1.4 you should at first get the c2cgeoportal 1.5:

.. prompt:: bash

   wget https://raw.github.com/camptocamp/c2cgeoportal/<version>/c2cgeoportal/scaffolds/create/versions.cfg -O versions.cfg
    ./buildout/bin/buildout install eggs

Replace ``<version>`` by a version number (branch) or release number (tag).
To get the last dev version, replace ``<version>`` by ``master``.


Easy updating an application code (experimental)
------------------------------------------------

.. prompt:: bash

   ./buildout/bin/c2ctool update <buildout_file>

Where ``<buildout_file>`` is your user buildout file.


Easy upgrading an application (experimental)
--------------------------------------------

Create a ``project.yaml.in`` file that contains:

.. code::

   project_folder: <folder>
   project_package: <package>
   host: <host>
   checker_path: /${instanceid}/wsgi/check_collector?
   template_vars:
        mobile_application_title: 'Geoportal Mobile Application'

Where ``<folder>`` is the last element of the folder e.g. for
``/home/user/c2cgeoportal`` it will be ``c2cgeoportal``,

the ``<package>`` is the package name,

and the ``<host>`` is the host to use for the Apache VirtualHost.


Add ``project.yaml`` in the ``.gitignore`` file.

.. prompt:: bash

   ./buildout/bin/c2ctool upgrade <buildout_file> <target_version>

Where ``<buildout_file>`` is your user buildout file,
``<target_version>`` is the version that you wish to update to.

And follow the instructions.


Updating an application code
----------------------------

To get the changes done by other people, we need to ``pull`` the new code:

.. prompt:: bash

    git pull
    git submodule sync
    git submodule update --init
    git submodule foreach git submodule sync
    git submodule foreach git submodule update --init

.. note::

   The submodule command is used to have the right version of CGXP.

.. note::

   If you update the code after an upgrade of the application it is
   recommended to clean your old eggs (this will also build your application):

  .. prompt:: bash

        ./buildout/bin/buildout -c CONST_buildout_cleaner.cfg
        rm -rf old


Updating CGXP
-------------

To update CGXP to a release tag (like 1.3.0) use the following:

.. prompt:: bash

    cd <package>/static/lib/cgxp
    git fetch
    git checkout <tag>
    git submodule sync
    git submodule update --init

To update CGXP to a version branch (like 1.3) use the following:

.. prompt:: bash

    cd <package>/static/lib/cgxp
    git fetch
    git checkout <branch>
    git pull origin <branch>
    git submodule sync
    git submodule update --init

``<package>`` is to be replaced by the name of your application package name,
``<tag>`` is the name of the release (in Git we use a tag),
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


Updating c2cgeoportal
---------------------

Upgrading an application to a new release of c2cgeoportal requires several
steps:

1. It's good to start an update in a clean repository, then:

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
   get the ``version.cfg`` file:

   .. prompt:: bash

       wget https://raw.github.com/camptocamp/c2cgeoportal/<version>/c2cgeoportal/scaffolds/create/versions.cfg -O versions.cfg

   Replace ``<version>`` by a version number (branch) or release number (tag).
   To get the last dev version, replace ``<version>`` by ``master``.

   For example to get the ``versions.cfg`` file of version 1.5, type:

   .. prompt:: bash

       wget https://raw.github.com/camptocamp/c2cgeoportal/1.5/c2cgeoportal/scaffolds/create/versions.cfg -O versions.cfg

3. Execute ``buildout`` (``eggs`` part) to get the new ``c2cgeoportal`` version:

   .. prompt:: bash

       ./buildout/bin/buildout install eggs

4. Apply the ``c2cgeoportal_update`` scaffold:

   .. prompt:: bash

       ./buildout/bin/pcreate --interactive -s c2cgeoportal_update ../<project_name> package=<package_name>

   .. note::

      Don't add any '/' after the project name.

   .. note::

      ``<package_name>`` is to be replaced by the name of the application module.
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

6. Clean your old eggs:

   .. prompt:: bash

        ./buildout/bin/buildout -c CONST_buildout_cleaner.cfg
        rm -rf old

   .. note::

      The first line will build the application and move the old eggs in a folder named ``old/``.

7. Execute ``buildout`` to rebuild and install the application:

   .. prompt:: bash

       ./buildout/bin/buildout -c <buildout_config_file>

8. Update the database using the ``alembic`` script:

   .. prompt:: bash

       ./buildout/bin/alembic upgrade head


9. Add the new files in the repository:

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

   .. prompt:: sql

      ALTER INDEX layer_pkey RENAME TO layertmp_pkey;
      ALTER TABLE layer ADD CONSTRAINT layertmp_id_fkey FOREIGN KEY (id) REFERENCES treeitem(id);
      ALTER TABLE layer DROP CONSTRAINT layer_id_fkey;
      ALTER TABLE layer RENAME TO layertmp;

.. note::
  We can't rename a foreign key, we have to create a new one before removing the 
  old one.

Then you can create the database dump and run postgis_restore.pl to restore 
it in your Postgis 2.x database (exemple using Postgres 9.1, Postgis 2.1):

    .. prompt:: bash
      
       createdb -T template_postgis <database_name>
       perl /usr/share/Postgresql/9.1/contrib/Postgis-2.1/postgis_restore.pl -v <dump_name>.dump | psql <database_name>

.. note::
  If you dont have a template_postgis database, you need to add Postgis support 
  manually, refer to :ref:`integrator_install_application_create_database`.

Once restored, set the original names back:

   .. prompt:: sql

      ALTER TABLE layertmp RENAME TO layer;
      ALTER INDEX layertmp_pkey RENAME TO layer_pkey;
      ALTER TABLE layer ADD CONSTRAINT layer_id_fkey FOREIGN KEY (id) REFERENCES treeitem(id);
      ALTER TABLE layer DROP CONSTRAINT layertmp_id_fkey;


Test and commit
---------------

* After the update process is done, do a final build of the application:

  .. prompt:: bash

    ./buildout/bin/buildout -c <buildout_config_file>

* Reload Apache configuration:

  .. prompt:: bash

    sudo /usr/sbin/apache2ctl graceful

* Test your application.

* Test the checker at `http://<application base>/wsgi/check_collector?type=all`.

* Commit your changes:

  .. prompt:: bash

    git commit -am "Update to GeoMapFish <release>"
