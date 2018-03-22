.. _integrator_checker:

Automated check
===============

c2cgeoportal applications include functionality for testing and assessing that the application is correctly
functioning, i.e. that its web services respond as expected.

For that we have parts: a *checker* and a *check_collector*.

Those (especially the collector) are meant to be used by a
monitoring system like Nagios to check that the application is alive.

They integrate into c2cwsgiutils's health check service. The return code are:

* ``200`` => OK
* ``500`` => Error

.. Note::

    Check collector can only check pages that are on the same server as it.

You can access the health_check service with this kind of url:

    <project_url>/c2c/health_check?max_level=3

The used levels with the default configuration (recommended):

* ``1``: Vital checkers (quick checks).
* ``3``: Slow service check like print and GetCapabilities.
* ``10``: collector of different sites.

See also: https://github.com/camptocamp/c2cwsgiutils/#health-checks

The recommended URL that should be checked by e service like Pingdom:

    <project_url>/c2c/health_check?checks=check_collector

The recommended URL to use to validate the migration (``checker_url`` in ``proect.yaml.mako``):

    <project_url>/c2c/health_check?max_level=9

.. note::

    For non Docker project the ``<project_url>`` should ends with ``/wsgi``.

Checker
-------

The checker use the following configuration structure in ``vars_<project>.yaml``:

.. code:: yaml

   vars:
       # Global configuration
       ...
       checker:
           # Checker configurations

.. note::

    If some of the checked services require an authenticated user, the
    ``forward_headers`` allows to forward ``Cookie`` or ``Authorisation`` headers
    in the underlying requests.

    .. code:: yaml

        checker:
            forward_headers: ['Cookie', 'Authorisation']

``print``
~~~~~~~~~

Check the print version 3.x (try to print a page).

Use as spec the ``spec`` from configuration.

``fulltextsearch``
~~~~~~~~~~~~~~~~~~

Check that the FullText-search service return an element.

Use the ``search`` from configuration as text to search.

``themes``
~~~~~~~~~~

Check that the theme has no error for all interface present in the database.

It use the ``themes`` configuration:

.. code:: yaml

   themes:
       params:
           # Dictionary that represent the query string
       <interface>:
           params:
               # Dictionary that represent the query string
       level: 2

``lang``
~~~~~~~~

Check that all the language files are present,
use the global configuration ``available_locale_names``, and the checker configuration
``files``, an array of string that must be in ``[cgxp, cgxp-api, ngeo]``.

``routes``
~~~~~~~~~~

Check some routes, configured in ``routes`` as array of objects with::

  * ``name`` witch is the route name.
  * ``params`` the used query string as a dictionary.
  * ``level``

In the configuration we can also fill the ``routes_disable`` to disable some routes.

``phantomjs``
~~~~~~~~~~~~~

Check with phantomjs that the pages load correctly without errors,
use the ``routes`` configuration as an array of route name to check::

  * ``name`` witch is the route name.
  * ``params`` the used query string as a dictionary.
  * ``level``


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
           max_level: 1
           level: 2
           hosts: []

The ``max_level`` is the default max_level parameter used for every hosts. The ``max_level`` option can be set
for a host to override it.

To add a host:

.. code:: yaml

    vars:
        check_collector:
            hosts:
            - display: Child
              url: http://{host}/child/wsgi
              max_level: 1

    update_paths:
    - check_collector.hosts
