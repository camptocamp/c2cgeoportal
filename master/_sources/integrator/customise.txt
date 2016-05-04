.. _integrator_customise:

=========================
Customise the application
=========================

There is to generic way to customise the application.

The ``functionnalities`` and the ``UI metadata``.

The functionalities will be attached to the ``role`` and the ``theme``,
and the UI metadata will be attached to all the elements of the theme.

Thy should be configured in the vars file, in the ``admin_interface`` /
``available_functionnalities`` or respectively ``available_matadata``.

It's a list of object who have a ``name`` and a ``type``.

The type can be::

* ``string``
* ``list`` a list fo string
* ``boolean``
* ``integer``
* ``float``
* ``date``
* ``time``
* ``datetime`` `see the python-dateutil documentation <http://labix.org/python-dateutil#head-b95ce2094d189a89f80f5ae52a05b4ab7b41af47>`
* ``url`` see bellow

URL
---

In the admin interface we can use in all the URL the following special schema:

* ``static``: to use a static route,

  * ``static:///icon.png`` will get the URL of the ``static-ngeo`` static route of the project.
  * ``static://static-cgxp/icon.png`` will get the URL of the ``static-cgxp`` static route of the project.
  * ``static://prj:img/icon.png`` will get the URL of the ``img`` static route of ``prj``.

* ``config``: to get the server name from the URL, with the config from the ``vars`` file:

  .. code:: yaml

     servers:
        my_server: http://example.com/test

  ``config://my_server/icon.png`` will be transformed into
  the URL ``http://example.com/test/icon.png``.
