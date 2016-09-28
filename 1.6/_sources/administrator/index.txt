.. _administrator_guide:

===================
Administrator Guide
===================

This chapter describes how to install, deploy, and administrate a c2cgeoportal
application.

The application administrator configures and administrates the application
through the database. The administrator does not deal with the files of the
application (the integrator is the one responsible for these files). Except for
one file (or set of files) actually: the MapServer mapfile. Adding layers to
the application indeed requires inserting information in the database, as well
as adding ``LAYER`` sections to the application's MapServer mapfile. So the
mapfile is a place where the administrator and the integrator collaborate.

Content:

.. toctree::
   :maxdepth: 1

   mapfile
   administrate
   editing
   tinyows
