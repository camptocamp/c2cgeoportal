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

Configuration in ``config.yaml.in``:

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

A typical configuration:

.. code:: yaml

    check_collector:
        check_type:
            all:
                - name: checker_main
                  display: Main page
                - name: checker_viewer
                  display: Viewer script
                - name: checker_edit
                  display: Edit page
                - name: checker_edit_js
                  display: Edit script
                - name: checker_apiloader
                  display: API loader
                - name: checker_printcapabilities
                  display: Print capabilities
                - name: checker_pdf
                  display: Print PDF
                - name: checker_fts
                  display: FullTextSearch
                - name: checker_wmscapabilities
                  display: WMS capabilities
                - name: checker_wfscapabilities
                  display: WFS capabilities
            main:
                - name: checker_main
                  display: Main page
                - name: checker_viewer
                  display: Viewer script
                - name: checker_printcapabilities
                  display: Print capabilities
                - name: checker_pdf
                  display: Print PDF
                - name: checker_apiloader
                  display: API loader
            default: # for children
                - name: checker_viewer
                  display: Viewer script
        hosts:
            - display: Parent
              url: http://${vars:host}/main/wsgi
              type: main
            - display: Child 1
              url: http://${vars:host}/child1/wsgi
            - display: Child 2
              url: http://${vars:host}/child2/wsgi

``check_collector/check_type/<name>`` is the list of definitions of the
checkers that we want to apply on a host,
``name`` is the name of the checker described in the
Checker section, ``display`` is just a text used in the result page.

``check_collector/hosts`` is a list of hosts, ``display`` is just a text
used in the result page, ``url`` is the WSGI URL of the application,
``type`` is the type of checkers list that we want to use on this host
(default is 'default').

We can use an argument type of the script to call a specific
list of checks on all hosts, for example::

    http://example.com/main/wsgi/check_collector?type=all
