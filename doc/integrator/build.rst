.. _integrator_build:

Build configuration
===================

Env files
---------

Usually we have the following env files:

* ``env.default`` for the c2cgeoportal default configuration.
* ``env.project`` for the project configuration.
* ``env.<organization>`` in a multi-organization project, these files will contain organization-specific
  configurations.
* ``env.(dev|int|prod)`` environment specific settings, for example one for development, one for integration
  and one for production. This is not needed for projects managed in a Kubernetes platform.

The usage of env file should be configured in the ``project.yaml`` file, in the ``env`` section.

Project env configuration:

* ``files``: the env files interpreted with the build env arguments.
* ``required_args``: the number of required build env arguments.
* ``help``: the message displayed on wrong build env arguments number.

For a Kubernetes project, you can use (default):

.. code:: yaml

  env:
    files:
      - env.default
      - env.project
    required_args: 0
    help: No arguments needed.

For a non-Kubernetes project, you can use:

.. code:: yaml

  env:
    files:
      - env.default
      - env.project
      - env.{0}
    required_args: 1
    help: You should use `./build <env>`, where <env> can be dev, int or prod.

For a non-K8S multi-organisation project, you can use:

.. code:: yaml

  env:
    files:
      - env.default
      - env.project
      - env.{0}
      - env.{1}
    required_args: 2
    help: You should use `./build <town> <env>` where <env> can be dev, int or prod.

Vars files
----------

The project variables are set in the ``geoportal/vars.yaml`` file,
which extends the default ``geoportal/CONST_vars.yaml``.

To make such variables available to the python code, for instance using

.. code:: python

    request.registry.settings.get('some_config_var')

they must be listed in the makefile as well using ``CONFIG_VARS`` (see below).

To be able to use a variable from the makefile in the vars file,
you should export your variable as follows:

.. code:: make

   export MY_VAR ?= my_value

And in your yaml vars file, add:

.. code:: yaml

   vars:
      ...
      my_var: MY_VAR
   interpreted:
      ...
      environment:
      - ...
      - my_var

For more information, see the
`c2c.template <https://github.com/camptocamp/c2c.template>`_ documentation.

Dockerfile config variables
---------------------------

The following variables may be set in the Dockerfile:

* ``CONFIG_VARS``: The list of parameters read from the project YAML configuration file.

Makefile config variables
-------------------------

.. note::

    This is not possible in the simple application mode

The following variables may be set in the makefiles:

* ``DISABLE_BUILD_RULES``: List of rules we want to disable, default is empty.
* ``LANGUAGES``: List of available languages, default is ``en fr de``.
* ``NGEO_INTERFACES``: List of ngeo interfaces, default is ``mobile desktop``.


Custom rules
------------

.. note::

    This is not possible in the simple application mode

In the ``geoportal/Makefile`` file, you can create custom rules.
Here is an example:

.. code:: makefile

    MY_FILE ?= <file>

    build: $(MY_FILE)

    $(MY_FILE): <source_file>
        cp <source_file> $(MY_FILE)
        # Short version:
        # cp $< $@

    clean: project-clean
    .PHONY: project-clean
    project-clean:
        rm -f $(MY_FILE)


Upstream `make documentation <https://www.gnu.org/software/make/manual/make.html>`_.

Custom image
------------

In the build script, we use `docker-compose build`, as this simplifies adding a new service from another `Dockerfile`.

By adding the following in the `docker-compose.yaml` file:

.. code:: yaml

   custom:
      image: ${DOCKER_BASE}-custom:${DOCKER_TAG}
      build:
        context: custom
        args:
          GIT_HASH: ${GIT_HASH}

A new image with the suffix `-custom` will be built with the standard `./build` command and a build
argument is passed to the build with the hash of the latest Git commit.

Everything that is present in the `.env` file can be used.
