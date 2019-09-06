Authentication
--------------

The default policy
~~~~~~~~~~~~~~~~~~

By default, ``c2cgeoportal`` applications use an *auth ticket* authentication
policy (``AuthTktAuthenticationPolicy``). With this policy, the user name is
obtained from the "auth ticket" cookie set in the request.
The policy is created, and added to the application's configuration, in the
application's main ``__init__.py`` file.

In the file ``.env.sample``, you can configure the policy with the following variables:

.. code::

   AUTHTKT_TIMEOUT  # Default to one day.
   AUTHTKT_REISSUE_TIME  # Default to 2h30, recommended to be 10 times smaller than AUTHTKT_TIMEOUT.
   AUTHTKT_MAXAGE  # Default to one day, good to have the same value as AUTHTKT_TIMEOUT.
   AUTHTKT_SECRET  # Should be defined
   AUTHTKT_COOKIENAME
   AUTHTKT_HTTP_ONLY  # Default to true.
   AUTHTKT_SECURE  # Default to true.
   AUTHTKT_SAMESITE  # Default to Lax.

See also `the official documentation <https://docs.pylonsproject.org/projects/pyramid/en/latest/api/authentication.html#pyramid.authentication.AuthTktAuthenticationPolicy>`_.


Using another policy
~~~~~~~~~~~~~~~~~~~~

When using ``AuthTktAuthenticationPolicy``, an "auth ticket" cookie should be
set in the request for the user to be identified. In some applications, using
a custom identification mechanism may be needed instead, for instance to use SSO.
Our knowledge base has an example of how this can be achieved.

User validation
~~~~~~~~~~~~~~~

For logging in, ``c2cgeoportal`` validates the user credentials
(username/password) by reading the user information from the ``user`` database
table. If a c2cgeoportal application should work with another user information
source, like LDAP, a custom *client validation* mechanism can be set up.
Our knowledge base has an example of how this can be achieved.

Two factors authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~

GeoMapFish support TOTP (Time-Based One-Time Password Algorithm) two factors authentication
(`RFC 6238 <https://tools.ietf.org/html/rfc6238>`_).
To enable the two factors authentication you should set the following settings:

.. code:: yaml

   vars:
     authentication:
       two_factor: true

If a user lost his second authentication factor he can't ask for a new one, to reset it the administrator
should uncheck the 'The user changed his password' field on the user in the admin interface.
