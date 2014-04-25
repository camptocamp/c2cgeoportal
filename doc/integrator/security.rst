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

``use_security_metadata`` in your ``<package>/config.yaml.in`` allow to enable or 
disable the filtering of the layers using Mapserver runtime 
substitution variables in METADATA to hide protected layers from the WMS GetCapabilities. 

Be careful as too many protected layers will cause an error because Apache has a 
8190 characters hard limit for GET query length.

default: ``false``
