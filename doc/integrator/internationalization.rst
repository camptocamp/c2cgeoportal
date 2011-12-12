
.. _internationalization:

====================
Internationalization
====================

------
Client
------

For the client parts you have localisation files at 
'${package}/static/js/Proj/Lang/lang.js' where lang is the ISO 639-1 
code, ex: en, de or fr.

------
Server
------

1. Extract all messages from the project::

    ./buildout/bin/python setup.py extract_messages

2. Initialize a catalog for every supported language, for example::

    ./buildout/bin/python setup.py init_catalog -l en
    ./buildout/bin/python setup.py init_catalog -l fr
    ./buildout/bin/python setup.py init_catalog -l de

3. Edit the .po files in ``<package>/locale/*/LC_MESSAGES/<package>.po``

4. Run buildout to compile all the .po files to .mo::

    ./buildout/bin/buildout -c buildout_$$USER.cfg

5. Finally don't forget to restart apache::

    sudo apache2ctl graceful

When you add a new message repeat all steps but replace the step 2. by::

    ./buildout/bin/python setup.py update_catalog


Source: http://wiki.pylonshq.com/display/pylonsdocs/Internationalization+and+Localization



