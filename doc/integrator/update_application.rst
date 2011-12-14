.. _integrator_update_application:

Update a c2cgeoportal application
=================================

Update your working copy from the repository::

    $ svn update

Apply update template ('IOError: No egg-info directory found (...)' should be
ignore)::

    $ ./buildout/bin/paster create --template=c2cgeoportal_update --output-dir=.. \
            <project_name> package=<package_name>

Read the CONST_CHANGELOG.txt to see if there is something to change in the
project.

Upgrade the database to the latest repository version::

    $ ./buildout/bin/manage_db -c CONST_production.ini -n <package_name> upgrade

Rebuild and install the application::

    $ ./buildout/bin/buildout -c buildout_$USER.cfg

