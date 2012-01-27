.. _developer_server_side:

Server-side development
=======================

Create development environment in a project
-------------------------------------------

* Check out ``c2cgeoportal`` from GitHub::

    $ git clone git@github.com:camptocamp/c2cgeoportal.git
    $ cd c2cgeoportal; git submodule update --init; cd -

* Edit your ``buildout_$USER.cfg`` to have something like::

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

* Build::

    ./buildout/bin/buildout -c c2cgeoportal/buildout_dev.cfg

Tests
-----

Running tests
~~~~~~~~~~~~~

To be able to run c2cgeoportal tests you need to have the c2cgeoportal source
code, and a buildout environment for it. So do that first, as described below.

Install c2cgeportal from source
...............................

Check out c2cgeoportal from GitHub::

    $ git clone git@github.com:camptocamp/c2cgeoportal.git

Bootstrap Buildout::

    $ cd c2cgeoportal
    $ python bootstrap.py --version 1.5.2 --distribute --download-base \
        http://pypi.camptocamp.net/ --setup-source \
        http://pypi.camptocamp.net/distribute_setup.py

Install and build c2cgeoportal::

    $ ./buildout/bin/buildout -c buildout_dev.cfg

c2cgeoportal has two types of tests: unit tests and functional tests. The unit
tests are self-contained, and do not require any specific setup. The functional
tests require a PostGIS database and a MapServer installation that can access
the test mapfile ``c2cgeoportal/tests/functional/c2cgeoportal_test.map``.

Unit tests
..........

To run the unit tests simply do this::

    $ ./buildout/bin/python setup.py nosetests

Functional tests
................

For the functional tests you need to have MapServer and PostgreSQL/PostGIS
installed. Make sure this is the case before proceeding.

You now need to create PostGIS database (named ``c2cgeoportal_test`` for example)
and a schema named ``main`` into it.

To create the database use the following command if you have a PostGIS database
template at your disposal::

    $ sudo -u postgres createdb -T template_postgis c2cgeoportal_test

Else use this::

    $ sudo -u postgres createlang plpgsql c2cgeoportal_test
    $ sudo -u postgres psql -d c2cgeoportal_test \
           -f /usr/share/postgresql/8.4/contrib/postgis-1.5/postgis.sql
    $ sudo -u postgres psql -d c2cgeoportal_test \
           -f /usr/share/postgresql/8.4/contrib/postgis-1.5/spatial_ref_sys.sql

If you don't have a ``www-data`` user you need to create one::

    $ sudo -u postgres createuser -P www-data

To create the ``main`` schema::

    $ sudo -u postgres psql -d c2cgeoportal_test \
           -c 'CREATE SCHEMA main;'
    $ sudo -u postgres psql -d c2cgeoportal_test \
           -c 'GRANT ALL ON SCHEMA main TO "www-data";'

Now edit ``buildout_dev.cfg`` (or create your own buildout config file
extending ``buildout_dev.cfg``) and set the ``dbuser``, ``dbpassword``,
``dbhost``, ``dbport``, ``db``, and ``mapserv_url`` as appropriate.  Once done,
run the ``template`` part to generate
``c2cgeoportal/tests/functional/test.ini`` and
``c2cgeoportal/tests/functional/c2cgeoportal_test.map.ini``::

    $ ./buildout/bin/buildout -c buildout_dev.cfg install template

You can now run both the unit and functional tests with this::

    $ ./buildout/bin/python setup.py nosetests -a functional

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

