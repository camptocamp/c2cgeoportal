
.. _internationalization:

====================
Internationalization
====================

------
Client
------

For the client parts you have localisation files at 
``<package>/static/js/Proj/Lang/<lang>.js`` where <lang> is the 
`ISO 639-1 code <http://en.wikipedia.org/wiki/List_of_ISO_639-1_codes>`_,
ex: en, de or fr.

------
Server
------

#. Extract all messages from the project::

    ./buildout/bin/python setup.py extract_messages

#. Initialize a catalog for every supported language, for example::

    ./buildout/bin/python setup.py init_catalog -l en
    ./buildout/bin/python setup.py init_catalog -l fr
    ./buildout/bin/python setup.py init_catalog -l de

#. Edit the .po files in ``<package>/locale/<lang>/LC_MESSAGES/<package>.po``

#. Run buildout to compile all the .po files to .mo::

    ./buildout/bin/buildout -c buildout_$USER.cfg

#. Finally don't forget to restart apache::

    sudo apache2ctl graceful

When you add a new message repeat all steps but replace the step 2. by::

    ./buildout/bin/python setup.py update_catalog


Source: http://wiki.pylonshq.com/display/pylonsdocs/Internationalization+and+Localization



