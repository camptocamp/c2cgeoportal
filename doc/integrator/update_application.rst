.. _integrator_update_application:

Update a c2cgeoportal application
=================================

Update the application code
---------------------------

To update the application use::

    $ svn update

or::

    $ git pull origin master

depending on the VCS used for that application.

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

If the application code is under SVN the ``[cgxp-install]`` part was certainly
used for the initial installation of CGXP (under
``<package_name>/static/lib/cgxp``). This part did ``git clone`` of CGXP, so
``<package_name>/static/lib/cgxp`` is a clone of
https://github.com/camptocamp/cgxp.git. So to update CGXP for the application
you can use the following Git commands::

    $ cd <package_name>/static/lib/cgxp
    $ git pull origin master
    $ git submobule update

``<package_name>`` is to be replaced by the name of your application package.
If unsure, see the ``name`` argument to the ``setup`` call in the application's
``setup.py`` file.

If the application code is under Git ... (TO COMPLETE)
