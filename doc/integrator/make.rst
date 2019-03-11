.. _integrator_make:

Build configuration
===================

Makefiles
---------

Usually we have the following makefile includes:
``<user>.mk`` -> ``<package>.mk`` -> ``CONST_Makefile.mk``.

The ``CONST_Makefile.mk`` is a huge makefile that is maintained by the
GeoMapFish developers.

The ``<package>.mk`` contains the project-specific config and rules,
default is:

.. code:: makefile

    ifdef VARS_FILE
    VARS_FILES += ${VARS_FILE} vars.yaml
    else
    VARS_FILE = vars.yaml
    VARS_FILES += ${VARS_FILE}
    endif

    include CONST_Makefile


.. code:: makefile

    DEVELOPMENT = TRUE

    include <package>.mk


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


Makefile config variables
-------------------------

The following variables may be set in the makefiles:

* ``CONFIG_VARS``: The list of parameters read from the project YAML configuration file.
* ``DEVELOPMENT``: If ``TRUE`` the ``CSS`` and ``JS`` files are not minified and the
    ``development.ini`` pyramid config file is used, default is ``FALSE``.
* ``DISABLE_BUILD_RULES``: List of rules we want to disable, default is empty.
* ``LANGUAGES``: List of available languages, default is ``en fr de``.
* ``CGXP_INTERFACES``: List of CGXP interfaces, default is empty.
* ``NGEO_INTERFACES``: List of ngeo interfaces, default is ``mobile desktop``.
* ``PRINT``: Mapfish print is enabled, default is ``TRUE``.
* ``TILECLOUD_CHAIN``: ``TRUE`` to indicate that we use TileCloud-chain, default is ``TRUE``.


Secrets
-------

We provide an easy way to secure some files into your repository, for that you should add
in your project makefile:

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
   ``./docker-run --home make --makefile=<user>.mk secrets``

   If you have an error about opening ``/dev/tty``, try to run it in Docker as root:
   ``./docker-run --root --home make --makefile=<user>.mk secrets``


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
