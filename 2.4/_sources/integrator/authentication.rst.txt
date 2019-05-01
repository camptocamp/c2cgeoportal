Authentication
--------------

The default policy
~~~~~~~~~~~~~~~~~~

By default, ``c2cgeoportal`` applications use an *auth ticket* authentication
policy (``AuthTktAuthenticationPolicy``). With this policy, the user name is
obtained from the "auth ticket" cookie set in the request.
The policy is created, and added to the application's configuration, in the
application's main ``__init__.py`` file.

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
