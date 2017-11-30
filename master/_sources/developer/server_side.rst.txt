.. _developer_server_side:

Server-side development
=======================

Create development environment in a project
-------------------------------------------

c2cgeoportal developers often need to test c2cgeoportal changes in the context
of an existing c2cgeoportal application. Here is how:

* Change current directory to your sources root directory and clone ``c2cgeoportal`` there (in the
  following line the sources directory is the user home directory). Then build c2cgeoportal,
  and go back to your project directory:

  .. prompt:: bash

    cd ~
    git clone git@github.com:camptocamp/c2cgeoportal.git
    cd c2cgeoportal
    ./docker-run make build
    cd  ~/<project>

.. note:: Old build directory

   If you still have old build directory remove it before running the build

   .. prompt:: bash

      rm -rf .build

  You can now check out your development branch if necessary.

* Edit your ``<user>.mk`` to have something like this:

  .. code:: make

    DEVELOPMENT = TRUE
    REQUIREMENTS = -e ../c2cgeoportal

    include <package>.mk

* Uninstall the regular c2cgeoportal egg from the virtual environment:

  .. prompt:: bash

    ./docker-run pip uninstall c2cgeoportal

* Remove/comment the following line in the CONST_requirements.txt file:

  .. code:: make

    c2cgeoportal==1.6.0

* Build your application application:

  .. prompt:: bash

    ./docker-run rm /build/requirements.timestamp && ./docker-run make build

.. note:: Print performance issue

   When restarting the print server frequently, performance issues may randomly be observed.
   This is done in random number generation.

   To improve the performances you should add in the ``/srv/tomcat/tomcat1/bin/setenv-local.sh`` file:

   .. code:: bash

      export ADD_JAVA_OPTS="-Djava.security.egd=file:/dev/./urandom"


Tests
-----

Running tests
~~~~~~~~~~~~~

To be able to run c2cgeoportal tests you need to have the c2cgeoportal source
code, and a make environment for it. So do that first, as described below.

Install c2cgeportal from source
...............................

Check out c2cgeoportal from GitHub:

.. prompt:: bash

    git clone git@github.com:camptocamp/c2cgeoportal.git
    cd c2cgeoportal

c2cgeoportal has two types of tests: unit tests and functional tests. The unit
tests are self-contained, and do not require any specific setup. The functional
tests require to run with `docker-compose-run`.

Unit tests
..........

To run the unit tests do this:

.. prompt:: bash

    ./docker-run make build
    docker build --tag=geomapfish-db docker/test-db
    ./docker-compose-run alembic --config c2cgeoportal/tests/functional/alembic.ini upgrade head
    ./docker-compose-run alembic --config c2cgeoportal/tests/functional/alembic_static.ini upgrade head
    ./docker-compose-run make tests

To run a specific test use the ``--where`` switch. For example:

.. prompt:: bash

    ./docker-compose-run nosetests --where \
        /src/geoportal/tests/functional/test_themes.py:TestThemesView.test_catalogue

Adding tests
~~~~~~~~~~~~

**To Be Done**

Upgrade dependencies
--------------------

When we start a new version of c2cgeoportal or just before a new development
phase it is a good idea to update the dependencies.

Eggs
~~~~

All the ``c2cgeoportal`` (and ``tilecloud-chain``) dependencies are present in
the ``c2cgeoportal/scaffolds/update/CONST_versions.mako`` file.

To update them you can simply get them from a travis build in the
``./docker-run pip freeze`` task.

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
.. source file is database.dia.
   export from DIA using the type "PNG (anti-crénelé) (*.png)", set the width to 1000px.

``TreeItem`` and ``TreeGroup`` are abstract (cannot be create) class used to create the tree.

``FullTextSearch`` references a first level ``LayerGroup`` but without any constrains.

it is not visible on this schema, but the ``User`` of a child schema has a link (``parent_role``)
to the ``Role`` of the parent schema.

``metadata`` vs ``functionality``
....................................

Technically the same ``functionality`` can be reused by more than one element.

``functionalities`` are designed to configure and customize various parts of
the application. For instance to change the default basemap when a new theme
is loaded.

To do that in the CGXP application we trigger an event when we load a theme the
new ``functionnalities``.

The ``metadata`` contains attributes that are directly related to the element.
For example the layer disclaimer, ...


Migration
~~~~~~~~~

We use the ``alembic`` module for database migration. ``alembic`` works with a
so-called *migration repository*, which is a simple directory ``/opt/alembic`` in the
docker image. So developers who modify the ``c2cgeoportal`` database schema should add migration scripts.

Add a new script call from the application's root directory:

.. prompt:: bash

    ./docker-compose-run alembic --name=[main|static] revision --message "<Explicit name>"

Or in c2cgeoportal root directory:

.. prompt:: bash

    ./docker-compose-run alembic \
        --config geoportal/tests/functional/alembic.ini --name=[main|static] \
        revision --message "<Explicit name>"

This will generate the migration script in
``commons/c2cgeoportal/commons/alembic/[main|static]/xxx_<Explicite_name>.py``.

To get the project schema use:
``schema = context.get_context().config.get_main_option('schema')``

The scripts should not fail if it is run again. See:
http://alembic.readthedocs.org/en/latest/cookbook.html#conditional-migration-elements

Then customize the migration to suit your needs, test it:

.. prompt:: bash

    ./docker-compose-run alembic upgrade head

More information at:
 * http://alembic.readthedocs.org/en/latest/index.html
 * http://alembic.readthedocs.org/en/latest/tutorial.html#create-a-migration-script
 * http://alembic.readthedocs.org/en/latest/ops.html

Sub domain
----------

All the static resources used sub domains by using the configurations variables:
``subdomain_url_template`` and ``subdomains``.

To be able to use sub domain in a view we should configure the route as this::

    from c2cgeoportal_geoportal.lib import MultiDomainPregenerator
    config.add_route(
        '<name>', '<path>',
        pregenerator=MultiDomainPregenerator())

And use the ``route_url`` with an additional argument ``subdomain``::

    request.route_url('<name>', subdomain='<subdomain>')}",

Code
----

Coding style
~~~~~~~~~~~~

Please read http://www.python.org/dev/peps/pep-0008/.

And run validation:

.. prompt:: bash

    make checks

Dependencies
------------

Major dependencies docs:

* `SQLAlchemy <http://docs.sqlalchemy.org/>`_
* `GeoAlchemy2 <http://geoalchemy-2.readthedocs.org/>`_
* `alembic <http://alembic.readthedocs.org/>`_
* `Pyramid <http://docs.pylonsproject.org/en/latest/docs/pyramid.html>`_
* `Papyrus <http://pypi.python.org/pypi/papyrus>`_
* `MapFish Print <http://mapfish.github.io/mapfish-print-doc/>`_
* `reStructuredText <http://docutils.sourceforge.net/docs/ref/rst/introduction.html>`_
* `Sphinx <http://sphinx.pocoo.org/>`_
