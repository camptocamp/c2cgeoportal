.. _developer_server_side:

Server-side development
=======================

Running tests
~~~~~~~~~~~~~

Run the tests: 

* Have the c2cgeoportal as a dev egg in c2cgeoportal directory

* run buildout::

    ./buildout/bin/buildout -c buildout_$USER.cfg

* run the tests::

   . buildout/bin/activate
   cd c2cgeoportal/
   nosetests
   cd -
   deactivate

Adding tests
~~~~~~~~~~~~

**To Be Done**

Coding style
~~~~~~~~~~~~

Please read http://www.python.org/dev/peps/pep-0008/.

