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
* ``PRINT_VERSION``: , The print version we want to use (``2``, ``3`` or ``NONE``), defaults to ``3``.
* ``TILECLOUD_CHAIN``: ``TRUE`` to indicate that we use TileCloud-chain, defaults to ``TRUE``.


Custom rules
------------

In the ``<package>.mk`` file we can create some other rules.
Here is a simple example that copies a file:

.. code:: makefile

    DESTINATION_FILE = <destination file>
    PRE_RULES = $(DESTINATION_FILE)

    $(DESTINATION_FILE): <source file>
        cp $< $@

Upstream `make documentation <https://www.gnu.org/software/make/manual/make.html>`_.
