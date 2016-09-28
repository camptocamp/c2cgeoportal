
.. _internationalization:

====================
Internationalization
====================

------
Client
------

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

------
Server
------

#. Extract all messages from the project::

    .build/venv/bin/python setup.py extract_messages

#. Initialize a catalog for every supported language, for example::

    .build/venv/bin/python setup.py init_catalog -l en
    .build/venv/bin/python setup.py init_catalog -l fr
    .build/venv/bin/python setup.py init_catalog -l de

#. Edit the .po files in ``<package>/locale/<lang>/LC_MESSAGES/<package>.po``

#. Run make to compile all the .po files to .mo::

    make -f <user>.mk build

When you add a new message repeat all steps but replace the step 2. by::

    .build/venv/bin/python setup.py update_catalog


`Source from pylondhq <http://wiki.pylonshq.com/display/pylonsdocs/Internationalization+and+Localization>`_


Mobile application
------------------

It's also possible to translate the mobile application title, for that you should
add the following line at the top of ``message_extractor`` array:

.. code:: python

   ('static/mobile/index.html', 'mako', {'input_encoding': 'utf-8'}),

Than mark your title as translated:

.. code:: html

   <title>${_('GeoMapFish Mobile Application')}</title>

And don't forget (for the upgrades) to do the same in the ``project.yaml.mako`` file,
in section ``template_vars``:

.. code:: yaml

   mobile_application_title: "{_('GeoMapFish Mobile Application')}"
