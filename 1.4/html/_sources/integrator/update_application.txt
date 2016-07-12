.. _integrator_update_application:

Update a c2cgeoportal application
---------------------------------

Update the application code
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To get the changes done by other people, we need to ``pull`` the new code::

    git pull
    git submodule sync
    git submodule update --init
    git submodule foreach git submodule sync
    git submodule foreach git submodule update --init

.. note::
   The submodule command is used to have the right version of CGXP.

If you still use SVN::

    svn update

.. caution::
   This command will not update CGXP, and c2cgeoportal is not able to
   fix the revision of CGXP.


Update c2cgeoportal
~~~~~~~~~~~~~~~~~~~

Upgrading an application to a new version of c2cgeoportal requires several
steps:

1. It's good to start an update in a clean repository, then:

   * See what's not commited::

        git status

   * Reset non commited changes::

        git reset --hard

   * Remove all untracked files and directories::

        git clean -f -d

2. If you are upgrading from version 1.3.1 or older, make your application
   require the new version of the ``c2cgeoportal`` package by editing the
   application's Buildout config (``buildout.cfg``) and change the version of
   ``c2cgeoportal`` in the ``[versions]`` section. Make sure the version
   specifications in ``setup.py`` and ``buildout.cfg`` do not conflict.

3. Now, to update the application's other dependencies,
   get the new ``version.cfg`` file::

       wget https://raw.github.com/camptocamp/c2cgeoportal/<version>/c2cgeoportal/scaffolds/create/versions.cfg -O versions.cfg

   Replace ``<version>`` by a version number (branch) or release number (tag).
   To get the last dev version, replace <version> by "master".

   For example to get the ``versions.cfg`` file of version 1.4, type::

       wget https://raw.github.com/camptocamp/c2cgeoportal/1.4/c2cgeoportal/scaffolds/create/versions.cfg -O versions.cfg

4. Execute ``buildout`` (``eggs`` part) to get the new ``c2cgeoportal`` version::

       $ ./buildout/bin/buildout install eggs

5. Apply the ``c2cgeoportal_update`` scaffold::

       $ ./buildout/bin/pcreate --interactive -s c2cgeoportal_update \
         ../<project_name> package=<package_name>

.. note::
    Don't add any '/' after the project name.

.. note::
   For ``c2cgeoportal`` 0.6 and lower::

       $ ./buildout/bin/paster create --template=c2cgeoportal_update \
         --output-dir=.. <project_name> package=<package_name>

   ``<project_name>`` is the name of the application's root directory,
   including ``development.ini``, etc.  ``<package_name>`` is the name of the
   application's root Python module, i.e. the name of the subdir including the
   application's Python code. If unsure, see the ``name`` argument to the
   ``setup`` call in the application's ``setup.py`` file.

6. Do manual migration steps based on what's in the ``CONST_CHANGELOG.txt``
   file.

7. If it still exists, you can now entirely remove the ``[versions]`` section in your
   ``buildout.cfg`` file.

8. Execute ``buildout`` to rebuild and install the application::

       $ ./buildout/bin/buildout -c <buildout_config_file>

9. Update the database using the ``manage_db`` script::

       $ ./buildout/bin/manage_db upgrade

   .. note::

        With c2cgeoportal 0.7 and lower, or if the app section is not ``[app:app]``
        in the production.ini file, you need to specify the app name on the
        ``manage_db`` command line. For example, the above command would be as
        follows::

           $ ./buildout/bin/manage_db -n <package_name> upgrade

   ``<package_name>`` is to be replaced by the name of the application module.
   See above for more information.

10. Add the new files in the repository:

   Get informations on the status of the repository::

        git status

   Add the new files::

        git add <file1> <file2> ...


Update CGXP
~~~~~~~~~~~

To update CGXP to a release tag (like 1.3.0) use the following::

    cd <package>/static/lib/cgxp
    git fetch
    git checkout <tag>
    git submodule sync
    git submodule update --init

To update CGXP to a version branch (like 1.3) use the following::

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
to reference the new commit for the cgxp submodule::

    $ cd ..
    $ git add cgxp
    $ git commit -m "Update cgxp submodule"

.. warning::

    We have a major issue here for applications under SVN. When SVN, as
    opposed to Git, is used for the application the version of CGXP is
    not fixed in the application. This means that each installation of
    an application may work with a different version of CGXP.

Do manual migration steps based on what's in the
`CHANGELOG <https://github.com/camptocamp/cgxp/blob/master/CHANGELOG.rst>`_.

Test and commit
~~~~~~~~~~~~~~~

* After the update process is done, do a final build of the application::

        ./buildout/bin/buildout -c <buildout_config_file>

* Reload Apache configuration::

        sudo /usr/sbin/apache2ctl graceful

* Test your application

* Commit your changes::

        git commit -am "Update GeoMapFish to version <version>"
