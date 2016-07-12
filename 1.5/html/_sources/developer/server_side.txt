.. _developer_server_side:

Server-side development
=======================

Create development environment in a project
-------------------------------------------

c2cgeoportal developers often need to test c2cgeoportal changes in the context
of an existing c2cgeoportal application. Here's how:

* Change dir to your application's root dir and clone ``c2cgeoportal`` there:

  .. prompt:: bash

    git clone git@github.com:camptocamp/c2cgeoportal.git
    cd c2cgeoportal; git submodule update --init; cd -

  You can now check out your development branch if necessary.

* Edit your ``buildout_$USER.cfg`` to have something like this::

    [buildout]
    extends = buildout.cfg
    develop += c2cgeoportal
    parts -= fix-perm

    [vars]
    instanceid = <instanceid>

    [jsbuild]
    compress = False

    [jsbuild-mobile]
    compress = False

    [cssbuild]
    compress = false

    [template]
    exclude-directories += c2cgeoportal

    [versions]
    c2cgeoportal =

  .. note::

    ``develop += c2cgeoportal`` and ``c2cgeoportal =`` lines refer to the
    installation of c2cgeoportal as a develop egg.

    ``parts -= fix-perm`` disables the ``fix-perm`` task that may take some
    time whereas it is not needed in a personal environment.

* Remove the regular c2cgeoportal egg from the Buildout environment:

  .. prompt:: bash

    rm -rf ./buildout/eggs/c2cgeoportal-*

* Build c2cgeoportal and rebuild the c2cgeoportal application:

  .. prompt:: bash

    ./buildout/bin/buildout -c c2cgeoportal/buildout_dev.cfg
    ./buildout/bin/buildout -c buildout_$USER.cfg


Tests
-----

Running tests
~~~~~~~~~~~~~

To be able to run c2cgeoportal tests you need to have the c2cgeoportal source
code, and a buildout environment for it. So do that first, as described below.

Install c2cgeportal from source
...............................

Check out c2cgeoportal from GitHub:

.. prompt:: bash

    git clone git@github.com:camptocamp/c2cgeoportal.git

Change into the ``c2cgeoportal`` directory and initialize the submodules:

.. prompt:: bash

    cd c2cgeoportal
    git submodule update --init

Bootstrap Buildout:

.. prompt:: bash

    python bootstrap.py --version 1.5.2 --distribute --download-base \
        http://pypi.camptocamp.net/distribute-0.6.22_fix-issue-227/ --setup-source \
        http://pypi.camptocamp.net/distribute-0.6.22_fix-issue-227/distribute_setup.py

Install and build c2cgeoportal:

.. prompt:: bash

    ./buildout/bin/buildout -c buildout_dev.cfg

c2cgeoportal has two types of tests: unit tests and functional tests. The unit
tests are self-contained, and do not require any specific setup. The functional
tests require a PostGIS database and a MapServer installation that can access
the test mapfile ``c2cgeoportal/tests/functional/c2cgeoportal_test.map``.

Unit tests
..........

To run the unit tests do this:

.. prompt:: bash

    ./buildout/bin/python setup.py nosetests -a '!functional'

Functional tests
................

For the functional tests you need to have MapServer and PostgreSQL/PostGIS
installed. Make sure this is the case before proceeding.

You now need to create PostGIS database (named ``c2cgeoportal_test`` for example)
and a schema named ``main`` into it.

To create the database use the following command if you have a PostGIS database
template at your disposal:

.. prompt:: bash

    sudo -u postgres createdb -T template_postgis c2cgeoportal_test

.. note::

    If you don't have a template named ``template_postgis`` use this:

    .. prompt:: bash

        sudo -u postgres createdb -E UTF8 -T template0 c2cgeoportal_test
        sudo -u postgres createlang plpgsql c2cgeoportal_test
        sudo -u postgres psql -d c2cgeoportal_test \
               -f /usr/share/postgresql/9.1/contrib/postgis-1.5/postgis.sql
        sudo -u postgres psql -d c2cgeoportal_test \
               -f /usr/share/postgresql/9.1/contrib/postgis-1.5/spatial_ref_sys.sql
        sudo -u postgres psql -d c2cgeoportal_test \
               -c 'GRANT ALL ON geometry_columns TO "www-data";'
        sudo -u postgres psql -d c2cgeoportal_test \
               -c 'GRANT SELECT ON spatial_ref_sys TO "www-data";'

    The ``template0`` is needed on Debian and Ubuntu to create a utf-8
    database.

If you don't have a ``www-data`` user you need to create one:

.. prompt:: bash

    sudo -u postgres createuser -P www-data

To create the ``main`` and ``main_static`` schema:

.. prompt:: bash

    sudo -u postgres psql -d c2cgeoportal_test -c 'CREATE SCHEMA main;'
    sudo -u postgres psql -d c2cgeoportal_test -c 'GRANT ALL ON SCHEMA main TO "www-data";'
    sudo -u postgres psql -d c2cgeoportal_test -c 'CREATE SCHEMA main_static;'
    sudo -u postgres psql -d c2cgeoportal_test -c 'GRANT ALL ON SCHEMA main_static TO "www-data";'

Now edit ``buildout_dev.cfg`` (or create your own buildout config file
extending ``buildout_dev.cfg``) and set the ``dbuser``, ``dbpassword``,
``dbhost``, ``dbport``, ``db``, and ``mapserv_url`` as appropriate.

``mapserv_url`` needs to refer a valid ``mapserv`` instance running locally,
i.e. on the machine you run the tests on. For example, if you use your desktop
machine it may be ``http://locahost/cgi-bin/mapserv``.

.. note::

    On Camptocamp servers ``mapserv`` is usually not available on the
    ``localhost`` virtual host. One option involves creating a specific script
    alias for ``mapserv``, for example by adding something like the following
    to your ``/var/www/<virtual_host_name>/conf/<your_login>.conf`` file::

        ScriptAlias /elemoine-mapserv /usr/lib/cgi-bin/mapserv
        <Location /elemoine-mapserv>
            SetHandler fcgid-script
        </Location>

    To know what domain name to use look at the ``ServerAlias``'es
    configured for the virtual host in
    ``/etc/apache2/sites-enabled/<virtual_host_name>``.

    Here's an example of a possible ``mapserv_url``:
    ``http://mapfish-geoportal-demo/elemoine-mapserv``.


Once done with the editing of ``buildout_dev.cfg``, run the ``template`` part
to generate ``c2cgeoportal/tests/functional/test.ini`` and
``c2cgeoportal/tests/functional/c2cgeoportal_test.map``:

.. prompt:: bash

    ./buildout/bin/buildout -c buildout_dev.cfg install template

.. warning::

    If you change the configuration in ``buildout_dev.cfg`` you may need to
    manually remove ``c2cgeoportal/tests/functional/test.ini`` and
    ``c2cgeoportal/tests/functional/c2cgeoportal_test.map`` before running the
    ``template`` part again. This is due to an unknown issue with the
    ``z3c.recipe.filetemplate`` recipe. See
    https://github.com/camptocamp/c2cgeoportal/issues/145.

You can now run the functional tests with this:

.. prompt:: bash

    ./buildout/bin/python setup.py nosetests -a functional

All tests
.........

To run all the tests do this:

.. prompt:: bash

    ./buildout/bin/python setup.py nosetests

To run a specific test use the ``--tests`` switch. For example:

.. prompt:: bash

    ./buildout/bin/python setup.py nosetests --tests \
            c2cgeoportal/tests/test_echoview.py:test_json_base64_encode

Adding tests
~~~~~~~~~~~~

**To Be Done**

Upgrade dependencies
--------------------

When we start a new version of c2cgeoportal or just before a new development
phase it's a good idea to update the dependencies.

Eggs
~~~~

All the ``c2cgeoportal`` (and ``tilecloud-chain``) dependencies are present in
the ``c2cgeoportal/scaffolds/create/versions.cfg`` file.

To update them you should remove all the version listed after the
line ``# Package version that can be easily update``.

Then run:

.. prompt:: bash

    rm -rf *.egg
    ./buildout/bin/buildout -n

Copy the dependency version lines (of the form ``Mako = 0.7.2``)
from the ``buildout`` command output and paste them where you have previously
removed the versions.

And apply the following corrections (to work around bugs in
``buildout.dumppickedversions``)::

     Jinja2 = x.y.z
    +jinja2 = x.y.z
     Mako = x.y.z
    +mako = x.y.z
     Markdown = x.y.z
    +markdown = x.y.z
     MarkupSafe = x.y.z
    +markupsafe = x.y.z
     Pillow = x.y.z
    +pillow = x.y.z
     Tempita = x.y.z
    +tempita = x.y.z

Development eggs
~~~~~~~~~~~~~~~~

Empty the ``[versions]`` section of the ``buildout_dev.cfg`` file.

Then run:

.. prompt:: bash

    ./buildout/bin/buildout -n -c buildout_dev.cfg

Copy the dependency version lines from the ``buildout`` command output and
paste them where you have previously removed the versions.

Submodules
~~~~~~~~~~

Go to the OpenLayers folder:

.. prompt:: bash

    cd c2cgeoportal/static/lib/openlayers/

Get the new revision of OpenLayers:

.. prompt:: bash

    git fetch
    git checkout release-<version>

Then you can commit it:

.. prompt:: bash

    cd -
    git add c2cgeoportal/static/lib/openlayers/
    git commit -m "update OpenLayers to <version>"


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

Migration
~~~~~~~~~

We use the sqlalchemy-migrate module for database migration.
sqlalchemy-migrate works with a so-called *migration
repository*, which is a simple directory in the application
source tree:``<package>/CONST_migration``. As the
``CONST_`` prefix suggests this repository is part of
the ``c2cgeoportal_update`` scaffold, it is created or
updated when this scaffold is applied. So developers
who modify the c2cgeoportal database schema should add
migration scripts to the ``c2cgeoportal_update``
scaffold, as opposed to the application.

Add a new script call from the application's root directory:

.. prompt:: bash

    ./buildout/bin/manage_db script "<Explicite name>"

.. note::

    With c2cgeoportal 0.7 and lower, or if the app section is not ``[app:app]``
    in the production.ini file, you need to specify the app name on the
    ``manage_db`` command line. For example, the above command would be as
    follows:

    .. prompt:: bash

       ./buildout/bin/manage_db -n <package_name> script "<Explicite name>"

This will generate the migration script in
``<package>/CONST_migration/versions/xxx_<Explicite_name>.py``
You should *NOT* commit the script in this directory because this migration
script should be shared with all c2cgeoportal projects.
It is the c2cgeoportal ``update`` template which is responsible for updating
this directory.

Then customize the migration to suit your needs, test it:

.. prompt:: bash

    ./buildout/bin/manage_db test

If your script fails during upgrade, it is possible the version number has been
incremented anyway, so you need to explicitly reset the version to its
correct value using:

.. prompt:: bash

    ./buildout/bin/manage_db drop_version_control
    ./buildout/bin/manage_db version_control <the_correct_version_number>

Once you have tested it, move it to the c2cgeoportal ``update`` template, in
``c2cgeoportal/scaffolds/update/+package+/CONST_migration/versions/``.


More information at:
 * http://code.google.com/p/sqlalchemy-migrate/
 * http://www.karoltomala.com/blog/?p=633

Sub domain
----------

All the static resources used sub domains by using the configurations variables:
``subdomain_url_template`` and ``subdomains``.

To be able to use sub domain in a view we should configure the route as this::

    from c2cgeoportal.lib import MultiDomainPregenerator
    config.add_route(
        '<name>', '<path>',
        pregenerator=MultiDomainPregenerator())

And use the ``route_url`` with an additional argument ``subdomain``::

    request.route_url('<name>', path='', subdomain='<subdomain>')}",

Code
----

Coding style
~~~~~~~~~~~~

Please read http://www.python.org/dev/peps/pep-0008/.

And run validation:

.. prompt:: bash

    ./buildout/bin/buildout -c buildout_dev.cfg install validate-py

Dependencies
------------

Major dependencies docs:

* `SQLAlchemy <http://docs.sqlalchemy.org/en/latest/>`_
* `GeoAlchemy <http://www.geoalchemy.org/>`_
* `Formalchemy <http://docs.formalchemy.org/>`_
* `GeoFormAlchemy <https://github.com/camptocamp/GeoFormAlchemy/blob/master/GeoFormAlchemy/README.rst>`_
* `sqlalchemy-migrate <http://readthedocs.org/docs/sqlalchemy-migrate/en/v0.7.2/>`_
* `Pyramid <http://docs.pylonsproject.org/en/latest/docs/pyramid.html>`_
* `Papyrus <http://pypi.python.org/pypi/papyrus>`_
* `MapFish Print <http://www.mapfish.org/doc/print/index.html>`_
* `reStructuredText <http://docutils.sourceforge.net/docs/ref/rst/introduction.html>`_
* `Sphinx <http://sphinx.pocoo.org/>`_
