.. _custom_alembic:

Alembic on custom tables
========================

If you want to manage custom tables (GMF tables; not in the ``main`` nor the ``static`` schema)
with alembic you must setup a custom alembic process. Here's an example. Others solutions
are possible, but do not try to reuse the existing ``alembic.ini`` (because you will not be able to specify a
schema through the configuration levels).

The following example uses ``docker cp``. You can achieve the same with a volume, but you will
have to set the owner (root) of copied files.

Init alembic
------------

In your project, add a ``geoportal/alembic_<project_name>`` folder.

Build and run your project.

In the running container initialize alembic in a folder that have **not** already
an ``alembic.ini`` file, like the /tmp folder. Create also directly the first revision file:

.. prompt:: bash

  docker-compose exec geoportal mkdir /tmp/new_alembic
  docker-compose exec geoportal bash -c "cd /tmp/new_alembic; alembic init alembic"
  # Ignore the warning message about setting the alembic.ini file for now.
  docker-compose exec geoportal bash -c "cd /tmp/new_alembic; alembic revision -m 'Inital revision'"

Run ``docker-compose ps geoportal`` to know the name of the running geoportal container.

Then copy the generated alembic folder in the ``geoportal`` folder of your project:

.. prompt:: bash

  PROJECT=<your_project>
  docker cp <geoportal_container_name>:/tmp/new_alembic geoportal/alembic_${PROJECT}

You can now customize the ``alembic.ini`` and the ``env.py``.

Configure ``alembic.ini``
-------------------------

The main change to apply is to use environment variables to run alembic on the right database.
To do so, use a ``tmpl`` file:

.. prompt:: bash

  mv geoportal/alembic_${PROJECT}/alembic.ini{,.tmpl}
  rm geoportal/alembic_${PROJECT}/alembic.ini
  echo "/geoportal/alembic_${PROJECT}/alembic.ini" >> .gitignore

And inside the ``alembic.ini.tmpl`` set the ``sqlalchemy.url`` to
``postgresql://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/${PGDATABASE}``.

In this file, you may also directly set a new variable ``version_table_schema`` to set the
name of the schema inside which alembic must create its revision table. See:
`The Environment Context <https://alembic.sqlalchemy.org/en/latest/api/runtime.html#the-environment-context>`_.

You must now set permissions on this tmpl file to authorize evaluation of this ``tmpl`` file.
Add the following lines in the ``geoportal/Dockerfile`` just before the command
``ENTRYPOINT [ "/usr/bin/eval-templates" ]``, in the ``FROM camptocamp/geomapfish`` section.

.. code::

  # Custom - To be able to run tmpl on alembic.ini.tmpl file
  RUN rm -f /app/alembic_<project>/alembic.ini && \
      chmod g+w /app/alembic_<project> && \
      chown www-data /app/alembic_<project>/alembic.ini.tmpl

Configure ``env.py``
--------------------

Edit the file ``geoportal/alembic_${PROJECT}/alembic/env.py``.

In there, update the ``run_migrations_offline`` function by adding
``version_table_schema = config.get_main_option("version_table_schema")`` to get the schema
name from the ``alembic.ini`` file. Add this value as parameter of the ``context.configure()``
function.

Do the same in the ``run_migrations_online`` function.

At this point, you should be able to run your (currently empty) first revision file.

Run an alembic upgrade
----------------------

Once your revision file completed, build and run docker-compose up on your project.
Your alembic files should be in the running container. You can now run manually an upgrade with:

.. prompt:: bash

  docker-compose exec geoportal bash -c "cd /app/alembic_${PROJECT}; alembic upgrade head"

Create a new revision file
--------------------------

With a running instance, execute:

.. prompt:: bash

  docker-compose exec geoportal bash -c "cd /app/alembic_${PROJECT}; alembic revision -m '<msg>'"
  docker cp <geoportal_container_name>:/app/alembic_${PROJECT}/alembic/versions/<the_new_file> geoportal/alembic_${PROJECT}/alembic/versions/.
