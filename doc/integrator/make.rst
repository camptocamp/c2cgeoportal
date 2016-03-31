.. _integrator_make:

Build the project with Make
===========================

Makefiles
---------

Usually we have the following makefiles includes:
``<user>.mk`` -> ``<package>.mk`` -> ``CONST_Makefile.mk``.

The ``CONST_Makefile.mk`` is a huge makefile that is maintained by the
GeoMapFish developers.

The ``<package>.mk`` contains the project-specific config and rules,
Default is:

.. code:: makefile

    ifdef VARS_FILE
    VARS_FILES += ${VARS_FILE} vars_<package>.yaml
    else
    VARS_FILE = vars_<package>.yaml
    VARS_FILES += ${VARS_FILE}
    endif

    include CONST_Makefile


And the ``<user>.mk`` contains the user-specific config (mainly the
``INSTANCE_ID`` config), and should look like:

.. code:: makefile

    INSTANCE_ID = <user>
    DEVELOPMENT = TRUE

    include <package>.mk


Vars files
----------

The project variables are set in the ``vars_<package>.yaml`` file,
which extends the default ``CONST_vars.yaml``.

To make such variables available to the python code, for instance using

.. code:: python

    request.registry.settings.get('some_config_var')

they must be listed in the makefile as well using ``CONFIG_VARS`` (see below).

For more information see the
`c2c.template <https://github.com/sbrunner/c2c.template>`_ documentation.


Makefile config variables
-------------------------

The following variables may be set in the makefiles:

* ``APACHE_ENTRY_POINT``: The apache entry point, defaults to ``/$(INSTANCE_ID)/``.
* ``APACHE_VHOST``: The vhost folder name in ``/var/www/vhost``.
* ``CGXP``: ``TRUE`` to build the CGXP interface, defaults to ``TRUE``.
* ``CONFIG_VARS``: The list of parameters read from the project yaml configuration file.
* ``DEVELOPMENT``: if ``TRUE`` the ``CSS`` and ``JS`` files are not minified and the
  ``development.ini`` pyramid config file is used, defaults to ``FALSE``.
* ``DISABLE_BUILD_RULES``: List of rules we want to disable, default is empty.
* ``INSTANCE_ID``: The WSGI instance id (should be unique on a server).
* ``LANGUAGES``: the list of available languages.
* ``MOBILE``: ``TRUE`` to build the Sencha Touch interface, defaults to ``TRUE``.
* ``NGEO``: ``TRUE`` to build the ngeo interface, defaults to ``FALSE``.
* ``POST_RULES``: postdefine some build rules, default is empty.
* ``PRE_RULES``: predefine some build rules, default is empty.
* ``PRINT_VERSION``: , The print version we want to use (``3`` or ``NONE``), defaults to ``3``.
* ``TILECLOUD_CHAIN``: ``TRUE`` to indicate that we use TileCloud-chain, defaults to ``TRUE``.


Custom rules
------------

In the ``<package>.mk`` file we can create some other rules.
Here is a simple example that creates the
`/var/sig/tiles/1.0.0/WMTSCapabilities.xml` file
and removes it on the `clean` rule:

.. code:: makefile

    WMTSCAPABILITIES_FILE ?= /var/sig/tiles/1.0.0/WMTSCapabilities-$(INSTANCE_ID).xml

    PRE_RULES = $(WMTSCAPABILITIES_FILE)

    $(WMTSCAPABILITIES_FILE): tilegeneration/config.yaml .build/dev-requirements.timestamp
        $(VENV_BIN)/generate_controller --capabilities

    clean: project-clean
    .PHONY: project-clean
    project-clean:
        rm -f $(WMTSCAPABILITIES_FILE)

``tilegeneration/config.yaml`` and ``.build/dev-requirements.timestamp`` are the files
that must be built to run the current rule.

``$(VENV_BIN)/generate_controller --capabilities`` is the command that generates the wanted file.

And if you don't want the instance id in the production file you can put in your production mk file:

.. code:: makefile

    WMTSCAPABILITIES_FILE = /var/sig/tiles/1.0.0/WMTSCapabilities.xml

Note
----

The ``.build/*.timestamp`` files are not really required  but they are flags
indicating that an other rule is correctly done.

Upstream `make documentation <https://www.gnu.org/software/make/manual/make.html>`_.
