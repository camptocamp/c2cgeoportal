.. _integrator_legacy_print:

Print version 2.x
=================

The print version 2.x cannot be used in the ngeo application be it still can be used in the CGXP application.

The print version 3.x and the version 2.x cannot be used together.

To use it you should:

  * Keep the print war in your repository.
  * Add ``PRINT_VERSION ?= 2`` in your project makefile.
  * Add in the ``vars`` of your project vars file: ``print_url: http://localhost:8080/print/pdf/``.

Later on, if you want to use print version 3.x, follow the above instructions.

  * Remove your war file ``git rm print/print-servlet.war``.
  * Remove the ``PRINT_VERSION`` from your project makefile (default is 3).
  * In your project vars file remove the following keys:

    * ``vars/print_url``
