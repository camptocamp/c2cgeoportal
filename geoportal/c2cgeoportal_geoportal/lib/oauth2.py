# Copyright (c) 2021-2024, Camptocamp SA
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.

import logging
from datetime import datetime, timedelta
from typing import Any, TypedDict

import basicauth
import oauthlib.common
import oauthlib.oauth2
import pyramid.threadlocal
from pyramid.httpexceptions import HTTPBadRequest

import c2cgeoportal_commons
from c2cgeoportal_geoportal.lib.caching import get_region

_LOG = logging.getLogger(__name__)
_OBJECT_CACHE_REGION = get_region("obj")


class _Token(TypedDict):
    access_token: str
    refresh_token: str
    expires_in: int
    state: str | None


class RequestValidator(oauthlib.oauth2.RequestValidator):  # type: ignore
    """The oauth2 request validator implementation."""

    def __init__(self, authorization_expires_in: int) -> None:
        # in minutes
        self.authorization_expires_in = authorization_expires_in

    def authenticate_client(
        self,
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Authenticate client through means outside the OAuth 2 spec.

        Means of authentication is negotiated beforehand and may for example
        be `HTTP Basic Authentication Scheme`_ which utilizes the Authorization
        header.

        Headers may be accesses through request.headers and parameters found in
        both body and query can be obtained by direct attribute access, i.e.
        request.client_id for client_id in the URL query.

        Keyword Arguments:

            request: oauthlib.common.Request

        Returns: True or False

        Method is used by:
            - Authorization Code Grant
            - Resource Owner Password Credentials Grant (may be disabled)
            - Client Credentials Grant
            - Refresh Token Grant

        .. _`HTTP Basic Authentication Scheme`: https://tools.ietf.org/html/rfc1945#section-11.1
        """
        del args, kwargs

        _LOG.debug("authenticate_client => unimplemented")

        raise NotImplementedError("Not implemented, the method `authenticate_client_id` should be used.")

    def authenticate_client_id(
        self,
        client_id: str,
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Ensure client_id belong to a non-confidential client.

        A non-confidential client is one that is not required to authenticate
        through other means, such as using HTTP Basic.

        Note, while not strictly necessary it can often be very convenient
        to set request.client to the client object associated with the
        given client_id.

        Method is used by:
            - Authorization Code Grant
        """
        del args, kwargs

        _LOG.debug("authenticate_client_id %s", client_id)

        from c2cgeoportal_commons.models import DBSession, static  # pylint: disable=import-outside-toplevel

        assert DBSession is not None

        params = dict(request.decoded_body)

        if "client_secret" in params:
            client_secret = params["client_secret"]
        elif "Authorization" in request.headers:
            username, password = basicauth.decode(request.headers["Authorization"])
            assert client_id == username
            client_secret = password
        else:
            # Unable to get the client secret
            return False

        request.client = (
            DBSession.query(static.OAuth2Client)
            .filter(static.OAuth2Client.client_id == client_id)
            .filter(static.OAuth2Client.secret == client_secret)
            .one_or_none()
        )

        _LOG.debug("authenticate_client_id => %s", request.client is not None)
        return request.client is not None

    def client_authentication_required(
        self,
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Determine if client authentication is required for current request.

        According to the rfc6749, client authentication is required in the following cases:
            - Resource Owner Password Credentials Grant, when Client type is Confidential or when
              Client was issued client credentials or whenever Client provided client
              authentication, see `Section 4.3.2`_.
            - Authorization Code Grant, when Client type is Confidential or when Client was issued
              client credentials or whenever Client provided client authentication,
              see `Section 4.1.3`_.
            - Refresh Token Grant, when Client type is Confidential or when Client was issued
              client credentials or whenever Client provided client authentication, see
              `Section 6`_

        Keyword Arguments:

            request: oauthlib.common.Request

        Returns: True or False

        Method is used by:
            - Authorization Code Grant
            - Resource Owner Password Credentials Grant
            - Refresh Token Grant

        .. _`Section 4.3.2`: https://tools.ietf.org/html/rfc6749#section-4.3.2
        .. _`Section 4.1.3`: https://tools.ietf.org/html/rfc6749#section-4.1.3
        .. _`Section 6`: https://tools.ietf.org/html/rfc6749#section-6
        """
        del request, args, kwargs

        _LOG.debug("client_authentication_required => False")

        return False

    def confirm_redirect_uri(
        self,
        client_id: str,
        code: str,
        redirect_uri: str,
        client: "c2cgeoportal_commons.models.static.OAuth2Client",  # noqa: F821
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Ensure that the authorization process is correct.

        Ensure that the authorization process represented by this authorization code began with this
        ``redirect_uri``.

        If the client specifies a redirect_uri when obtaining code then that
        redirect URI must be bound to the code and verified equal in this
        method, according to RFC 6749 section 4.1.3.  Do not compare against
        the client's allowed redirect URIs, but against the URI used when the
        code was saved.

        Keyword Arguments:

            client_id: Unicode client identifier
            code: Unicode authorization_code.
            redirect_uri: Unicode absolute URI
            client: Client object set by you, see authenticate_client.
            request: The HTTP Request

        Returns: True or False

        Method is used by:
            - Authorization Code Grant (during token request)
        """
        del args, kwargs

        _LOG.debug("confirm_redirect_uri %s %s", client_id, redirect_uri)

        from c2cgeoportal_commons.models import DBSession, static  # pylint: disable=import-outside-toplevel

        assert DBSession is not None

        authorization_code = (
            DBSession.query(static.OAuth2AuthorizationCode)
            .join(static.OAuth2AuthorizationCode.client)
            .filter(static.OAuth2AuthorizationCode.code == code)
            .filter(static.OAuth2Client.client_id == client_id)
            .filter(static.OAuth2AuthorizationCode.redirect_uri == redirect_uri)
            .filter(static.OAuth2AuthorizationCode.expire_at > datetime.now())
            .one_or_none()
        )
        _LOG.debug("confirm_redirect_uri => %s", authorization_code is not None)
        return authorization_code is not None

    def get_default_redirect_uri(
        self,
        client_id: str,
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """
        Get the default redirect URI for the client.

        Keyword Arguments:

            client_id: Unicode client identifier
            request: The HTTP Request

        Returns: The default redirect URI for the client

        Method is used by:
            - Authorization Code Grant
            - Implicit Grant
        """
        del request, args, kwargs

        _LOG.debug("get_default_redirect_uri %s", client_id)

        raise NotImplementedError("Not implemented.")

    def get_default_scopes(
        self,
        client_id: str,
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> list[str]:
        """
        Get the default scopes for the client.

        Keyword Arguments:

            client_id: Unicode client identifier
            request: The HTTP Request

        Returns: List of default scopes

        Method is used by all core grant types:
            - Authorization Code Grant
            - Implicit Grant
            - Resource Owner Password Credentials Grant
            - Client Credentials grant
        """
        del request, args, kwargs

        _LOG.debug("get_default_scopes %s", client_id)

        return ["geomapfish"]

    def get_original_scopes(
        self,
        refresh_token: str,
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> list[str]:
        """
        Get the list of scopes associated with the refresh token.

        Keyword Arguments:

            refresh_token: Unicode refresh token
            request: The HTTP Request

        Returns: List of scopes.

        Method is used by:
            - Refresh token grant
        """
        del refresh_token, request, args, kwargs

        _LOG.debug("get_original_scopes")

        return []

    def introspect_token(
        self,
        token: str,
        token_type_hint: str,
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Introspect an access or refresh token.

        Called once the introspect request is validated. This method
        should verify the *token* and either return a dictionary with the list of claims associated, or `None`
        in case the token is unknown. Below the list of registered claims you should be interested in:

        - scope : space-separated list of scopes
        - client_id : client identifier
        - username : human-readable identifier for the resource owner
        - token_type : type of the token
        - exp : integer timestamp indicating when this token will expire
        - iat : integer timestamp indicating when this token was issued
        - nbf : integer timestamp indicating when it can be "not-before" used
        - sub : subject of the token - identifier of the resource owner
        - aud : list of string identifiers representing the intended audience
        - iss : string representing issuer of this token
        - jti : string identifier for the token
        Note that most of them are coming directly from JWT RFC. More details
        can be found in `Introspect Claims`_ or `_JWT Claims`_.
        The implementation can use *token_type_hint* to improve lookup
        efficiency, but must fallback to other types to be compliant with RFC.
        The dict of claims is added to request.token after this method.

        Keyword Arguments:

            token: The token string.
            token_type_hint: access_token or refresh_token.
            request: OAuthlib request.

        Method is used by:
            - Introspect Endpoint (all grants are compatible)

        .. _`Introspect Claims`: https://tools.ietf.org/html/rfc7662#section-2.2
        .. _`JWT Claims`: https://tools.ietf.org/html/rfc7519#section-4
        """
        del token, request, args, kwargs

        _LOG.debug("introspect_token %s", token_type_hint)

        raise NotImplementedError("Not implemented.")

    def invalidate_authorization_code(
        self,
        client_id: str,
        code: str,
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Invalidate an authorization code after use.

        Keyword Arguments:

            client_id: Unicode client identifier
            code: The authorization code grant (request.code).
            request: The HTTP Request

        Method is used by:
            - Authorization Code Grant
        """
        del args, kwargs

        _LOG.debug("invalidate_authorization_code %s", client_id)

        from c2cgeoportal_commons.models import DBSession, static  # pylint: disable=import-outside-toplevel

        assert DBSession is not None

        DBSession.delete(
            DBSession.query(static.OAuth2AuthorizationCode)
            .join(static.OAuth2AuthorizationCode.client)
            .filter(static.OAuth2AuthorizationCode.code == code)
            .filter(static.OAuth2Client.client_id == client_id)
            .filter(static.OAuth2AuthorizationCode.user_id == request.user.id)
            .one()
        )

    def is_within_original_scope(
        self,
        request_scopes: list[str],
        refresh_token: str,
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Check if requested scopes are within a scope of the refresh token.

        When access tokens are refreshed the scope of the new token
        needs to be within the scope of the original token. This is
        ensured by checking that all requested scopes strings are on
        the list returned by the get_original_scopes. If this check
        fails, is_within_original_scope is called. The method can be
        used in situations where returning all valid scopes from the
        get_original_scopes is not practical.

        Keyword Arguments:

            request_scopes: A list of scopes that were requested by client
            refresh_token: Unicode refresh_token
            request: The HTTP Request

        Method is used by:
            - Refresh token grant
        """
        del request, args, kwargs

        _LOG.debug("is_within_original_scope %s %s", request_scopes, refresh_token)

        return False

    def revoke_token(
        self,
        token: str,
        token_type_hint: str,
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Revoke an access or refresh token.

        Keyword Arguments:

            token: The token string.
            token_type_hint: access_token or refresh_token.
            request: The HTTP Request

        Method is used by:
            - Revocation Endpoint
        """
        del token, request, args, kwargs

        _LOG.debug("revoke_token %s", token_type_hint)

        raise NotImplementedError("Not implemented.")

    def rotate_refresh_token(self, request: oauthlib.common.Request) -> bool:
        """
        Determine whether to rotate the refresh token. Default, yes.

        When access tokens are refreshed the old refresh token can be kept
        or replaced with a new one (rotated). Return True to rotate and
        and False for keeping original.

        Keyword Arguments:

            request: oauthlib.common.Request

        Method is used by:
            - Refresh Token Grant
        """
        del request

        _LOG.debug("rotate_refresh_token")

        return True

    def save_authorization_code(
        self,
        client_id: str,
        code: dict[str, str],
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Persist the authorization_code.

        The code should at minimum be stored with:
            - the client_id (client_id)
            - the redirect URI used (request.redirect_uri)
            - a resource owner / user (request.user)
            - the authorized scopes (request.scopes)
            - the client state, if given (code.get('state'))

        The 'code' argument is actually a dictionary, containing at least a
        'code' key with the actual authorization code:

            {'code': '<secret>'}

        It may also have a 'state' key containing a nonce for the client, if it
        chose to send one.  That value should be saved and used in
        'validate_code'.

        Keyword Arguments:

            client_id: Unicode client identifier
            code: A dict of the authorization code grant and, optionally, state.
            request: The HTTP Request

        Method is used by:
            - Authorization Code Grant

        To support PKCE, you MUST associate the code with:

            Code Challenge (request.code_challenge) and
            Code Challenge Method (request.code_challenge_method)
        """
        del args, kwargs

        _LOG.debug("save_authorization_code %s", client_id)

        from c2cgeoportal_commons.models import DBSession, static  # pylint: disable=import-outside-toplevel

        assert DBSession is not None

        user = pyramid.threadlocal.get_current_request().user

        # Don't allows to have two authentications for the same user and the same client
        authorization_code = (
            DBSession.query(static.OAuth2AuthorizationCode)
            .filter(static.OAuth2AuthorizationCode.client_id == request.client.id)
            .filter(static.OAuth2AuthorizationCode.user_id == user.id)
            .one_or_none()
        )

        if authorization_code is not None:
            authorization_code.expire_at = datetime.now() + timedelta(minutes=self.authorization_expires_in)
        else:
            authorization_code = static.OAuth2AuthorizationCode()
            authorization_code.client_id = request.client.id
            authorization_code.user_id = user.id
            authorization_code.expire_at = datetime.now() + timedelta(minutes=self.authorization_expires_in)
            authorization_code.state = code.get("state")

        authorization_code.code = code["code"]
        authorization_code.redirect_uri = request.redirect_uri

        client = (
            DBSession.query(static.OAuth2Client)
            .filter(static.OAuth2Client.client_id == client_id)
            .one_or_none()
        )
        if client and client.state_required and not code.get("state"):
            raise HTTPBadRequest("Client is missing the state parameter.")

        if client and client.pkce_required:
            authorization_code.challenge = request.code_challenge
            authorization_code.challenge_method = request.code_challenge_method

        DBSession.add(authorization_code)

    def save_bearer_token(
        self,
        token: _Token,
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Persist the Bearer token.

        The Bearer token should at minimum be associated with:
            - a client and it's client_id, if available
            - a resource owner / user (request.user)
            - authorized scopes (request.scopes)
            - an expiration time
            - a refresh token, if issued

        The Bearer token dict may hold a number of items::

            {
                'token_type': 'Bearer',
                'access_token': '<secret>',
                'expires_in': 3600,
                'scope': 'string of space separated authorized scopes',
                'refresh_token': '<secret>',  # if issued
                'state': 'given_by_client',  # if supplied by client
            }

        Note that while "scope" is a string-separated list of authorized scopes,
        the original list is still available in request.scopes

        Keyword Arguments:

            client_id: Unicode client identifier
            token: A Bearer token dict
            request: The HTTP Request

        Returns: The default redirect URI for the client

        Method is used by all core grant types issuing Bearer tokens:
            - Authorization Code Grant
            - Implicit Grant
            - Resource Owner Password Credentials Grant (might not associate a client)
            - Client Credentials grant
        """
        del args, kwargs

        _LOG.debug("save_bearer_token")

        from c2cgeoportal_commons.models import DBSession, static  # pylint: disable=import-outside-toplevel

        assert DBSession is not None

        # Don't allows to have tow token for one user end one client
        bearer_token = (
            DBSession.query(static.OAuth2BearerToken)
            .filter(static.OAuth2BearerToken.client_id == request.client.id)
            .filter(static.OAuth2BearerToken.user_id == request.user.id)
            .one_or_none()
        )

        if bearer_token is None:
            bearer_token = static.OAuth2BearerToken()
            bearer_token.client_id = request.client.id
            bearer_token.user_id = request.user.id
            DBSession.add(bearer_token)

        bearer_token.access_token = token["access_token"]
        bearer_token.refresh_token = token["refresh_token"]
        bearer_token.expire_at = datetime.now() + timedelta(seconds=float(token["expires_in"]))
        bearer_token.state = token.get("state")

    def validate_bearer_token(
        self,
        token: str,
        scopes: list[str],
        request: oauthlib.common.Request,
    ) -> bool:
        """
        Ensure the Bearer token is valid and authorized access to scopes.

        Keyword Arguments:

            token: A string of random characters.
            scopes: A list of scopes associated with the protected resource.
            request: The HTTP Request

        A key to OAuth 2 security and restricting impact of leaked tokens is
        the short expiration time of tokens, *always ensure the token has not
        expired!*.

        Two different approaches to scope validation:

            1) all(scopes). The token must be authorized access to all scopes
                            associated with the resource. For example, the
                            token has access to ``read-only`` and ``images``,
                            thus the client can view images but not upload new.
                            Allows for fine grained access control through
                            combining various scopes.

            2) any(scopes). The token must be authorized access to one of the
                            scopes associated with the resource. For example,
                            token has access to ``read-only-images``.
                            Allows for fine grained, although arguably less
                            convenient, access control.

        A powerful way to use scopes would mimic UNIX ACLs and see a scope
        as a group with certain privileges. For a restful API these might
        map to HTTP verbs instead of read, write and execute.

        Note, the request.user attribute can be set to the resource owner
        associated with this token. Similarly the request.client and
        request.scopes attribute can be set to associated client object
        and authorized scopes. If you then use a decorator such as the
        one provided for django these attributes will be made available
        in all protected views as keyword arguments.

        Keyword Arguments:

            token: Unicode Bearer token
            scopes: List of scopes (defined by you)
            request: The HTTP Request

        Method is indirectly used by all core Bearer token issuing grant types:
            - Authorization Code Grant
            - Implicit Grant
            - Resource Owner Password Credentials Grant
            - Client Credentials Grant
        """

        _LOG.debug("validate_bearer_token %s", scopes)

        from c2cgeoportal_commons.models import DBSession, static  # pylint: disable=import-outside-toplevel

        assert DBSession is not None

        bearer_token = (
            DBSession.query(static.OAuth2BearerToken)
            .join(static.User)
            .filter(static.OAuth2BearerToken.access_token == token)
            .filter(static.OAuth2BearerToken.expire_at > datetime.now())
        ).one_or_none()

        if bearer_token is not None:
            request.user = bearer_token.user

        _LOG.debug("validate_bearer_token => %s", bearer_token is not None)
        return bearer_token is not None

    def validate_client_id(
        self,
        client_id: str,
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Ensure client_id belong to a valid and active client.

        Note, while not strictly necessary it can often be very convenient
        to set request.client to the client object associated with the
        given client_id.

        Keyword Arguments:

            client_id: Unicode client identifier
            request: oauthlib.common.Request

        Method is used by:
            - Authorization Code Grant
            - Implicit Grant
        """
        del args, kwargs

        _LOG.debug("validate_client_id")

        from c2cgeoportal_commons.models import DBSession, static  # pylint: disable=import-outside-toplevel

        assert DBSession is not None

        client = (
            DBSession.query(static.OAuth2Client)
            .filter(static.OAuth2Client.client_id == client_id)
            .one_or_none()
        )
        if client is not None:
            request.client = client
        return client is not None

    def validate_code(
        self,
        client_id: str,
        code: str,
        client: "c2cgeoportal_commons.models.static.OAuth2Client",  # noqa: F821
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Verify that the authorization_code is valid and assigned to the given client.

        Before returning true, set the following based on the information stored
        with the code in 'save_authorization_code':

            - request.user
            - request.state (if given)
            - request.scopes
        OBS! The request.user attribute should be set to the resource owner
        associated with this authorization code. Similarly request.scopes
        must also be set.

        Keyword Arguments:

            client_id: Unicode client identifier
            code: Unicode authorization code
            client: Client object set by you, see authenticate_client.
            request: The HTTP Request

        Method is used by:
            - Authorization Code Grant
        """
        del args, kwargs

        _LOG.debug("validate_code %s", client_id)

        from c2cgeoportal_commons.models import DBSession, static  # pylint: disable=import-outside-toplevel

        assert DBSession is not None

        authorization_code_query = (
            DBSession.query(static.OAuth2AuthorizationCode)
            .join(static.OAuth2AuthorizationCode.client)
            .filter(static.OAuth2AuthorizationCode.code == code)
            .filter(static.OAuth2AuthorizationCode.client_id == client.id)
            .filter(static.OAuth2AuthorizationCode.expire_at > datetime.now())
        )
        if client.state_required:
            authorization_code_query = authorization_code_query.filter(
                static.OAuth2AuthorizationCode.state == request.state
            )

        authorization_code = authorization_code_query.one_or_none()
        if authorization_code is None:
            _LOG.debug("validate_code => KO, no authorization_code found")
            return False

        if authorization_code.client.pkce_required:
            request.code_challenge = authorization_code.challenge
            request.code_challenge_method = authorization_code.challenge_method

        request.user = authorization_code.user
        _LOG.debug("validate_code => OK")
        return True

    def validate_grant_type(
        self,
        client_id: str,
        grant_type: str,
        client: "c2cgeoportal_commons.models.static.OAuth2Client",
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Ensure client is authorized to use the grant_type requested.

        Keyword Arguments:

            client_id: Unicode client identifier
            grant_type: Unicode grant type, i.e. authorization_code, password.
            client: Client object set by you, see authenticate_client.
            request: The HTTP Request

        Method is used by:
            - Authorization Code Grant
            - Resource Owner Password Credentials Grant
            - Client Credentials Grant
            - Refresh Token Grant
        """
        del client, request, args, kwargs

        _LOG.debug(
            "validate_grant_type %s %s => %s",
            client_id,
            grant_type,
            grant_type in ("authorization_code", "refresh_token"),
        )

        return grant_type in ("authorization_code", "refresh_token")

    def validate_redirect_uri(
        self,
        client_id: str,
        redirect_uri: str,
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Ensure client is authorized to redirect to the redirect_uri requested.

        All clients should register the absolute URIs of all URIs they intend
        to redirect to. The registration is outside of the scope of oauthlib.

        Keyword Arguments:

            client_id: Unicode client identifier
            redirect_uri: Unicode absolute URI
            request: The HTTP Request

        Method is used by:
            - Authorization Code Grant
            - Implicit Grant
        """
        del request, args, kwargs

        _LOG.debug("validate_redirect_uri %s %s", client_id, redirect_uri)

        from c2cgeoportal_commons.models import DBSession, static  # pylint: disable=import-outside-toplevel

        assert DBSession is not None

        client = (
            DBSession.query(static.OAuth2Client)
            .filter(static.OAuth2Client.client_id == client_id)
            .filter(static.OAuth2Client.redirect_uri == redirect_uri)
            .one_or_none()
        )
        _LOG.debug("validate_redirect_uri %s", client is not None)
        return client is not None

    def validate_refresh_token(
        self,
        refresh_token: str,
        client: "c2cgeoportal_commons.models.static.OAuth2Client",  # noqa: F821
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Ensure the Bearer token is valid and authorized access to scopes.

        OBS! The request.user attribute should be set to the resource owner
        associated with this refresh token.

        Keyword Arguments:

            refresh_token: Unicode refresh token
            client: Client object set by you, see authenticate_client.
            request: The HTTP Request

        Method is used by:
            - Authorization Code Grant (indirectly by issuing refresh tokens)
            - Resource Owner Password Credentials Grant (also indirectly)
            - Refresh Token Grant
        """
        del args, kwargs

        _LOG.debug("validate_refresh_token %s", client.client_id if client else None)

        from c2cgeoportal_commons.models import DBSession, static  # pylint: disable=import-outside-toplevel

        assert DBSession is not None

        bearer_token = (
            DBSession.query(static.OAuth2BearerToken)
            .filter(static.OAuth2BearerToken.refresh_token == refresh_token)
            .filter(static.OAuth2BearerToken.client_id == request.client.id)
            .one_or_none()
        )

        if bearer_token is not None:
            request.user = bearer_token.user

        return bearer_token is not None

    def validate_response_type(
        self,
        client_id: str,
        response_type: str,
        client: "c2cgeoportal_commons.models.static.OAuth2Client",
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Ensure client is authorized to use the response_type requested.

        Keyword Arguments:

            client_id: Unicode client identifier
            response_type: Unicode response type, i.e. code, token.
            client: Client object set by you, see authenticate_client.
            request: The HTTP Request

        Method is used by:
            - Authorization Code Grant
            - Implicit Grant
        """
        del client, request, args, kwargs

        _LOG.debug("validate_response_type %s %s", client_id, response_type)

        return response_type == "code"

    def validate_scopes(
        self,
        client_id: str,
        scopes: list[str],
        client: "c2cgeoportal_commons.models.static.OAuth2Client",
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Ensure the client is authorized access to requested scopes.

        Keyword Arguments:

            client_id: Unicode client identifier
            scopes: List of scopes (defined by you)
            client: Client object set by you, see authenticate_client.
            request: The HTTP Request

        Method is used by all core grant types:
            - Authorization Code Grant
            - Implicit Grant
            - Resource Owner Password Credentials Grant
            - Client Credentials Grant
        """
        del client, request, args, kwargs

        _LOG.debug("validate_scopes %s %s", client_id, scopes)

        return True

    def validate_user(
        self,
        username: str,
        password: str,
        client: "c2cgeoportal_commons.models.static.OAuth2Client",  # noqa: F821
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Ensure the username and password is valid.

        OBS! The validation should also set the user attribute of the request
        to a valid resource owner, i.e. request.user = username or similar. If
        not set you will be unable to associate a token with a user in the
        persistence method used (commonly, save_bearer_token).

        Keyword Arguments:

            username: Unicode username
            password: Unicode password
            client: Client object set by you, see authenticate_client.
            request: The HTTP Request

        Method is used by:
            - Resource Owner Password Credentials Grant
        """
        del password, client, request, args, kwargs

        _LOG.debug("validate_user %s", username)

        raise NotImplementedError("Not implemented.")

    def is_pkce_required(self, client_id: int, request: oauthlib.common.Request) -> bool:
        """
        Determine if current request requires PKCE.

        Default, False. This is called for both “authorization” and “token” requests.

        Override this method by return True to enable PKCE for everyone. You might want to enable it only
        for public clients. Note that PKCE can also be used in addition of a client authentication.

        OAuth 2.0 public clients utilizing the Authorization Code Grant are susceptible to
        the authorization code interception attack. This specification describes the attack as well as
        a technique to mitigate against the threat through the use of Proof Key for Code Exchange
        (PKCE, pronounced “pixy”). See RFC7636.

        Keyword Arguments:

            client_id: Client identifier.
            request (oauthlib.common.Request): OAuthlib request.


        Method is used by:

                Authorization Code Grant


        """
        from c2cgeoportal_commons.models import DBSession, static  # pylint: disable=import-outside-toplevel

        assert DBSession is not None

        client = (
            DBSession.query(static.OAuth2Client)
            .filter(static.OAuth2Client.client_id == client_id)
            .one_or_none()
        )

        return client and client.pkce_required  # type: ignore

    def get_code_challenge(self, code: str, request: oauthlib.common.Request) -> str | None:
        """
        Is called for every “token” requests.

        When the server issues the authorization code in the authorization response, it MUST associate the
        code_challenge and code_challenge_method values with the authorization code so it can be
        verified later.

        Typically, the code_challenge and code_challenge_method values are stored in encrypted form in
        the code itself but could alternatively be stored on the server associated with the code.
        The server MUST NOT include the code_challenge value in client requests in a form that other
        entities can extract.

        Return the code_challenge associated to the code. If None is returned, code is considered to not
        be associated to any challenges.

        Keyword Arguments:

            code: Authorization code.
            request: OAuthlib request.

        Return:

            code_challenge string

        Method is used by:

                Authorization Code Grant - when PKCE is active
        """
        from c2cgeoportal_commons.models import DBSession, static  # pylint: disable=import-outside-toplevel

        assert DBSession is not None

        _LOG.debug("get_code_challenge")

        authorization_code = (
            DBSession.query(static.OAuth2AuthorizationCode)
            .filter(static.OAuth2AuthorizationCode.code == code)
            .one_or_none()
        )
        if authorization_code:
            return authorization_code.challenge
        _LOG.debug("get_code_challenge authorization_code not found")
        return None

    def get_code_challenge_method(self, code: str, request: oauthlib.common.Request) -> str | None:
        """
        Is called during the “token” request processing.

        When a code_verifier and a code_challenge has been provided.

        See .get_code_challenge.

        Must return plain or S256. You can return a custom value if you have implemented your own
        AuthorizationCodeGrant class.

        Keyword Arguments:

            code: Authorization code.
            request: OAuthlib request.

        Return type:

            code_challenge_method string

        Method is used by:

                Authorization Code Grant - when PKCE is active
        """
        from c2cgeoportal_commons.models import DBSession, static  # pylint: disable=import-outside-toplevel

        assert DBSession is not None

        _LOG.debug("get_code_challenge_method")

        authorization_code = (
            DBSession.query(static.OAuth2AuthorizationCode)
            .filter(static.OAuth2AuthorizationCode.code == code)
            .one_or_none()
        )
        if authorization_code:
            return authorization_code.challenge_method
        _LOG.debug("get_code_challenge_method authorization_code not found")
        return None


def get_oauth_client(settings: dict[str, Any]) -> oauthlib.oauth2.WebApplicationServer:
    """Get the oauth2 client, with a cache."""
    authentication_settings = settings.get("authentication", {})
    return _get_oauth_client_cache(
        authentication_settings.get("oauth2_authorization_expire_minutes", 10),
        authentication_settings.get("oauth2_token_expire_minutes", 60),
    )


@_OBJECT_CACHE_REGION.cache_on_arguments()
def _get_oauth_client_cache(
    authorization_expire_minutes: int, token_expire_minutes: int
) -> oauthlib.oauth2.WebApplicationServer:
    """Get the oauth2 client, with a cache."""
    return oauthlib.oauth2.WebApplicationServer(
        RequestValidator(authorization_expires_in=authorization_expire_minutes),
        token_expires_in=token_expire_minutes * 60,
    )
