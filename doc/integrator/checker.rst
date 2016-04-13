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

Available services:

* ``checker_routes``: Check some routes, configured in ``routes`` aa array of objects
  with ``name`` and ``params``, ``routes_disable`` can be use to disable only one rule.
* ``checker_pdf3``: Check the print (try to print a page).
* ``checker_fts``: Check the FullTextSearch.
* ``checker_theme_errors``: Check the that the theme don't have errors on all the interfaces.
* ``checker_lang_files``: Check that all the language files are present,
  use the configuration global ``available_locale_names``, and the checker configuration
  ``lang_files``, an array of string that must be in ``[cgxp, cgxp-api, ngeo]``.
* ``checker_phantomjs``: Check with phantomjs that the pages load correctly without errors,
  use the ``phantomjs_routes`` configuration as an array of route name to check.

Configuration in ``vars_<project>.yaml``:

.. code:: yaml

    checker:
        defaults:
            <the config>
        <a type>:
            <overide the default config for a specific type>


If some of the checked services require an authenticated user, the
``forward_headers`` permit to forward ``Cookie`` or ``Authorisation`` headers
in the underlying requests.

.. code:: yaml

    checker:
        forward_headers: ['Cookie', 'Authorisation']

Check collector
---------------

Used to collect checks from a different instance in the parent/children
structure. It is useful to perform a set of checks all at once.

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
