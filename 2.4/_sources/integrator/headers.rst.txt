.. _integrator_headers:

Headers
=======

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

Where ``<path>`` can be: ``main``, ``admin``, ``apihelp``, ``oldapihelp`` or ``c2c``,
``<directive>`` can be: ``default_src``, ``script_src``, `style_src``, ``img_src``,
``connect_src`` or ``worker_src``,
``[_extra]`` is a suffix to be able to extend a directive instance of completely overriding it.
