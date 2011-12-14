.. _developer_server_side:

Server-side development
=======================

Tests
-----

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

Database
--------

Object model
~~~~~~~~~~~~

.. image:: database.png
.. source file is database.dia
   export to database.eps
   than run « convert -density 150 database.eps database.png » to have a good quality png file

``TreeItem`` and ``TreeGroup`` are abstract (can't be create) class used to create the tree.

``FullTextSearch`` references a first level ``LayerGroup`` but without any constrains.

It's not visible on this schema, but the ``User`` of a child schema has a link (``parent_role``) 
to the ``Role`` of the parent schema.

Code
----

Coding style
~~~~~~~~~~~~

Please read http://www.python.org/dev/peps/pep-0008/.

