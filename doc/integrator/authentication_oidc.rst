OpenID Connect
~~~~~~~~~~~~~~

We can configure an OpenID connect service as an SSO (Single Sign-On) provider for our application. This allows users to log in to our application using their OpenID Connect credentials.

We use `OpenID Connect Discovery 1.0 <https://openid.net/specs/openid-connect-discovery-1_0.html>`_ with an Authorization Code Flow from `OpenID Connect Core 1.0 <https://openid.net/specs/openid-connect-core-1_0.html>`_, with PKCE (Proof Key for Code Exchange, `RFC 7636 <https://tools.ietf.org/html/rfc7636>`_).

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

If we want to use OpenID Connect as an authentication provider, we need to set the environment variable
``OPENID_CONNECT_ENABLED`` to ``true``, then we need to set the following configuration in our
``vars.yaml`` file:

.. code:: yaml

   vars:
     authentication:
       openid_connect:
         url: <the service URL>
         client_id: <the client application ID>

With that the user will be create in the database at the first login, and the access right will be set in the GeoMapFish database.
The user correspondence will be done on the email field.

~~~~~~~~~~~~~~~~~~~~~~
Authorization provider
~~~~~~~~~~~~~~~~~~~~~~

If we want to use OpenID Connect as an authorization provider, we need to set the environment variable
``OPENID_CONNECT_ENABLED`` to ``true``, then we need to set the following configuration in our
``vars.yaml`` file:

.. code:: yaml

   vars:
     authentication:
       openid_connect:
         url: <the service URL>
         client_id: <the client application ID>
         provide_roles: true
         user_info_fields:
           settings_role: settings_role
           roles: roles

With that the user will not be in the database only the roles will be set in the GeoMapFish database.

~~~~~~~~~~~~~
Other options
~~~~~~~~~~~~~

``client_secret``: The secret of the client.

``trusted_audiences``: The list of trusted audiences, if the audience provided by the id-token is not in
  this list, the ``ID token`` will be rejected.

``scopes``: The list of scopes to request, default is [``openid``, ``profile``, ``email``].

``query_user_info``: If ``true``, the OpenID Connect provider user info endpoint will be requested to
  provide the user info instead of using the information provided in the ``ID token``,
  default is ``false``.

``create_user``: If ``true``, a user will be create in the geomapfish database if not exists,
  default is ``false``.

``match_field``: The field to use to match the user in the database, can be ``username`` (default) or ``email``.

``update_fields``: The fields to update in the database, default is: ``[]``, allowed values are
  ``username``, ``display_name`` and ``email``.

``user_info_fields:`` The mapping between the user info fields and the user fields in the GeoMapFish database,
  the key is the GeoMpaFish user field and the value is the field of the user info provided by the
  OpenID Connect provider, default is:

  .. code:: yaml

     username: sub
     display_name: name
     email: email

~~~~~~~~~~~~~~~~~~~~
Example with Zitadel
~~~~~~~~~~~~~~~~~~~~

.. code:: yaml

   vars:
     authentication:
       openid_connect:
         url: https://sso.example.com
         client_id: '***'
         query_user_info: true
         create_user: true

~~~~~
Hooks
~~~~~

If you want to redefine the user creation process, you can use the hooks ``get_remember_from_user_info``
and ``get_user_from_remember``.

``get_remember_from_user_info``: This hook is called during the user is authentication.
The argument are the pyramid ``request``, the received ``user_info``, and the ``remember_object`` dictionary
to be filled and will be stored in the cookie.

``get_user_from_remember``: This hook is called during the user is certification.
The argument are the pyramid ``request``, the received ``remember_object``, and the ``update_create_user`` boolean.
The return value is the user object ``User`` or ``DynamicUsed``.
The ``update_create_user`` will be ``True`` only when we are in the callback endpoint.

Full signatures:

.. code:: python

    def get_remember_from_user_info(request: Request, user_info: Dict[str, Any], remember_object: OidcRememberObject) -> None:

    def get_user_from_remember(request: Request, remember_object: OidcRememberObject, update_create_user: bool) -> Union[User, DynamicUsed]:

Configure the hooks in the project initialization:

.. code:: python

    def includeme(config):
        config.add_request_method(get_remember_from_user_info, name="get_remember_from_user_info")
        config.add_request_method(get_user_from_remember, name="get_user_from_remember")

~~~~~~~~~~~~~~~~~
QGIS with Zitadel
~~~~~~~~~~~~~~~~~

In Zitadel you should have a PKCS application with the following settings:
Redirect URI: ``http://127.0.0.1:7070/``.

On QGIS:

* Add an ``Authentication``.
* Set a ``Name``.
* Set ``Authentication`` to ``OAuth2``.
* Set ``Grant flow`` to ``PKCE authentication code``.
* Set ``Request URL`` to ``<zitadel_base_url>/oauth/v2/authorize``.
* Set ``Token URL`` to ``<zitadel_base_url>/oauth/v2/token``.
* Set ``Client ID`` to ``<client_id>``.
* Set ``Scope`` to the ``openid profile email``.

~~~~~~~~~~~~~~
Implementation
~~~~~~~~~~~~~~

When we implement OpenID Connect, we have to possibilities:

* Implement it in the backend.
* Implement it in the frontend, and give a token to the backend that allows to be authenticated
  on an other service.

In c2cgeoportal we have implemented booth method.

The backend implementation is used by ngeo an the admin interface, where se store the user information
(including the access and refresh token) in an encrypted JSON as a cookie.
To use the backend implementation, the ``/oidc/login`` endpoint should be called with
an optional ``came_from`` parameter to redirect the user after the login.

The frontend implementation is used by application like QGIS desktop,
on every call the Bearer Token should be provided in the Authorization header,
we have to call the user info endpoint to get the user information.
