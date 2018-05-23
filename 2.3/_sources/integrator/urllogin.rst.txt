.. _integrator_urllogin:

URL login
=========

We are able to share a permalink of the application to access to protected data.

First you should configure it in the vars file like it:

.. code:: yaml

    urllogin:
        aes_key: foobarfoobar1234

The AES key must be either 16, 24, or 32 bytes long.

To do that you should use the urllogin command: ``./docker-run urllogin --help``.

It generate a token like: ``auth=148b60cc...`` that you can add it in the query string of
the permalink.

When the use use this link he will be connected as a normal user, then you should be sure
that the session timeout is not too big.

You can change it in the vars file with:

.. code:: yaml

    authtkt:
        # in second => One day
        timeout: 86400

How to build your token in your application?
---------------------------------------------

The token is simply a json like this:

.. code:: json

    {
        u: <username>,
        p: <password>,
        t: <timestamp> // end of validity in second
    }

Witch is encrypted in AES with the provided key, and encoded in hexadecimal.
