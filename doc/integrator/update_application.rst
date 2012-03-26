.. _integrator_update_application:

Update a c2cgeoportal application
=================================

Update the application code
---------------------------

To get the changes done by other people, we need to ``pull`` the new code::

    git pull
    git submodule sync
    git submodule update
    git submodule foreach git submodule sync
    git submodule foreach git submodule update

.. note::
   The submodule command is used to have the right version of CGXP.

If you still use SVN::

    svn update

.. caution::
   This command will not updates CGXP, and c2cgeoportal is not able to
   fix the revision of CGXP.

Update c2cgeoportal
-------------------

Upgrading an application to a new version of c2cgeoportal requires several
steps:

1. Set a new version for the ``c2cgeoportal`` package. For this edit the
   application's buildout config file and change the version for the
   ``c2cgeoportal`` dependency in the ``[versions]`` section.
2. Execute ``buildout`` to download and install the new version of the
   ``c2cgeoportal`` package::

       $ ./buildout/bin/buildout -c <buildout_config_file>

   At this point you can verify that the ``buildout/eggs`` directory
   includes the new version of the ``c2cgeoportal`` package.

3. Apply the ``c2cgeoportal_update`` skeleton (``IOError: No egg-info directory
   found (...)`` can be ignored)::

       $ ./buildout/bin/paster create --template=c2cgeoportal_update \
         --output-dir=.. <project_name> package=<package_name>

4. Do manual migration steps based on what's in the ``CONST_CHANGELOG.txt``
   file.
5. Update the database using the ``manage_db`` script::

        $ ./buildout/bin/manage_db -c production.ini -n <package_name> upgrade

   ``<package_name>`` is to be replaced by the name of your application
   package. If unsure, see the ``name`` argument to the ``setup`` call in the
   application's ``setup.py`` file.

6. Execute ``buildout`` one more time to rebuild and reinstall the
   application::

       $ ./buildout/bin/buildout -c <buildout_config_file>

Update CGXP
-----------

To update CGXP in the application use the following::

    $ cd <package_name>/static/lib/cgxp
    $ git pull origin master
    $ git submobule update

``<package_name>`` is to be replaced by the name of your application package.
If unsure, see the ``name`` argument to the ``setup`` call in the application's
``setup.py`` file.

If the application code is under Git you also need to update the application
to reference the new commit for the cgxp submodule::

    $ cd ..
    $ git commit -m "Update cgxp submodule"

.. warning::

    We have a major issue here for applications under SVN. When SVN, as
    opposed to Git, is used for the application the version of CGXP is
    not fixed in the application. This means that each installation of
    an application may work with a different version of CGXP.
