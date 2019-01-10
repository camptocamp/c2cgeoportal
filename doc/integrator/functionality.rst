Functionalities
---------------

c2cgeoportal provides the concept of *functionality* that can be used to customize
the application according to the user's permissions.

A functionality may be associated to users through different ways:

1. Functionalities for anonymous users are defined through the
   ``functionalities:anonymous`` variable in the ``vars.yaml`` configuration file.
2. Functionalities for authenticated users are defined through the
   ``functionalities:registered`` variable in the ``vars.yaml`` configuration file.
3. Functionalities for specific roles are defined in the database through the administration interface.
4. Functionalities for specific users are defined in the database through the administration interface.

Each level overrides the previous ones in the same order as indicated above.
For example, if the user is authenticated and has associated functionalities in
the ``user`` database table, then the ``functionalities:anonymous`` and
``functionalities:registered`` configuration variables, as well as any
functionality associated with his/her role, will be ignored.

Configuration
~~~~~~~~~~~~~

The ``vars.yaml`` file includes variables for managing *functionalities*.

``admin_interface``/``available_functionalities``
    List of functionality types that should be available in the administration interface (and added to the
    ``functionality`` table in the database).

    For example:

    .. code:: yaml

        admin_interface:
            available_functionalities:
            - default_basemap
            - print_template
            - mapserver_substitution

    The following syntax is also accepted:

    .. code:: yaml

        admin_interface:
            available_functionalities: [default_basemap, print_template, mapserver_substitution]


``functionalities:anonymous``
    Functionalities accessible to anonymous users. This is a list of
    key/value pairs, whose values are either arrays or scalars.

    For example:

    .. code:: yaml

        functionalities:
            anonymous:
                print_template:
                - 1 A4 portrait
                - 2 A3 landscape
                default_basemap: plan

    In this example anonymous users can print maps using the ``1 A4 portrait``
    and ``2 A3 landscape`` layouts only. And their default base layer is the
    ``plan`` layer.

``functionalities:registered``
    Functionalities accessible to any authenticated user. This is a list of
    key/value pairs, of the same form as for ``functionalities:anonymous``.

``functionalities:available_in_templates``
    Functionalities that are made available to Mako templates (e.g.
    ``viewer.js``) through the ``functionality`` template variable.

    For example with:

    .. code:: yaml

        functionalities:
            available_in_templates:
            - <functionality_name>

    if a user is associated to, say,
    ``<functionality_name>``/``value1`` and ``<functionality_name>``/``value2``,
    then the ``functionality`` template variable will be set to a dict with one
    key/value pair: ``"<functionality_name>": ["value1","value2"]``.

Usage in Javascript client
~~~~~~~~~~~~~~~~~~~~~~~~~~

The functionalities will be send to the Javascript client application through the user web service.
To be published a functionality should be present in ``functionalities:available_in_templates`` parameter
in the ``vars.yaml`` configuration file.


Using Functionalities to configure the basemap to use for each theme
....................................................................

A default basemap may be automatically loaded when the user selects a given
theme.

Then, in the administration interface, if not available yet, define a
``default_basemap`` functionality containing the basemap reference. Edit the
theme and select the basemap to load in the ``default_basemap`` list. If
several ``default_basemap`` items are selected, only the first one will be
taken into account.
