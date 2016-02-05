Use Docker to deploy your application
=====================================

Configure your project
----------------------

Edit the ``<package>.mk`` file and add those lines after the APACHE_VHOST
line:

.. code:: make

    DOCKER = TRUE
    DOCKER_BASE = camptocamp/<project_name>
    JASPERREPORTS_VERSION = 6.1.1

In the private makefiles, don't specify the ``INSTANCE_ID`` (you'll be alone
in your container).

After that, a ``make -f <xxx.mk> build`` will create Docker images named like
that:

* camptocamp/<project_name>_wsgi:latest
* camptocamp/<project_name>_mapserver:latest
* camptocamp/<project_name>_print:latest

The tag is by default ``latest``, but you can change it by setting the
``DOCKER_TAG`` Makefile variable.

Edit ``vars_<package>.yaml`` and add:

.. code:: yaml

    dbhost: db

Database container
------------------

You can add scripts to populate the DB container by adding ``.sql`` or ``.sh``
files in the ``testDB`` directory. They must start with 2 digits, followed by
an underscore. Please start at number 10.

Developer composition
---------------------

A ``docker-compose.yml.mako`` file is created as a starting point.

If you want to host the database on your local machine, you must add a
``dbhost`` entry pointing to ``172.17.0.1`` (your host address for Docker
container) in your ``vars_<package>.yaml`` file. Then you need to make sure
Postgres is configured to listen on that interface and accepts authentication.

If you want to use an external serveur for the database, just put it's address
in the ``dbhost`` entry.

Run the developer composition
-----------------------------

.. prompt:: bash

    make -f <xxx.mk> build && docker-compose up

You can then access your application with http://localhost:8480/


Run with a local c2cgeoportal
-----------------------------

If you need to fix bugs in c2cgeoportal or test new features, you need to hack
the Docker image creation to use your version of c2cgeoportal.

First, you need to move/copy you c2cgeoportal clone into you project root
directory. That is needed to allow Docker to see those files.

Then, add this line to your ``<package>.mk`` file (before the ``include ...``):

.. code:: make

    TEMPLATE_EXCLUDE = c2cgeoportal

Edit your ``.dockerignore`` file and add those lines at the end:

.. code:: docker

    !c2cgeoportal/c2cgeoportal*
    !c2cgeoportal/setup.*
    !c2cgeoportal/requirements.txt

Finally, edit your ``Dockerfile`` and add those lines just before the step #2:

.. code:: docker

    COPY c2cgeoportal /app/c2cgeoportal
    RUN pip install -e c2cgeoportal


Make your Docker images configurable from the composition
---------------------------------------------------------

WSGI
....

To make the DB connection used by your WSGI configurable from the
composition, you can add this in your ``vars_<package>.yaml`` file:

.. code:: yaml

    hooks:
      after_setup: {{package}}.after_setup_hook

Then, in your ``<package>/__init__.py`` file, add this function:

.. code:: python

    def after_settings_hook(settings):
        DB_KEY = "sqlalchemy.url"
        orig = settings[DB_KEY]
        new = os.environ.get("SQLALCHEMY_URL", orig)
        settings[DB_KEY] = new

By setting the ``SQLALCHEMY_URL`` environment variable in your composition
for the wsgi image, you'll be able to change the DB connection used.

Mapserver
.........

The created ``mapserver/Dockerfile`` file installs a hook to make the setup of
the DB possible. Just set the ``DB_CONNECTION`` environment variable to
something like that:

.. code:: docker

    environment:
      DB_CONNECTION: user=www-data password=toto dbname=geoacordaDev host=db
