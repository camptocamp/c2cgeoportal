.. _developer_server_side:

Server-side development
=======================

Create development environment
-------------------------------

* Check out ``c2cgeoportal`` from GitHub::

    $ git clone git@github.com:camptocamp/c2cgeoportal.git

* Edit your ``buildout_$USER.cfg`` to have somthing like::

    [buildout]
    extends = buildout.cfg
    parts -= libs-update
    develop += c2cgeoportal
    extensions -= buildout.dumppickedversions

    [vars]
    instanceid = <instanceid>

    [jsbuild]
    compress = False

    [cssbuild]
    compress = false

    [template]
    exclude-directories += c2cgeoportal/paste_templates

Tests
-----

Running tests
~~~~~~~~~~~~~

* Check out ``c2cgeoportal`` from GitHub::

        $ git clone git@github.com:camptocamp/c2cgeoportal.git

* Bootstrap Buildout::

        $ python bootstrap.py --version 1.5.2 --distribute --download-base \
            http://pypi.camptocamp.net/ --setup-source \
            http://pypi.camptocamp.net/distribute_setup.py

* Install and build c2cgeoportal::

        $ ./buildout/bin/buildout -c buildout_dev.cfg

* Run the tests::

        $ ./buildout/bin/python setup.py nosetests

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

