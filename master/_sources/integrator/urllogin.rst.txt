.. _integrator_urllogin:

URL login
=========

You can generate a permalink of your application to give a user direct access to protected data.

First, you should configure ``urllogin`` in the vars file:

.. code:: yaml

    urllogin:
        aes_key: foobarfoobar1234

The AES key must be either 16, 24, or 32 bytes long.

To generate a key, you can use the ``docker compose exec geoportal urllogin`` command:

.. argparse::
   :ref: c2cgeoportal_geoportal.scripts.urllogin.get_argparser
   :prog: docker compose exec geoportal urllogin

This generates a token like: ``auth=148b60cc...`` that you can add in the query string of the permalink.

When the user uses this link, s/he will be connected as a normal user, therefore you should be sure
that the session timeout is not too big.

You can change the session timeout in the ``docker-compose.yaml`` file with:

.. code:: yaml

    services:
        geoportal:
            environment:
                # in second => One day
                AUTHTKT_TIMEOUT: 86400

How to build your token in your application
-------------------------------------------

The content of the token is a json-encoded text like this:

.. code::

    {
        u: <username>,
        p: <password>,
        t: <timestamp> // end of validity in seconds
    }

This content is then encrypted in AES with the provided key, and encoded in hexadecimal.
