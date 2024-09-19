OpenID Connect
~~~~~~~~~~~~~~

We can configure an OpenID connect service as an SSO (Single Sign-On) provider for our application. This allows users to log in to our application using their OpenID Connect credentials.

We use [OpenID Connect Discovery 1.0](https://openid.net/specs/openid-connect-discovery-1_0.html) with an Authorization Code Flow from [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html), with PKCE (Proof Key for Code Exchange, RFC 7636).

.. mermaid::

    sequenceDiagram
        actor User
        participant Browser
        participant Geoportal
        participant IAM
        Geoportal->>IAM: discovery endpoint

        User->>+Browser: Login
        Browser->>+Geoportal: Login
        Geoportal->>-Browser: redirect
        Browser->>+IAM: authorization endpoint
        IAM->>-Browser: redirect
        Browser->>+Geoportal: callback endpoint
        Geoportal->>IAM: token endpoint
        opt on using user info instead of jwt token
        Geoportal->>IAM: userinfo endpoint
        end
        Geoportal->>-Browser: authentication data in cookie
        Browser->>-User: Reload

        Browser->>+Geoportal: any auth endpoint
        opt on token expiry
        Geoportal->>IAM: refresh token endpoint
        end
        Geoportal->>-Browser: response

~~~~~~~~~~~~~~~~~~~~~~~
Authentication provider
~~~~~~~~~~~~~~~~~~~~~~~

If we want to use OpenID Connect as an authentication provider, we need to set the following configuration in our ``vars.yaml`` file:

.. code:: yaml

   vars:
     authentication:
       openid_connect:
         enabled: true
         url: <the service URL>
         client_id: <the client application ID>
         user_info_fields:
           username: sub  # Default value
           display_name: name  # Default value
           email: email  # Default value

With that the user will be create in the database at the first login, and the access right will be set in the GeoMapFish database.
The user correspondence will be done on the email field.

~~~~~~~~~~~~~~~~~~~~~~
Authorization provider
~~~~~~~~~~~~~~~~~~~~~~

If we want to use OpenID Connect as an authorization provider, we need to set the following configuration in our ``vars.yaml`` file:

.. code:: yaml

   vars:
     authentication:
       openid_connect:
         enabled: true
         url: <the service URL>
         client_id: <the client application ID>
         provide_roles: true
         user_info_fields:
           username: name  # Default value
           email: email # Default value
           settings_role: settings_role
           roles: roles

With that the user will not be in the database only the roles will be set in the GeoMapFish database.

~~~~~~~~~~~~~
Other options
~~~~~~~~~~~~~

``client_secret``: The secret of the client.

``trusted_audiences``: The list of trusted audiences, if the token audience is not in this list, the token will be rejected.

``scopes``: The list of scopes to request, default is [``openid``, ``profile``, ``email``].

``query_user_info``: If ``true``, the user info will be requested instead if using the ``id_token``, default is false.

~~~~~
Hooks
~~~~~

If you want to redefine the user creation process, you can use the hooks ``get_remember_from_user_info``
and ``get_user_from_remember``.

``get_remember_from_user_info``: This hook is called during the user is authentication.
The argument are the pyramid ``request``, the received ``user_info``, and the ``remember_object`` dictionary
to be filled and will be stored in the cookie.

``get_user_from_remember``: This hook is called during the user is certification.
The argument are the pyramid ``request``, the received ``remember_object``, and the ``create_user`` boolean.
The return value is the user object ``User`` or ``DynamicUsed``.

Full signatures:

.. code:: python

    def get_remember_from_user_info(request: Request, user_info: Dict[str, Any], remember_object: OidcRememberObject) -> None:

    def get_user_from_remember(request: Request, remember_object: OidcRememberObject, create_user: bool) -> Union[User, DynamicUsed]:

Configure the hooks in the project initialization:

.. code:: python

    def includeme(config):
        config.add_request_method(get_remember_from_user_info, name="get_remember_from_user_info")
        config.add_request_method(get_user_from_remember, name="get_user_from_remember")
