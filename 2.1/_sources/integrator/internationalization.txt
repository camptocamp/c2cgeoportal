
.. _internationalization:

====================
Internationalization
====================

---------------
ngeo and server
---------------

In the ``<package>.mk`` file define the supported language with (default):

.. code: make

   LANGUAGES ?= en fr de

In the ``vars_<package>.yaml`` file define the available and default language:

.. code: yaml

   vars:
        ...
        default_locale_name: fr
        available_locale_names: [en, fr, de]

Build your application

The file to translate are:

* ``demo/locale/<lang>/LC_MESSAGES/demo-client.po`` for ngeo client
* ``demo/locale/<lang>/LC_MESSAGES/demo-server.po`` for the server part (Should be empty for ngeo interfaces)

.. note::

   All the ``#, fuzzy`` strings should be verified ans the line should be removed.
   (if the line isn't removed the localisation will not be used.)

----
CGXP
----

Translations of the browser interfaces (main viewer, edit interfaces and APIs)
are included in two kinds of Javascript files stored in
``<package>/static/js/Proj/Lang/``:

* ``<lang>.js`` is used to translate data-related strings such as layernames or
  attributenames (in interrogation results). It is based upon the OpenLayers
  translation syntax. For instance::

      OpenLayers.Util.extend(OpenLayers.Lang.<lang>, {
          "layertree": "Themes"
      });

* ``GeoExt-<lang>.js`` is used to adapt the translations of existing plugins/widgets
  or to add translations of project-specific plugins. It is based upon the GeoExt
  translation syntax. Key-value translation pairs are encapsulated by class.
  For instance::

      GeoExt.Lang.add("<lang>", {
          "cgxp.tree.LayerTree.prototype": {
              moveupText: "Move up"
          }
      });

.. note::

    <lang> is the `ISO 639-1 code <http://en.wikipedia.org/wiki/List_of_ISO_639-1_codes>`_.
    For example: en, de or fr.

.. note::

    Standard translations for CGXP plugins/widgets strings are available on
    `Github <https://github.com/camptocamp/cgxp/tree/master/core/src/script/CGXP/locale>`_.

.. note::

    Translations from both OpenLayers- and GeoExt-based systems are stored in
    separated files because of API constraints. Read more at :ref:`integrator_api_i18n`.
