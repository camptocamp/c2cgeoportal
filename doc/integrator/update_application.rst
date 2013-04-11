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

1. Make your application require the new version of the ``c2cgeoportal``
   package. For that edit the application's ``setup.py`` file, and change the
   ``c2cgeoportal`` requirement as appropriate. For example, if you were
   upgrading to ``c2cgeoportal`` version 0.7, you'd use this::

       c2cgeoportal>=0.7,<=0.7.99

   You may also need to edit the application's Buildout config
   (``buildout.cfg``) and change the version of ``c2cgeoportal`` in the
   ``[versions]`` section. Make sure the version specifications in ``setup.py``
   and ``buildout.cfg`` do not conflict.

2. Now, if you want or need to update the application's other dependencies,
   edit the application's Buildout config (``buildout.cfg``), and remove all
   the lines from the ``[versions]`` section. Emptying the ``[versions]``
   section is necessary for getting new dependency versions using ``buildout
   -n`` (see the next step). Keep only the new version of c2cgeoportal to use::

       [versions]
       c2cgeoportal = <version to install>

.. note::

   If the ``CONST_buildout.cfg`` file does not already have::
   
       distribute = 0.6.22
       zc.buildout = 1.5.2

   in its ``[versions]`` section (c2cgeoportal < 1.3), add them to the
   ``[versions]`` section of the ``buildout.cfg`` file.
   
   If you upgrade from c2cgeoportal < 1.3.2, you should also keep/add::

       [versions]
       ...
       zc.recipe.egg = 1.3.2

3. Execute ``buildout`` with the ``-n`` flag to download and install new
   versions of dependencies (``c2cgeoportal`` included)::

       $ ./buildout/bin/buildout -n -c <buildout_config_file>

   At this point you can verify that the ``buildout/eggs`` directory
   includes the new version of the ``c2cgeoportal`` package.

4. Copy the dependency version lines (of the form ``Mako = 0.7.2``)
   from the ``buildout`` command output and paste them into the ``[versions]``
   part of ``buildout.cfg``. Then, apply the following corrections
   (to work around bugs in ``buildout.dumppickedversions``)::

    -Mako = x.y.z
    +mako = x.y.z
    -Markdown = x.y.z
    +markdown = x.y.z
    -SQLAHelper = x.y.z
    +sqlahelper = x.y.z
    -SQLAlchemy = x.y.z
    +sqlalchemy = x.y.z
    -Tempita = x.y.z
    +tempita = x.y.z

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

7. Execute ``buildout`` to rebuild and install the application::

       $ ./buildout/bin/buildout -c <buildout_config_file>

8. Update the database using the ``manage_db`` script::

       $ ./buildout/bin/manage_db upgrade


   .. note::

        With c2cgeoportal 0.7 and lower, or if the app section is not ``[app:app]``
        in the production.ini file, you need to specify the app name on the
        ``manage_db`` command line. For example, the above command would be as
        follows::

           $ ./buildout/bin/manage_db -n <package_name> upgrade

   ``<package_name>`` is to be replaced by the name of the application module.
   See above for more information.


Update CGXP
~~~~~~~~~~~

To update CGXP in the application use the following::

    cd <package_name>/static/lib/cgxp
    git fetch
    git checkout <tag>
    git submodule sync
    git submodule update --init

``<package_name>`` is to be replaced by the name of your application package,
``<tag>`` is the name of the version.
If unsure, see the ``name`` argument to the ``setup`` call in the application's
``setup.py`` file.

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
