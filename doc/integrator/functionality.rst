Functionalities
-------------------------------------------------

c2cgeoportal provides the concept of *functionality* that can be used to customize
the application according to the user's permissions.

A functionality may be associated to users through different ways:

1. Functionalities for anonymous users are defined through the
   ``functionalities:anonymous`` variable in the ``vars_<project>.yaml``
   configuration file.
2. Functionalities for authenticated users are defined through the
   ``functionalities:registered`` variable in the ``vars_<project>.yaml``
   configuration file.
3. Functionalities for specific roles are defined in the database through the
   administration interface.
4. Functionalities for specific users are defined in the database through the
   administration interface.

Each level overrides the previous ones in the same order as indicated above.
For example, if the user is authenticated and has associated functionalities in
the ``user`` database table, then the ``functionalities:anonymous`` and
``functionalities:registered`` configuration variables, as well as any
functionality associated with his/her role, will be ignored.

Configuration
~~~~~~~~~~~~~

The ``vars_<project>.yaml`` file includes variables for managing *functionalities*.

``admin_interface``/``available_functionalities``
    List of functionality types that should be available in the
    administration interface (and added to the ``functionality`` table in the
    database).

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

Usage in Templates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As explained in the configuration section above,
a functionality can be used in the Mako templates as long as it has been
enabled using the ``functionalities:available_in_templates`` parameter in the
``vars_<project>.yaml`` configuration file.

Functionalities may be used in templates for various purposes. The examples
below explain how to set the default basemap and how to limit access to some
plugins according to the user's permissions.

Example of the default_basemap Functionality
............................................

Using functionalities, it is easy to set the default basemap that will be
displayed when a user loads the application depending on whether he/she is
anonymous, authenticated or has some specific role.

First make sure that ``default_basemap`` is made available in the templates
using the ``functionalities:available_in_templates`` parameter in the
``vars_<project>.yaml`` configuration file:

.. code:: yaml

    functionalities:
        available_in_templates: [default_basemap]

Then indicate (still in ``vars_<project>.yaml``) what default basemap should be used
for anonymous users:

.. code:: yaml

    functionalities:
        anonymous:
            # some other configs...
            default_basemap: <some_basemap>

Optionally you may also indicate what basemap to use for authenticated users
(if omitted, the anonymous ``default_basemap`` value will be used):

.. code:: yaml

    functionalities:
        anonymous:
            # ...
        registered:
            default_basemap: <some_other_basemap>

Finally you may link ``default_basemap`` functionalities to some roles or
users in the administration interface.

So that the ``default_basemap`` is actually provided to the
``cgxp_mapopacityslider`` plugin, use the following configuration in your
project's ``viewer.js`` template:

.. code:: javascript

    {
        ptype: "cgxp_mapopacityslider",
        defaultBaseLayerRef: "${functionality['default_basemap'][0] | n}"
    }

Limiting Access to some CGXP Plugins using Functionalities
..........................................................

Functionalities may also be used to enable some CGXP plugins only for users
with specific roles.

To do so, add ``authorized_plugins`` to the list of functionalities that must be
available in the administration interface and to the list of functionalities
provided to the templates. Set also ``authorized_plugins`` as an empty list for
anonymous users. In ``vars_<project>.yaml``:

.. code:: yaml

    admin_interface:
        # ...
        available_functionalities:
            - default_basemap
            - print_template
            - mapserver_substitution
            - authorized_plugins

    functionalities:
        # ...
        anonymous:
            # ...
            default_basemap: <some_basemap>
            authorized_plugins: []

        available_in_templates: [default_basemap, authorized_plugins]

Then you may test in your project's ``viewer.js`` template if the current user
has been granted access to some protected plugins:

.. code:: javascript

    app = new gxp.Viewer({
        // ...
        tools: [{
            //...
        },
        % if '<some_protected_plugin>' in functionality['authorized_plugins']:
        {
            ptype: ...
            //...
        },
        % endif
        {
            //...
        }]
    });

Using Functionalities list to configure the layers in the QueryBuilder
......................................................................

Add the new ``querybuilder_layer`` functionality to the list of
``available_functionalities`` in your ``vars_<project>.yaml`` file:

.. code:: yaml

    admin_interface:
        available_functionalities:
            ...
            - querybuilder_layer

Make sure that the ``dumps`` function is imported in
``<package>/templates/viewer.js`` using:

.. code:: python

   <%
   from json import dumps
   %>

And configure your plugin like that:

.. code:: javascript

    {
        ptype: "cgxp_querier",
        featureTypes: ${dumps(functionality['querybuilder_layer']) | n},
        ...
    }

This way you may assign more than one layer per role using functionalities.

Using Functionalities to configure the basemap to use for each theme
....................................................................

A default basemap may be automatically loaded when the user selects a given
theme.

To do so make sure that the ``MapOpacitySlider`` plugin has a reference to the
layertree plugin. For instance:

.. code:: javascript

    {
        ptype: "cgxp_mapopacityslider",
        layerTreeId: "layertree",
        defaultBaseLayerRef: "${functionality['default_basemap'][0] | n}"
    }

Then, in the administration interface, if not available yet, define a
``default_basemap`` functionality containing the basemap reference. Edit the
theme and select the basemap to load in the ``default_basemap`` list. If
several ``default_basemap`` items are selected, only the first one will be
taken into account.
