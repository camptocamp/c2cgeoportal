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

* ``checker_main``: Check the main page.
* ``checker_viewer``: Check the viewer.js used by the main page.
* ``checker_edit``: Check the edit page.
* ``checker_edit_js``: Check the edit.js used by the edit page.
* ``checker_apiloader``: Check the API loader.
* ``checker_printcapabilities``: Check the print capabilities.
* ``checker_pdf``: Check the print (try to print a page).
* ``checker_fts``: Check the FullTextSearch.
* ``checker_wmscapabilities``: Check the WMS GetCapabilities.
* ``checker_wfscapabilities``: Check the WFS GetCapabilities.

Configuration in ``vars_<project>.yaml``:

.. code:: yaml

    checker:
        print_template: 1 A4 portrait
        print_center_lon: to be defined
        print_center_lat: to be defined
        print_scale: 10000
        fulltextsearch: text to search

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
