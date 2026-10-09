.. _integrator_customise:

=========================
Customize the application
=========================

.. toctree::
   :maxdepth: 2

The application can be customized with the following mechanisms:
functionalities, UI metadata and data model extensions.

The functionalities will be attached to the ``role`` and the ``theme``,
and the UI metadata will be attached to all the elements of the theme.

They should be configured in the vars file, in the ``admin_interface`` /
``available_functionalities`` or respectively ``available_metadata``.
It is a list of objects which have a ``name`` and a ``type``.

The type can be:

* ``string``
* ``list`` a list of strings
* ``boolean``
* ``integer``
* ``float``
* ``json``
* ``date``
* ``time``
* ``datetime`` `see the python-dateutil documentation <https://labix.org/python-dateutil#head-b95ce2094d189a89f80f5ae52a05b4ab7b41af47>`_
* ``url`` see below

Check ``CONST_vars.yaml`` for examples of usage.

In order to inherit the default values from ``CONST_vars.yaml``, make sure the ``update_paths`` section contains
the item ``admin_interface.available_functionalities`` or respectively ``admin_interface.available_metadata``.

URL
---

In the admin interface, we can use for all URL definitions the following special schema:

* ``static``: to use a static route,

  * ``static:///icon.png`` will get the URL of the ``static`` static route of the project.
  * ``static://custom-static/icon.png`` will get the URL of the ``custom-static`` static route of the project.
  * ``static://prj:img/icon.png`` will get the URL of the ``img`` static route of ``prj``.

* ``config``: to get the server name from the URL, with the config from the ``vars`` file:

  .. code:: yaml

     servers:
        my_server: https://example.com/test

  ``config://my_server/icon.png`` will be transformed into
  the URL ``https://example.com/test/icon.png``.

.. _integrator_functionality:

.. include:: functionality.rst

.. include:: extend_data_model.rst
