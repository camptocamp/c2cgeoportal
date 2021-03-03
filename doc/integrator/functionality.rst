Functionalities
---------------

c2cgeoportal provides the concept of *functionality* that can be used to customize
the application according to the user's permissions.

A functionality may be associated to users through the admin interface.

Some technical roles are used to define default functionalities depending on the user's context,
they are named `anonymous`, `registered` and `intranet`.

User get functionalities from, by priority order:

If authenticated::

    - roles associated to his user profile
    - role named `registered`

If his IP is included in the intranet networks::

    - role named `intranet`

In all cases::

    - role named `anonymous`


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

Usage in JavaScript client
~~~~~~~~~~~~~~~~~~~~~~~~~~

The functionalities will be sent to the JavaScript client application through the user web service.
To be published, a functionality should be present in the parameter ``functionalities:available_in_templates``
parameter in the ``vars.yaml`` configuration file.


Using Functionalities to configure the basemap to use for each theme
....................................................................

A default basemap may be automatically loaded when the user selects a given
theme. This can be configured in the administration interface, as follows:
if not available yet, define a
``default_basemap`` functionality containing the basemap reference. Edit the
theme and select the basemap to load in the ``default_basemap`` list. If
several ``default_basemap`` items are selected, only the first one will be
taken into account.
