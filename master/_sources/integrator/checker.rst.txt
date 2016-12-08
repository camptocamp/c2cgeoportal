.. _integrator_checker:

Automated check
===============

c2cgeoportal applications include web services for testing
and assessing that the application is correctly functioning,
ie. that its web services respond as expected.

For that we have two services: a *checker* and a *check_collector*.

Those services (especially the collector) are meant to be used by a
monitoring system like Nagios to check that the application is alive.

The return code are:

* ``200``-``299`` => OK
* ``400``-``499`` => Warning
* ``500``-``599`` => Error

.. Note::

    Check collector can only check pages that are on the same server as it.


Checker
-------

The checker use the following configuration structure:

.. code:: yaml

   vars:
       # Global configuration
       ...
       checker:
           default:
               # Default checkers configuration
           <type>: # type of checker get from the query string
               # Checker configuration

.. note::

    If some of the checked services require an authenticated user, the
    ``forward_headers`` allows to forward ``Cookie`` or ``Authorisation`` headers
    in the underlying requests.

    .. code:: yaml

        checker:
            forward_headers: ['Cookie', 'Authorisation']

``checker_pdf``
~~~~~~~~~~~~~~~

Legacy, check the print version 2.x (try to print a page).

Use the following configuration items::

  * ``print_template``
  * ``print_center_lon``
  * ``print_center_lat``
  * ``print_scale``

``checker_pdf3``
~~~~~~~~~~~~~~~~

Check the print version 3.x (try to print a page).

Use as spec the ``print_spec`` from configuration.

``checker_fts``
~~~~~~~~~~~~~~~

Check that the FullText-search service return an element.

Use the ``fulltextsearch`` from configuration as text to search.

``checker_theme_errors``
~~~~~~~~~~~~~~~~~~~~~~~~

Check that the theme has no error for all interface present in the database.

It use the ``themes`` configuration:

.. code:: yaml

   themes:
       defaults:
           params:
               # Dictionary that represent the query string
       <interface>:
           params:
               # Dictionary that represent the query string

``checker_lang_files``
~~~~~~~~~~~~~~~~~~~~~~

Check that all the language files are present,
use the global configuration ``available_locale_names``, and the checker configuration
``lang_files``, an array of string that must be in ``[cgxp, cgxp-api, ngeo]``.

``checker_routes``
~~~~~~~~~~~~~~~~~~

Check some routes, configured in ``routes`` as array of objects with::

  * ``name`` witch is the route name.
  * ``params`` the used query string as a dictionary.

In the configuration we can also fill the ``routes_disable`` to disable some routes.

``checker_phantomjs``
~~~~~~~~~~~~~~~~~~~~~

Check with phantomjs that the pages load correctly without errors,
use the ``phantomjs_routes`` configuration as an array of route name to check::

  * ``name`` witch is the route name.
  * ``params`` the used query string as a dictionary.

Configuration in ``vars_<project>.yaml``:

.. code:: yaml

    checker:
        defaults:
            <the config>
        <a type>:
            <overide the default config for a specific type>

Check collector
---------------

Used to collect checks from a different instance in the parent/children
structure. It is useful to perform a set of checks all at once.

The checker collector use the following configuration structure:

.. code:: yaml

   vars:
       # Global configuration
       ...
       check_collector:
           disable: # List of checker name that will be disable
           check_type:
               default:
                   # The checker available for all type
               <type>: # type of checker get from the query string
               - name: # The checker name (see above)
                 display: # The text to display in the result page

To disable a predefined check do this:

.. code:: yaml

    vars:
        check_collector:
            disabled:
            - <name>

    update_paths:
    - check_collector


To add a host:

.. code:: yaml

    vars:
        check_collector:
            hosts:
            - display: Child
              url: http://{host}/child/wsgi

    update_paths:
    - check_collector.hosts

We can use an argument type of the script to call a specific
list of checks on all hosts, for example::

    http://example.com/main/wsgi/check_collector?type=all
