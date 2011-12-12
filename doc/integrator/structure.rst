
.. _structure:

File and Folder structure
=========================

| ``setup.*`` - the egg configuration
| ``tilecache/`` - tilecache configuration (parent only)
| ``buildout*.cfg`` - buildout scripts that contain the configuration variables
| ``deploy/`` - deployment configuration
| ``print/`` - print configuration and his images and other needed files
| ``mapserver/`` - the mapfile and his depandancies
| ``<package>/models.py`` - database extension
| ``<package>/forms.py`` - the admin interface configuration for the database extension
| ``<package>/locale`` - the server side localysation for the database extension
| ``<package>/scripts`` - the custom scripts
| ``<package>/views`` - the custom web servicies
| ``<package>/templates/index.html`` - the main page
| ``<package>/templates/viewer.js`` - the viewer configuration of the main page
| ``<package>/templates/apiviewer.js`` - the viewer configuration for the API
| ``<package>/static/images`` - the custom and theme images
| ``<package>/static/css`` - the custom css
| ``<package>/static/js`` - the custom javascript component
| ``<package>/static/js/Proj/Lang/*.js`` - the custom client side localisation

