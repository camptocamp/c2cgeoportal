.. _integrator_subdomain:

Subdomain
=========

If you want to optimize the parallelization of static resource downloads, you
can use subdomains by defining in the ``vars_<project>.yaml``
something like this:

.. code:: yaml

    # subdomains for static resources
    subdomains: ['s1', 's2', 's3', 's4']

Those subdomains must be defined in the DNS and in the Apache
vhost. If the application is served on different URL and you want to use
the subdomains on only one of them, you can define in the ``vars_<project>.yaml``
the following:

.. code:: yaml

    # The URL template used to generate the subdomain URL
    # %(sub)s will be replaced by the sub domain value.
    subdomain_url_template: http://%(sub)s.{host}
