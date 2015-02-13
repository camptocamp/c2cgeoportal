.. _integrator_security:

Security
========

Enable / Disable WMS GetCapability
----------------------------------

Set ``hide_capabilities`` to ``true`` in your ``vars_<project>.yaml`` to disable 
the WMS GetCapability when accessing the Mapserver proxy (mapserverproxy).

Default: ``false``

Enable / Disable layer(s) in the WMS GetCapability
--------------------------------------------------

To hide protected layers from the WMS GetCapabilities, set ``use_security_metadata`` to ``true`` in your ``vars_<project>.yaml``.

Be careful that too many protected layers will cause an error because Apache has a
8190 characters hard limit for GET query length.

Default: ``false``

Enable / Disable the admin interface
------------------------------------

To disable the admin interface, set ``enable_admin_interface`` to ``false``
in your ``vars_<project>.yaml`` file.

Default: ``true``

Enable / Disable the OGC proxy
------------------------------

To disable the OGC proxy, set ``ogcproxy_enable`` to ``false`` in your
``vars_<project>.yaml`` file.

Default: ``true``
