.. _integrator_functionalities:

Functionalities
===============

In c2cgeoportal we have a functionalities system to manage generic
functionality.

They are define at four levels:

 - anonymous users (define in ``anonymous_functionalities`` in ``config.yaml.in``)
 - registered users (define in ``registered_functionalities`` in ``config.yaml.in``)
 - role (linked functionalities to the Role in the admin interface)
 - user (linked functionalities to the User in the admin interface)

Each level overwrite the functionalities of his previous level.

Configuration
-------------

In the ``config.yaml.in`` we have various variable that's used to configur the
functionalities:

``formalchemy_available_functionalities``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Define the functionality that we have in the combobox of the admin interface.

``anonymous_functionalities``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
As previously explain the functionality used by the anonymous users.

``registered_functionalities``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
As previously explain the functionality used by the registered users.

``webclient_string_functionalities``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
List of functionalities available in the ``viewer.js``, in the
``FUNCTIONALITY`` variable as a unique value.

For example we can have::

    var FUNCTIONALITY = {"default_basemap": "plan"};

``webclient_array_functionalities``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
List of functionalities available in the ``viewer.js``, in the
``FUNCTIONALITIES`` variable as an array.

For example we can have::

    var FUNCTIONALITIES = {"default_basemap": ["plan", "ortho"]};

