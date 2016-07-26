.. _integrator_caching:

Caching
=======

Headers
-------

By default most of the elements will be cached for 10 days by the browser.

To change this value for all the application change in the
``vars_<package>.yaml`` file the ``vars/default_max_age`` value. ``0`` will mean ``no-cache``.
The specified value is in seconds.

To change this value for a specific service add the following stricture in the
``vars_<package>.yaml``:

.. code:: yaml

    vars:
        cache_control:
            "<service_name>":
                "max_age": <max_age>

Where ``<service_name>`` can be: ``entry``, ``fulltextsearch``, ``mapserver``,
``print`` or ``layers`` (editing).


Internal
--------

The application also has an internal cache, that will be invalidated on
application start and after each modification in the ``Theme`` or the
``RestrictionArea``.

The internal cache can also be invalidated by calling the URL
``http://<server>/<instance>/wsgi/invalidate``.
