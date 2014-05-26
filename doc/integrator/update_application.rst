.. _integrator_update_application:

Update a c2cgeoportal application
---------------------------------

Update the application code
~~~~~~~~~~~~~~~~~~~~~~~~~~~

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


Update c2cgeoportal
~~~~~~~~~~~~~~~~~~~

Upgrading an application to a new version of c2cgeoportal requires several
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
   To get the last dev version, replace <version> by "master".

   For example to get the ``versions.cfg`` file of version 1.4, type::

       wget https://raw.github.com/camptocamp/c2cgeoportal/1.4/c2cgeoportal/scaffolds/create/versions.cfg -O versions.cfg

3. Execute ``buildout`` (``eggs`` part) to get the new ``c2cgeoportal`` version:

   .. prompt:: bash

       ./buildout/bin/buildout install eggs

4. Apply the ``c2cgeoportal_update`` scaffold:

   .. prompt:: bash

       ./buildout/bin/pcreate --interactive -s c2cgeoportal_update ../<project_name> package=<package_name>

.. note::

    Don't add any '/' after the project name.

5. Do manual migration steps based on what's in the ``CONST_CHANGELOG.txt``
   file.

6. Clean your old eggs:

   .. prompt:: bash

        ./buildout/bin/buildout -c CONST_buildout_cleaner.cfg
        rm -rf old

   .. note::

      The first line will build the application and move the old eggs in a folder named `old/`.

7. Execute ``buildout`` to rebuild and install the application:

   .. prompt:: bash

       ./buildout/bin/buildout -c <buildout_config_file>

8. Update the database using the ``manage_db`` script:

   .. prompt:: bash

       ./buildout/bin/manage_db upgrade


   ``<package_name>`` is to be replaced by the name of the application module.
   See above for more information.

9. Add the new files in the repository:

    Get informations on the status of the repository:

    .. prompt:: bash

        git status

    Add the new files:

    .. prompt:: bash

        git add <file1> <file2> ...


Update CGXP
~~~~~~~~~~~

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
    git commit -m "Update cgxp submodule to <tag|branch>"

.. warning::

    We have a major issue here for applications under SVN. When SVN, as
    opposed to Git, is used for the application the version of CGXP is
    not fixed in the application. This means that each installation of
    an application may work with a different version of CGXP.

Do manual migration steps based on what's in the
`CHANGELOG <https://github.com/camptocamp/cgxp/blob/master/CHANGELOG.rst>`_.

Test and commit
~~~~~~~~~~~~~~~

* After the update process is done, do a final build of the application:

  .. prompt:: bash

    ./buildout/bin/buildout -c <buildout_config_file>

* Reload Apache configuration:

  .. prompt:: bash

    sudo /usr/sbin/apache2ctl graceful

* Test your application

* Commit your changes:

  .. prompt:: bash

    git commit -am "Update GeoMapFish to version <version>"
