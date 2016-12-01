.. _integrator_legacy_print:

Print version 2.x
=================

The print version 2.x cannot be used in the ngeo application be he still can be used in the CGXP application.

The print version 3.x and the version 2.x cannot be used together.

To use it you should::

  * Keep the print war in your repository.
  * Add ``PRINT_VERSION ?= 2`` in your project makefile.
  * Add in the ``vars`` of your project vars file: ``print_url: http://localhost:8080/print-{instanceid}/pdf/``.
  * Disable the print v3 checker and enable the print v2 one, edit your project vars file:

  .. code:: yaml

     vars:
         ...
         checker:
             defaults:
                 ...
                 routes_disable: [printproxy_capabilities]
                 routes:
                 - name: printproxy_info
                 print_template: 1 A4 portrait
                 print_center_lon: 600000
                 print_center_lat: 200000
                 print_scale: 10000

         check_collector:
             # Verify that in the `.build/config.yaml` `checker_pdf3` is present, and not `checker_pdf`.
             disabled: [checker_pdf3]

     update_paths:
     - checker.routes

Back to the print version 3.x::

  * Remove your war file ``git rm print/print-servlet.war``.
  * Remove the ``PRINT_VERSION`` from your project makefile (default is 3).
  * In your project vars file remove the following keys::

    * ``vars/print_url``
    * ``vars/checker/defaults/print_template``
    * ``vars/checker/defaults/print_center_lon``
    * ``vars/checker/defaults/print_center_lat``
    * ``vars/checker/defaults/print_scale``

  * Do not have ``printproxy_capabilities`` in ``vars/checker/defaults/routes_disable``.
  * Do not have a route named ``printproxy_info`` in ``vars/checker/defaults/routes``.
  * Do not have ``checker_pdf3`` in ``vars/check_collector/disabled``.
  * Have ``checker_pdf`` in ``vars/check_collector/disabled`` (it's possible that you can completely remove it).
  * Be sure that you do this thing in your project vars file:

  .. code:: yaml

     vars:
         ...
         checker:
             defaults:
                 ...
                 print_spec:
                     layout: "1 A4 portrait"
                     outputFormat: "pdf"
                     attributes:
                         title: ""
                         comments: ""
                         datasource: []
                         map:
                             projection: "EPSG:21781"
                             dpi: 254
                             rotation: 0
                             center: [600000, 200000]
                             scale: 100000
                             longitudeFirst: true
                             layers: []
                         legend: {}
