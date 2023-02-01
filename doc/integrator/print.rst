.. _integrator_print:

Print
=====

Template configuration
----------------------

All print-related files are located in the ``print/`` folder, notably the print templates in the
``print/print-apps/<package>`` folder.

The main configuration file is ``print/print-apps/<package>/config.yaml``.

* `MapFish Print documentation <https://mapfish.github.io/mapfish-print-doc/>`_
* `Startup with Jasper Reports <https://mapfish.github.io/mapfish-print-doc/#/jasperReports>`_

Attributes
^^^^^^^^^^

The templates make use of attributes which are either passed directly by the client (client attributes) or
processed by the print service.
The client attributes are specified in the print configuration (``print/print-apps/<package>/config.yaml``)
for each template. It's possible to remove the standard ones and to create custom ones. By default, they
appear as form fields in the UI print panel for the user to fill in. An attribute can be hidden from the UI by
adding its name in ``vars.yaml`` under ``gmfPrintOptions.hiddenAttributes``.

The standard client attributes in a new install of GeoMapFish are the following:

* ``title`` (string): title of the report (form field is visible by default)
* ``comments`` (string): comment to display in the report (form field is visible by default)
* ``debug`` (boolean): if true, the header of each section of the print template will be printed in the report. Defaults to false and is hidden from the UI by default
* ``username`` (string): filled by the client with the name of the currently logged-in user (not secured). Hidden by default, cannot be renamed
* ``timezone`` (string): filled by the client with the client timezone. Hidden by default, cannot be renamed

Template attributes managed by MapFish Print are ``mapSubReport``, ``legendDataSource``, ``legendSubReport``, ``numberOfLegendRows``,
``scalebarSubReport``, ``northArrowSubReport`` (related to the map) and ``jrDataSource`` (results of the feature query on
the map, if any).

Notes about the scales
----------------------

The web map and the map printing do not use the same scales. Therefore, if you change the configuration
of min/max scaling, you should also test map printing to be sure that it also works as expected.


Infrastructure
--------------

By default, the configuration is set up to the `mutualized print platform as a service from Camptocamp <https://www.camptocamp.com/en/actualite/saas-printing-service-offer/>`.

To use this platform, you should ask Camptocamp to create e.-g. two new applications on the platform,
one for the integration, one for the production.

Configure the application name in the ``MUTUALIZED_PRINT_APP`` variable of a ``Makefile``.

Development
-----------

To test the print locally, you can copy the ``docker-compose.override.sample.yaml`` to
``docker-compose.override.yaml``, and uncomment the ``PRINT_URL`` environment variable and the
``print`` service.

Local print
-----------

To use a local print service, you should:

* Set ``PRINT_URL`` to ``http://print:8080/print/`` in the ``env.project`` file.
* Uncomment the ``print`` service in the ``docker-compose.yaml`` file.
* Uncomment the ``!mapUri``, ``!forwardHeaders`` and ``!hostnameMatch`` in the print configuration.
* Uncomment the ``print``/``spec`` configuration section of the ``checker`` in the ``vars.yaml``.
