.. _integrator_caching:

Caching
=======

Headers
-------

By default, the static elements will be cached for 10 days by the browser.

To change this value for the whole application, change in the ``vars.yaml`` file the
``vars/default_max_age`` value. ``0`` will mean ``no-cache``.
The specified value is in seconds.

For the services it will be 10 minutes.
To change this value, add the following structure in the ``vars.yaml``:

.. code:: yaml

    vars:
        headers:
            <service_name>:
                cache_control_max_age: <max_age>


Where ``<service_name>`` can be: ``entry``, ``fulltextsearch``, ``mapserver``,
``print`` or ``layers`` (editing).


Internal
--------

The application also has an internal cache. The internal cache will be invalidated on
application start and after each modification in the ``Theme`` or the ``RestrictionArea``.

The internal cache can also be invalidated by calling the URL
``https://<server>/<instance>/invalidate``.
