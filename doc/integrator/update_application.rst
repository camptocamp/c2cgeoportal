.. _integrator_update_application:

Update a c2cgeoportal application
=================================

Update your working copy from the repository::

    svn update

Apply update template ('IOError: No egg-info directory found (...)' should be ignore)::

    ./buildout/bin/paster create --template=c2cgeoportal_update --output-dir=.. \
            ${project} package=${package} srid=${srid}

Read the CONST_CHANGELOG.txt to see if there is something to change in the project.

Upgrade the database::

    ./buildout/bin/manage_db upgrade

Build it::

    ./buildout/bin/buildout -c buildout_$USER.cfg

