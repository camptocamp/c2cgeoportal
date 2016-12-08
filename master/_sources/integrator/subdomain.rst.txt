.. _integrator_subdomain:

Sub domain
==========

If you want to optimize the parallelization of static resource download you
can use sub domain to do that you should define in the ``vars_<project>.yaml``
something like this:

.. code:: yaml

    # The used sub domain for the static resources
    subdommains: ['s1', 's2', 's3', 's4']

Those sub domain should obviously be define in the DNS and in the Apache
vhost. If the application is served on deferent URL and you want to use
the sub domain on only one of them you can define in the ``vars_<project>.yaml``
the following:

.. code:: yaml

    # The URL template used to generate the sub domain URL
    # %(sub)s will be replaced by the sub domain value.
    subdomain_url_template: http://%(sub)s.{host}
