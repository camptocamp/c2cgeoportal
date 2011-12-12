.. _integrator_update_application:

Update a c2cgeoportal application
=================================

Update c2cgeoportal::

    svn up

Apply update template ('IOError: No egg-info directory found (...)' should be ignore)::

    ./buildout/bin/paster create --template=c2cgeoportal_update --output-dir=.. \
            ${project} package=${package} srid=${srid}

Read the CONT_CHANGELOG.txt to see if there is comething to change in the project.

Upgrade the database::

    ./buildout/bin/manage_db upgrade

Build it::

    ./buildout/bin/buildout -c buildout_$USER.cfg

