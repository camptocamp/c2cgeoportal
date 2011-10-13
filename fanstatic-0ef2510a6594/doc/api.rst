API
===

.. py:module:: fanstatic

WSGI components
---------------

.. autofunction:: fanstatic.Fanstatic

.. autofunction:: fanstatic.Serf

.. autoclass:: fanstatic.Injector

.. autoclass:: fanstatic.Publisher

.. autoclass:: fanstatic.LibraryPublisher

.. autoclass:: fanstatic.Delegator

Python components
-----------------

.. autoclass:: fanstatic.Library
  :members:

.. autoclass:: fanstatic.Resource
  :members:

.. autoclass:: fanstatic.Slot
  :members:

.. autoclass:: fanstatic.Group
  :members:

.. autoclass:: fanstatic.NeededResources
  :members:

.. autoclass:: fanstatic.LibraryRegistry
  :members:
  :show-inheritance:

.. autoclass:: fanstatic.ConfigurationError
  :members:
  :show-inheritance:

.. autoclass:: fanstatic.UnknownResourceError
  :members:
  :show-inheritance:

.. autoclass:: fanstatic.UnknownResourceExtensionError
  :members:
  :show-inheritance:

.. autoclass:: fanstatic.LibraryDependencyCycleError
  :members:
  :show-inheritance:

.. autoclass:: fanstatic.SlotError
  :members:
  :show-inheritance:

Functions
---------

.. autofunction:: fanstatic.get_library_registry

.. autofunction:: fanstatic.register_inclusion_renderer

.. autofunction:: fanstatic.set_resource_file_existence_checking
