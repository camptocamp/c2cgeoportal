Runtime configuration
=====================

In some situations, you may wish to define settings of the ``vars.yaml`` not directly,
but via an environment variable instead, to be interpreted at runtime.

On this documentation page, we will use the following examples:

* the "Google API Key" shall be set via environment variable, because you do not want the
  key value to appear in the ``vars.yaml`` file, as it is sensitive information.
* the "Password reset" link shall appear or not depending on the value of an environment
  variable. This can be helpful if you are running several instances of your project,
  where the link shall appear in some instances, but not all.


Env files
---------

For ``env`` files in general, see :ref:`integrator_build`.

Add the environment variables to your ``env`` files, set the right values for that ``env``:

* ``GOOGLE_API_KEY=<your-key>``
* ``GMF_AUTH_PWD_CHANGE=false``


Usage in vars
-------------

In your ``geoportal/vars.yaml`` file, you can refer to these environment variables,
if you list them in the ``runtime_environment``:

.. code:: yaml

  vars:
    ...
    google_api_key: '{GOOGLE_API_KEY}'
    ...
    interfaces_config:
      default:
        constants:
          ...
          gmfAuthenticationConfig:
            allowPasswordReset: '{GMF_AUTH_PWD_RESET}'
  ...
  runtime_environment:
  - name: GOOGLE_API_KEY
    default: '***REMOVED***'
  - name: GMF_AUTH_PWD_RESET
    default: 'false'

Note that, in this example, the setting ``allowPasswordReset`` was added to the default
constants, but you could add it only to specific interfaces if you prefer. However,
because the variable ``allowPasswordReset`` is a boolean, additional
processing is needed to interpret it correctly, and you must provide the
correct full path to this variable:

.. code:: yaml

  runtime_environment:
  ...
  runtime_postprocess:
  - expression: str({}).lower() in ("true", "yes", "1")
    vars:
      - interfaces_config.default.constants.gmfAuthenticationConfig.allowPasswordReset
