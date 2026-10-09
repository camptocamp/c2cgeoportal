.. _integrator_checker:

Automated check
===============

c2cgeoportal applications include functionality for testing and assessing that the application is
functioning correctly, i.e. that its web services respond as expected.

For this purpose, c2cgeoportal provides a *checker* and a *check_collector*.
These (especially the collector) are meant to be used by a
monitoring system like Nagios to check that the application is alive.

They integrate into c2cwsgiutils's health check service. The return codes are:

* ``200`` => OK
* ``500`` => Error

.. Note::

    Check collector can only check pages that are on the same server as itself.

You can access the health_check service with this kind of url:

    <project_url>/c2c/health_check?max_level=3

The levels used in the default configuration (recommended settings):

* ``1``: Fatal checkers (main database connection, alembic versions).
* ``2``: Vital checkers (other database connection, redis connexions, versions).
* ``3``: Quick internal checks.
* ``4``: Slow service checks (phantomjs checks, theme).
* ``5``: Service checks (caution: these can result in costs, for example, print a page).
* ``10``: collector of different sites.

See also: https://github.com/camptocamp/c2cwsgiutils/#health-checks

The recommended URL that should be checked by services such as Pingdom or StatusCake:

    <project_url>/c2c/health_check?checks=check_collector

The recommended URL to use to validate a migration (``checker_url`` in ``project.yaml``):

    <project_url>/c2c/health_check?max_level=9

Checker
-------

The checker uses the following configuration structure in ``vars.yaml``:

.. code:: yaml

   vars:
       # Global configuration
       ...
       checker:
           # Checker configurations

.. note::

    If some of the checked services require an authenticated user, the
    ``forward_headers`` configuration allows to forward ``Cookie`` or ``Authorisation`` headers
    from the underlying requests.

    .. code:: yaml

        checker:
            forward_headers: ['Cookie', 'Authorisation']

.. note::

    The checker assumes that it can access the c2cgeoportal services via ``http://localhost``.
    If this is not allowed on your server, you can override this behavior as follows.
    In your ``vars`` file, add the following:

    .. code:: yaml

        vars:
            checker:
                rewrite_as_http_localhost: False

    Now, in your configuration file ``project.yaml``, instead of defining the ``checker_path``,
    define a ``checker_url`` with the full URL to be used, for example:

    .. code:: yaml

        ...
        host: ${host}
        checker_url: https://${host}${entrypoint}check_collector?
        ...


``print``
~~~~~~~~~

Check the print version 3.x (try to print a page).

Uses as spec the ``spec`` from configuration.

``fulltextsearch``
~~~~~~~~~~~~~~~~~~

Check that the Full-text search service returns an element.

Uses the ``search`` from configuration as text to search.

``themes``
~~~~~~~~~~

Check that the theme has no error for all interfaces present in the database.

Uses the ``themes`` configuration:

.. code:: yaml

   themes:
       params:
           # Dictionary that represents the query string
       <interface>:
           params:
               # Dictionary that represents the query string
       level: 2

``lang``
~~~~~~~~

Check that all the language files are present.

Uses the global configuration ``available_locale_names``, and the checker configuration ``files``,
an array of strings that must be in ``[ngeo]``.

``routes``
~~~~~~~~~~

Check some routes, configured in ``routes`` as array of objects with:

* ``name``: the route name.
* ``display_name``: the name to be displayed.
* ``params``: the used query string as a dictionary.
* ``level``

In the configuration, we can also fill the ``routes_disable`` to disable some routes.

``phantomjs``
~~~~~~~~~~~~~

Check with phantomjs that the pages load correctly without errors,
using the ``routes`` configuration as an array of route names to check:

* ``name``: the route name.
* ``params``: the query string to use, configured as a dictionary.
* ``level``

Infrastructure
--------------

If you experience connection issues with your checker, the following configuration options may be useful for you:

.. code:: yaml

   vars:
     checker:
       [base_internal_url]: URL like http://localhost:8080
       [forward_host]: <True|False>

Check collector
---------------

Used to collect checks from a different instance in the parent/children
structure. It is useful to perform a set of checks all at once.

The check collector uses the following configuration structure:

.. code:: yaml

   vars:
       # Global configuration
       ...
       check_collector:
           max_level: 1
           level: 2
           hosts: []

The ``max_level`` is the default max_level parameter used for every host. The ``max_level`` option can be set
for a host to override it.

To add a host:

.. code:: yaml

    vars:
        check_collector:
            hosts:
              - display: Child
                url: https://{host}/child
                max_level: 1

    update_paths:
      - check_collector.hosts
