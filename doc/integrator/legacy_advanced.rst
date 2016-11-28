.. _integrator_advanced:

Advanced configuration examples
===============================

We can use the ``functionalities`` or the ``vars_<project>.yaml`` to configure the
interface. For instance:

Activate CGXP plugin using an ``authorized_plugins`` functionality:

.. code:: javascript

   % if 'my_plugin' in functionality['authorized_plugins']:
   {
       // plugin configuration
   },
   % endif


Configure the ``querier`` layer using the ``vars_<project>.yaml``,
Add in ``vars_<project>.yaml``:

.. code:: yaml

    viewer:
        feature_types:
        - layer_1
        - layer_2

Add in your project Makefile ``<package>.mk``:

.. code:: makefile

   CONFIG_VARS += viewer

And in ``viewer.js``:

.. code:: javascript

    <%
    from json import dumps
    %>
    % if len(request.registry.settings['viewer']['feature_types']) > 0:
    {
        ptype: "cgxp_querier",
        // plugin configuration
        featureTypes: ${dumps(request.registry.settings['viewer']['feature_types']) | n}
    },
    % endif
