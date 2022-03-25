
.. _internationalization:

====================
Internationalization
====================

In the file ``<package>.mk``, define the supported languages with (default),
in the simple application mode, the list of languages is constant: en fr de it.

.. code:: make

   LANGUAGES ?= en fr de

In the file ``vars.yaml``, define the default locale:

.. code:: yaml

   vars:
        ...
        default_locale_name: fr

In the file ``language_mapping``, define any desired locale variants, for example:

.. code:: make

   fr=fr-ch

Build your application.

The files to translate are:

* ``geoportal/<package>_geoportal/locale/<lang>/LC_MESSAGES/<package>-client.po`` for the ngeo client

.. note::

   All the ``#, fuzzy`` strings should be verified and the line should be removed
   (if the line is not removed, the localization will not be used).

To update your ``po`` files, you should proceed as follows.

.. code:: bash

    make update-po

.. note::

   You should run this command when you change something in the following:

     * layer in Mapfile (new or modified)
     * layer in administration (new or modified)
     * raster layer in the vars file (new or modified)
     * print template
     * full-text search
     * application (JavaScript and HTML files)
     * layer enumeration
     * some metadata as disclaimer
     * editable layer (database structure, data or enumerations)

.. note::

   In Mapfiles, attributes added by MapServer substitution will not be collected
   for translation.

~~~~~~~~~~~~~~~~~~~~~~
Collect custom strings
~~~~~~~~~~~~~~~~~~~~~~

.. note::

    This is not possible in the simple application mode

If the standard system can not collect some strings, you can add them manually in
one of your JavaScript application controllers:

.. code:: javascript

    /** @type {angular.gettext.gettextCatalog} */
    const gettextCatalog = $injector.get('gettextCatalog');
    gettextCatalog.getString('My previously not collected string');

~~~~~~~~~~~~~~~~~~~~~
I18next configuration
~~~~~~~~~~~~~~~~~~~~~

In the ``vars`` in ``i18next`` you can override the default ``i18next`` configuration.
If not provided the ``backend/loadPath`` is automatically generated.

Seel also `i18next Configuration Options <https://www.i18next.com/overview/configuration-options>`_.

~~~~~~~~~~~~~~~~~~~~~~~~~~~
Different localization sets
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you use the application with different databases that contains two different layer trees you should
have a suffix on your po files.

Before calling the `update-po` command you should rename the po files you want to update without the suffix,
and after you should rename them with the right name.

In the config `Dockerfile` you should replace:

.. code:: Dockerfile

   RUN build-l10n "<package>"

by:

.. code:: Dockerfile

   RUN build-l10n --suffix=suffix_1 --suffix=suffix_2 "<package>"

in the `geoportal/<package>_geoportal/__init__.py` file you should add:

.. code:: python

    for lang in (<languages>):
        shutil.move(
            f'/app/<package>_geoportal/locale/{lang}/LC_MESSAGES/<package>_geoportal-client{<suffix>}.mo',
            f'/app/<package>_geoportal/locale/{lang}/LC_MESSAGES/<package>_geoportal-client.mo',
        )
