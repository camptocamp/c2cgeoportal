.. _integrator_headers:

Headers
=======

Global headers
--------------

``c2cgeoportal`` adds some HTTP headers on its responses with certain default values.
You may wish to override the values being written. All this is done in the configuration with the
``global _headers`` section in the vars file with the following syntax:

.. code:: yaml

    vars:
      global_headers:
        - pattern: <regex>
          headers:
            <header>: <value>

If a path matches more than one pattern, all headers listed in each match will be applied.
If the same header is matched more than once, the last value is kept.

For the ``Content-Security-Policy`` header, ``c2cgeoportal`` includes specific variables in its standard
template, to facilitate the customization of these values.
The naming of these variables follows this pattern: ``content_security_policy_<path>_<directive>[_extra]``.

Where ``<path>`` can be: ``main``, ``admin``, ``apihelp`` or ``c2c``,
``<directive>`` can be: ``default_src``, ``script_src``, `style_src``, ``img_src``,
``connect_src`` or ``worker_src``,
``[_extra]`` is a suffix to be able to extend a directive instance of completely overriding it.

Forward host
------------

Requests passing through the c2cgeoportal proxy will have their host set with the host
of the server. It's possible to keep the original host by adding the host value to preserve
in the `host_forward_host` array of strings.

.. code:: yaml

    vars:
      host_forward_host:
        - <host.one>
        - <host.two>

Headers whitelist and blacklist
-------------------------------

It's possible to filter the headers of requests with a whitelist or a blacklist.

.. code:: yaml

    vars:
      headers_whitelist: []
      headers_blacklist:
        - <header-one>
        - <header-two>

The whitelist is applied before the blacklist.
These lists are applied on each request passing through the c2cgeoportal proxy.
Pyramid will still add back its default headers.
