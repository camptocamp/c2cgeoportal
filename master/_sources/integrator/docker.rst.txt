.. _integrator_docker:

Use Docker to deploy your application
=====================================

Architecture schema
-------------------

.. image:: docker.png
.. source file is docker.dia.

Images
------

When we build the project it will generate the following images:

* ``camptocamp/<package>_geoportal:latest``
* ``camptocamp/<package>_config:latest``

The tag is by default ``latest``, but you can change it by setting the ``DOCKER_TAG`` Makefile variable.

Docker compose files
--------------------

``docker-compose.yaml``: The main file that describes the composition.
``docker-compose-lib.yaml``: Provide the base description of Geomapfish Docker services.
``.env``: Build from ``.env.mako`` the environment variable used by the composition.
``docker-compose-dev.yaml``: Use to start a webpack dev server.
``docker-compose-front.yaml``: Use to start a global front if you don't use Apache to do that.
``docker-compose-build.yaml``: Used by the ``docker-compose-run`` script.

Run the developer composition
-----------------------------

.. prompt:: bash

   docker-compose up -d

You can then access your application with http://localhost:8480/
