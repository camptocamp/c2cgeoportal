
.. _internationalization:

====================
Internationalization
====================

In the file ``<package>.mk``, define the supported languages with (default):

.. code:: make

   LANGUAGES ?= en fr de

In the file ``vars.yaml``, define the available and default locales:

.. code:: yaml

   vars:
        ...
        default_locale_name: fr
        available_locale_names: [en, fr, de]

In the file ``language_mapping``, define any desired locale variants, for example:

.. code:: make

   fr=fr-ch

Build your application.

The files to translate are:

* ``geoportal/<package>_geoportal/locale/<lang>/LC_MESSAGES/demo-client.po`` for the ngeo client
* ``geoportal/<package>_geoportal/locale/<lang>/LC_MESSAGES/demo-server.po`` for the server part (should be empty for ngeo interfaces)

.. note::

   All the ``#, fuzzy`` strings should be verified and the line should be removed
   (if the line is not removed, the localisation will not be used).

To update the ``po`` files, you must run this specific targets.

For non Docker project:

.. code:: bash

   ./docker-run make --makefile=<package>.mk update-po

For Docker project:

.. code:: bash

    ./docker-compose-run  make --makefile=<package>.mk update-po

.. note::

   You should run this command when you change something in the following:

     * layer in mapfile (new or modified)
     * layer in administration (new or modified)
     * raster layer in the vars file (new or modified)
     * print template
     * full text search
     * application (JavaScript and HTML files)
     * layer enumeration
     * some metadata as disclaimer
     * editable layer (database structure, data or enumerations)
