.. _integrator_make:

Build configuration
===================

Env files
---------

Usually we have the following env files::

 - ``env.default`` for the c2cgeoportal default configuration
 - ``env.project`` for the project configuration
 - ``env.<town>`` in a multi instance project we will have sone configuration per town
 - ``env.(dev|int|prod)`` we usualy have a file per integations environment,
   not needed for OpenShift project

The usage of env file should be configured in the ``project.yaml`` file, in the ``env`` section.

Project env confguration::

 * ``files``: the env files interpreted with the build env arguments.
 * ``required_args``: the number of required build env arguments.
 * ``help``: the displayed message on wrong build env arguments number.

For an OpenShift project you can use (default):

.. code:: yaml

  env:
    files:
      - env.default
      - env.project
    required_args: 0
    help: No arguments needed.

For a non OpenShift project you can use:

.. code:: yaml

  env:
    files:
      - env.default
      - env.project
      - env.{0}
    required_args: 1
    help: You should use `./build <env>` where <env> can be dev, int or prod.

For a non OpenShift multi town project you can use:

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

The project variables are set in the ``vars.yaml`` file,
which extends the default ``CONST_vars.yaml``.

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

Dockefile config variables
--------------------------

The following variables may be set in the Dockerfile:

* ``CONFIG_VARS``: The list of parameters read from the project YAML configuration file.

Makefile config variables
-------------------------

The following variables may be set in the makefiles:

* ``DISABLE_BUILD_RULES``: List of rules we want to disable, default is empty.
* ``LANGUAGES``: List of available languages, default is ``en fr de``.
* ``NGEO_INTERFACES``: List of ngeo interfaces, default is ``mobile desktop``.

Secrets
-------

We provide an easy way to secure some files into your repository, for that you should add
in your project Makefile:

.. code:: make

   GPG_KEYS += <allowed pgp key id> # <the owner name>

   secrets.tar.bz2.gpg: <the files to encrypt>

Add the files that should be encrypted in the ``.gitignore`` file.

To encrypt the files run:

.. prompt:: bash

   make --makefile=<user>.mk secrets.tar.bz2.gpg

Add the file ``secrets.tar.bz2.gpg`` to git:

.. prompt:: bash

   git add secrets.tar.bz2.gpg

To decrypt the files run:

.. prompt:: bash

   make --makefile=<user>.mk secrets

.. note::

   If you have an issue with the ``dirmngr`` package you can try to add:
   ``pinentry-mode loopback`` in your ``~/.gnupg/gpg.conf`` file and
   ``allow-loopback-pinentry``in your ``~/.gnupg/gpg-agent.conf`` file.
   Then it should be fixed or you can also try to run it in Docker:
   ``docker exec camptocamp/geoportal:${MAIN_VERSION} make --makefile=<user>.mk secrets``


Custom rules
------------

In the ``<package>.mk`` file, you can create custom rules.
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


Note
----

The ``/build/*.timestamp`` files are flags
indicating that another rule is correctly done.

Upstream `make documentation <https://www.gnu.org/software/make/manual/make.html>`_.
