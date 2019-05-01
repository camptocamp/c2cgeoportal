.. _integrator_print:

Print
=====

Template configuration
----------------------

All print-related files are located in the ``print/`` folder, and the files related to the template in the
``print/print-apps/<package>`` folder.

The main configuration file is ``print/print-apps/<package>/config.yaml``.

* `MapFish print documentation <https://mapfish.github.io/mapfish-print-doc/>`_
* `Startup with Jasper Reports <https://mapfish.github.io/mapfish-print-doc/#/jasperReports>`_


Notes about the scales
----------------------

The web map and the map printing do not use the same scales. Therefore, if you change the configuration
of min/max scaling, you should also test map printing to be sure that it also works as expected.


Infrastructure
--------------

By default we use the `mutualized print platform as a service from Camptocamp <https://www.camptocamp.com/en/actualite/saas-printing-service-offer/>`.

To configure it, you should ask Camptocamp to create e.-g. two new applications on the platform, one for the integration,
one for the production.

Configure the application name in the ``MUTUALIZED_PRINT_APP`` variable of a ``Makefile``.

Development
-----------

To test the print locally you can copy the ``docker-compose.override.sample.yaml`` to ``docker-compose.override.yaml``,
and uncomment the ``PRINT_URL`` environment variable and the ``print`` service.

Internal print
--------------

To use the internal print you should:

* Set ``PRINT_URL`` to ``http://print:8080/print/`` in the ``.env.mako`` file.
* Uncomment the ``print`` service in the ``docker-compose.yaml`` file.
* Uncomment the ``!mapUri`` in the print configuration.
* Uncomment the ``print``/``spec`` configuration section of the ``checker`` in the ``vars.yaml``.
