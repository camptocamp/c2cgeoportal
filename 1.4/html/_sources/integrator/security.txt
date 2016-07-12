.. _integrator_security:

Security
========

Enable / Disable WMS GetCapability
----------------------------------

Set ``hide_capabilities`` to ``true`` in your ``<package>/config.yaml.in`` to disable 
the WMS GetCapability when accessing the Mapserver proxy (mapserverproxy).

default: ``false``

Enable / Disable layer(s) in the WMS GetCapability
--------------------------------------------------

To hide protected layers from the WMS GetCapabilities, set ``use_security_metadata`` to ``true`` in your ``<package>/config.yaml.in``.

Be careful as too many protected layers will cause an error because Apache has a 
8190 characters hard limit for GET query length.

default: ``false``
