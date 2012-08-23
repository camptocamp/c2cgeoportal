.. _integrator_functionality:

Functionality
=============

c2cgeoportal provides a system for managing *functionality* in a generic way.
Functionality can be associated to users, and elements of the user interface
can change based on the user's permissions.

Functionality can be associated to users through different ways:

1. The functionality for anonymous users is defined through the
   ``anonymous_functionalities`` variable in the ``config.yaml.in``
   configuration file.
2. The functionality for authenticated users is defined through the
   ``registered_functionalities`` variable in the ``config.yaml.in``
   configuration file.
3. The functionality for a specific role is defined in the database through the
   admin interface.
4. The functionality for a specific user is defined in the database through the
   admin interface.

Each level overwrites the previous levels. For example, if the user is
authenticated and has associated functionality in the ``user`` database table
then the ``anonymous_functionalities`` and ``registered_functionalities``
configuration variables, and any functionality associated with his role, will be
ignored.

Configuration
-------------

The ``config.yaml.in`` file includes variables for managing *functionality*.

``admin_interface``/``available_functionalities``
    A list of strings representating features that can be added to the
    ``functionality`` database table through the admin interface.

    For example::

        admin_interface:
            available_functionalities:
            - default_basemap
            - print_template
            - mapserver_substitution


``functionalities``/``anonymous``
    The functionality accessible to anonymous users. This is a list of
    key/value pairs, whose values are either arrays, or scalars.

    For example::

        functionalities:
            anonymous:
                print_template:
                - 1 A4 portrait
                - 2 A3 landscape
                default_basemap: plan

    In this example anonymous users can print maps using the ``1 A4 portrait``
    and ``2 A3 landscape`` layouts only. And their default base layer is the
    ``plan`` layer.

``functionalities``/``registered``
    The functionality accessible to all authenticated users. This is a list of
    key/value pairs, of the same form of ``anonymous_functionalities``.

``functionalities``/``available_in_templates``
    The functionality that is made available to Mako templates (e.g.
    ``viewer.js``) through the ``functionality`` template variable.

    For example::

        functionalities:
            available_in_templates:
            - functionality_name

    (``functionality_name`` is just a random name.)

    With this, if the user is permitted to use, say,
    ``functionality_name``/``value1`` and ``functionality_name``/``value2``,
    then the ``functionality`` template variable will be set to a dict with one
    key/value pair: ``"functionality_name"``/``["value1","value2"]``.

    .. note::

        The ``viewer.js`` Mako template creates a js variable named
        ``FUNCTIONALITY`` from the ``functionality`` dict. For example::

            var FUNCTIONALITY = {"functionality_name": ["value1", "value2"]};
