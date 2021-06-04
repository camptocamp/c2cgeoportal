# -*- coding: utf-8 -*-

# Copyright (c) 2021, Camptocamp SA
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
from typing import Any, Dict, List, Union

import oauthlib.common
import oauthlib.oauth2
import pyramid.threadlocal

from c2cgeoportal_geoportal.lib.caching import get_region

LOG = logging.getLogger(__name__)
OBJECT_CACHE_REGION = get_region("obj")


class RequestValidator(oauthlib.oauth2.RequestValidator):
    def __init__(self, authorization_expires_in):
        # in minutes
        self.authorization_expires_in = authorization_expires_in

    def authenticate_client(  # pylint: disable=no-self-use,useless-suppression
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

        :param request: oauthlib.common.Request
        :rtype: True or False

        Method is used by:
            - Authorization Code Grant
            - Resource Owner Password Credentials Grant (may be disabled)
            - Client Credentials Grant
            - Refresh Token Grant

        .. _`HTTP Basic Authentication Scheme`: http://tools.ietf.org/html/rfc1945#section-11.1
        """
        del args, kwargs

        LOG.debug("authenticate_client")

        from c2cgeoportal_commons.models import DBSession, static  # pylint: disable=import-outside-toplevel

        params = dict(request.decoded_body)

        request.client = (
            DBSession.query(static.OAuth2Client)
            .filter(static.OAuth2Client.client_id == params["client_id"])
            .one_or_none()
        )

        return request.client is not None

    def authenticate_client_id(  # pylint: disable=no-self-use,useless-suppression
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

        :param request: oauthlib.common.Request
        :rtype: True or False

        Method is used by:
            - Authorization Code Grant
        """
        del args, kwargs

        LOG.debug("authenticate_client_id %s", client_id)

        from c2cgeoportal_commons.models import DBSession, static  # pylint: disable=import-outside-toplevel

        params = dict(request.decoded_body)

        request.client = (
            DBSession.query(static.OAuth2Client)
            .filter(static.OAuth2Client.client_id == client_id)
            .filter(static.OAuth2Client.secret == params["client_secret"])
            .one_or_none()
        )

        return request.client is not None

    def client_authentication_required(  # pylint: disable=no-self-use,useless-suppression
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

        :param request: oauthlib.common.Request
        :rtype: True or False

        Method is used by:
            - Authorization Code Grant
            - Resource Owner Password Credentials Grant
            - Refresh Token Grant

        .. _`Section 4.3.2`: http://tools.ietf.org/html/rfc6749#section-4.3.2
        .. _`Section 4.1.3`: http://tools.ietf.org/html/rfc6749#section-4.1.3
        .. _`Section 6`: http://tools.ietf.org/html/rfc6749#section-6
        """
        del request, args, kwargs

        LOG.debug("client_authentication_required")

        return True

    def confirm_redirect_uri(  # pylint: disable=no-self-use,useless-suppression
        self,
        client_id: str,
        code: str,
        redirect_uri: str,
        client: "c2cgeoportal_commons.models.static.OAuth2Client",  # noqa: F821
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Ensure that the authorization process represented by this authorization
        code began with this 'redirect_uri'.

        If the client specifies a redirect_uri when obtaining code then that
        redirect URI must be bound to the code and verified equal in this
        method, according to RFC 6749 section 4.1.3.  Do not compare against
        the client's allowed redirect URIs, but against the URI used when the
        code was saved.

        :param client_id: Unicode client identifier
        :param code: Unicode authorization_code.
        :param redirect_uri: Unicode absolute URI
        :param client: Client object set by you, see authenticate_client.
        :param request: The HTTP Request (oauthlib.common.Request)
        :rtype: True or False

        Method is used by:
            - Authorization Code Grant (during token request)
        """
        del args, kwargs

        LOG.debug("confirm_redirect_uri %s %s", client_id, redirect_uri)

        from c2cgeoportal_commons.models import DBSession, static  # pylint: disable=import-outside-toplevel

        authorization_code = (
            DBSession.query(static.OAuth2AuthorizationCode)
            .join(static.OAuth2AuthorizationCode.client)
            .filter(static.OAuth2AuthorizationCode.code == code)
            .filter(static.OAuth2Client.client_id == client_id)
            .filter(static.OAuth2AuthorizationCode.redirect_uri == redirect_uri)
            .filter(static.OAuth2AuthorizationCode.expire_at > datetime.now())
            .one_or_none()
        )
        return authorization_code is not None

    def get_code_challenge_method(  # pylint: disable=no-self-use,useless-suppression
        self, code: str, request: oauthlib.common.Request
    ) -> None:
        """Is called during the "token" request processing, when a
        ``code_verifier`` and a ``code_challenge`` has been provided.
        See ``.get_code_challenge``.
        Must return ``plain`` or ``S256``. You can return a custom value if you have
        implemented your own ``AuthorizationCodeGrant`` class.
        :param code: Authorization code.
        :param request: OAuthlib request.
        :type request: oauthlib.common.Request
        :rtype: code_challenge_method string
        Method is used by:
            - Authorization Code Grant - when PKCE is active
        """
        del code, request

        LOG.debug("get_code_challenge_method")

        raise NotImplementedError("Not implemented.")

    def get_default_redirect_uri(  # pylint: disable=no-self-use,useless-suppression
        self,
        client_id: str,
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """
        Get the default redirect URI for the client.

        :param client_id: Unicode client identifier
        :param request: The HTTP Request (oauthlib.common.Request)
        :rtype: The default redirect URI for the client

        Method is used by:
            - Authorization Code Grant
            - Implicit Grant
        """
        del request, args, kwargs

        LOG.debug("get_default_redirect_uri %s", client_id)

        raise NotImplementedError("Not implemented.")

    def get_default_scopes(  # pylint: disable=no-self-use,useless-suppression
        self,
        client_id: str,
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> List[str]:
        """
        Get the default scopes for the client.

        :param client_id: Unicode client identifier
        :param request: The HTTP Request (oauthlib.common.Request)
        :rtype: List of default scopes

        Method is used by all core grant types:
            - Authorization Code Grant
            - Implicit Grant
            - Resource Owner Password Credentials Grant
            - Client Credentials grant
        """
        del request, args, kwargs

        LOG.debug("get_default_scopes %s", client_id)

        return ["geomapfish"]

    def get_original_scopes(  # pylint: disable=no-self-use,useless-suppression
        self,
        refresh_token: str,
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> List[str]:
        """
        Get the list of scopes associated with the refresh token.

        :param refresh_token: Unicode refresh token
        :param request: The HTTP Request (oauthlib.common.Request)
        :rtype: List of scopes.

        Method is used by:
            - Refresh token grant
        """
        del refresh_token, request, args, kwargs

        LOG.debug("get_original_scopes")

        return []

    def introspect_token(  # pylint: disable=no-self-use,useless-suppression
        self,
        token: str,
        token_type_hint: str,
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Introspect an access or refresh token.
        Called once the introspect request is validated. This method should
        verify the *token* and either return a dictionary with the list of
        claims associated, or `None` in case the token is unknown.
        Below the list of registered claims you should be interested in:
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
        :param token: The token string.
        :param token_type_hint: access_token or refresh_token.
        :param request: OAuthlib request.
        :type request: oauthlib.common.Request
        Method is used by:
            - Introspect Endpoint (all grants are compatible)
        .. _`Introspect Claims`: https://tools.ietf.org/html/rfc7662#section-2.2
        .. _`JWT Claims`: https://tools.ietf.org/html/rfc7519#section-4
        """
        del token, request, args, kwargs

        LOG.debug("introspect_token %s", token_type_hint)

        raise NotImplementedError("Not implemented.")

    def invalidate_authorization_code(  # pylint: disable=no-self-use,useless-suppression
        self,
        client_id: str,
        code: str,
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Invalidate an authorization code after use.

        :param client_id: Unicode client identifier
        :param code: The authorization code grant (request.code).
        :param request: The HTTP Request (oauthlib.common.Request)

        Method is used by:
            - Authorization Code Grant
        """
        del args, kwargs

        LOG.debug("invalidate_authorization_code %s", client_id)

        from c2cgeoportal_commons.models import DBSession, static  # pylint: disable=import-outside-toplevel

        DBSession.delete(
            DBSession.query(static.OAuth2AuthorizationCode)
            .join(static.OAuth2AuthorizationCode.client)
            .filter(static.OAuth2AuthorizationCode.code == code)
            .filter(static.OAuth2Client.client_id == client_id)
            .filter(static.OAuth2AuthorizationCode.user_id == request.user.id)
            .one()
        )

    def is_within_original_scope(  # pylint: disable=no-self-use,useless-suppression
        self,
        request_scopes: List[str],
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

        :param request_scopes: A list of scopes that were requested by client
        :param refresh_token: Unicode refresh_token
        :param request: The HTTP Request (oauthlib.common.Request)
        :rtype: True or False

        Method is used by:
            - Refresh token grant
        """
        del request, args, kwargs

        LOG.debug("is_within_original_scope %s %s", request_scopes, refresh_token)

        return False

    def revoke_token(  # pylint: disable=no-self-use,useless-suppression
        self,
        token: str,
        token_type_hint: str,
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Revoke an access or refresh token.

        :param token: The token string.
        :param token_type_hint: access_token or refresh_token.
        :param request: The HTTP Request (oauthlib.common.Request)

        Method is used by:
            - Revocation Endpoint
        """
        del token, request, args, kwargs

        LOG.debug("revoke_token %s", token_type_hint)

        raise NotImplementedError("Not implemented.")

    def rotate_refresh_token(  # pylint: disable=no-self-use,useless-suppression
        self, request: oauthlib.common.Request
    ) -> bool:
        """
        Determine whether to rotate the refresh token. Default, yes.

        When access tokens are refreshed the old refresh token can be kept
        or replaced with a new one (rotated). Return True to rotate and
        and False for keeping original.

        :param request: oauthlib.common.Request
        :rtype: True or False

        Method is used by:
            - Refresh Token Grant
        """
        del request

        LOG.debug("rotate_refresh_token")

        return True

    def save_authorization_code(  # pylint: disable=no-self-use,useless-suppression
        self,
        client_id: str,
        code: Dict[str, str],
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

            {'code': 'sdf345jsdf0934f'}

        It may also have a 'state' key containing a nonce for the client, if it
        chose to send one.  That value should be saved and used in
        'validate_code'.

        :param client_id: Unicode client identifier
        :param code: A dict of the authorization code grant and, optionally, state.
        :param request: The HTTP Request (oauthlib.common.Request)

        Method is used by:
            - Authorization Code Grant
        """
        del args, kwargs

        LOG.debug("save_authorization_code %s", client_id)

        from c2cgeoportal_commons.models import DBSession, static  # pylint: disable=import-outside-toplevel

        user = pyramid.threadlocal.get_current_request().user_

        # Don't allows to have two authentications for the same user and the same client
        authorization_code = (
            DBSession.query(static.OAuth2AuthorizationCode)
            .filter(static.OAuth2AuthorizationCode.client_id == request.client.id)
            .filter(static.OAuth2AuthorizationCode.user_id == user.id)
            .one_or_none()
        )

        if authorization_code is not None:
            authorization_code.code = code["code"]
            authorization_code.expire_at = datetime.now() + timedelta(minutes=self.authorization_expires_in)
            authorization_code.redirect_uri = request.redirect_uri
        else:
            authorization_code = static.OAuth2AuthorizationCode()
            authorization_code.client_id = request.client.id
            authorization_code.code = code["code"]
            authorization_code.user_id = user.id
            authorization_code.expire_at = datetime.now() + timedelta(minutes=self.authorization_expires_in)
            authorization_code.redirect_uri = request.redirect_uri

        DBSession.add(authorization_code)

    def save_bearer_token(  # pylint: disable=no-self-use,useless-suppression
        self,
        token: Dict[str, Union[str, int]],
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
                'access_token': 'askfjh234as9sd8',
                'expires_in': 3600,
                'scope': 'string of space separated authorized scopes',
                'refresh_token': '23sdf876234',  # if issued
                'state': 'given_by_client',  # if supplied by client
            }

        Note that while "scope" is a string-separated list of authorized scopes,
        the original list is still available in request.scopes

        :param client_id: Unicode client identifier
        :param token: A Bearer token dict
        :param request: The HTTP Request (oauthlib.common.Request)
        :rtype: The default redirect URI for the client

        Method is used by all core grant types issuing Bearer tokens:
            - Authorization Code Grant
            - Implicit Grant
            - Resource Owner Password Credentials Grant (might not associate a client)
            - Client Credentials grant
        """
        del args, kwargs

        LOG.debug("save_bearer_token")

        from c2cgeoportal_commons.models import DBSession, static  # pylint: disable=import-outside-toplevel

        # Don't allows to have tow token for one user end one client
        bearer_token = (
            DBSession.query(static.OAuth2BearerToken)
            .filter(static.OAuth2BearerToken.client_id == request.client.id)
            .filter(static.OAuth2BearerToken.user_id == request.user.id)
            .one_or_none()
        )

        if bearer_token is not None:
            bearer_token.access_token = token["access_token"]
            bearer_token.refresh_token = token["refresh_token"]
            bearer_token.expire_at = datetime.now() + timedelta(seconds=float(token["expires_in"]))
        else:
            bearer_token = static.OAuth2BearerToken()
            bearer_token.client_id = request.client.id
            bearer_token.user_id = request.user.id
            bearer_token.access_token = token["access_token"]
            bearer_token.refresh_token = token["refresh_token"]
            bearer_token.expire_at = datetime.now() + timedelta(seconds=float(token["expires_in"]))

            DBSession.add(bearer_token)

    def validate_bearer_token(  # pylint: disable=no-self-use,useless-suppression
        self,
        token: str,
        scopes: List[str],
        request: oauthlib.common.Request,
    ) -> bool:
        """
        Ensure the Bearer token is valid and authorized access to scopes.

        :param token: A string of random characters.
        :param scopes: A list of scopes associated with the protected resource.
        :param request: The HTTP Request (oauthlib.common.Request)

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

        :param token: Unicode Bearer token
        :param scopes: List of scopes (defined by you)
        :param request: The HTTP Request (oauthlib.common.Request)
        :rtype: True or False

        Method is indirectly used by all core Bearer token issuing grant types:
            - Authorization Code Grant
            - Implicit Grant
            - Resource Owner Password Credentials Grant
            - Client Credentials Grant
        """

        LOG.debug("validate_bearer_token %s", scopes)

        from c2cgeoportal_commons.models import DBSession, static  # pylint: disable=import-outside-toplevel

        bearer_token = (
            DBSession.query(static.OAuth2BearerToken)
            .filter(static.OAuth2BearerToken.access_token == token)
            .filter(static.OAuth2BearerToken.expire_at > datetime.now())
        ).one_or_none()

        if bearer_token is not None:
            request.user = bearer_token.user

        return bearer_token is not None

    def validate_client_id(  # pylint: disable=no-self-use,useless-suppression
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

        :param request: oauthlib.common.Request
        :rtype: True or False

        Method is used by:
            - Authorization Code Grant
            - Implicit Grant
        """
        del args, kwargs

        LOG.debug("validate_client_id")

        from c2cgeoportal_commons.models import DBSession, static  # pylint: disable=import-outside-toplevel

        client = (
            DBSession.query(static.OAuth2Client)
            .filter(static.OAuth2Client.client_id == client_id)
            .one_or_none()
        )
        if client is not None:
            request.client = client
        return client is not None

    def validate_code(  # pylint: disable=no-self-use,useless-suppression
        self,
        client_id: str,
        code: str,
        client: "c2cgeoportal_commons.models.static.OAuth2Client",  # noqa: F821
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Verify that the authorization_code is valid and assigned to the given
        client.

        Before returning true, set the following based on the information stored
        with the code in 'save_authorization_code':

            - request.user
            - request.state (if given)
            - request.scopes
        OBS! The request.user attribute should be set to the resource owner
        associated with this authorization code. Similarly request.scopes
        must also be set.

        :param client_id: Unicode client identifier
        :param code: Unicode authorization code
        :param client: Client object set by you, see authenticate_client.
        :param request: The HTTP Request (oauthlib.common.Request)
        :rtype: True or False

        Method is used by:
            - Authorization Code Grant
        """
        del args, kwargs

        LOG.debug("validate_code %s", client_id)

        from c2cgeoportal_commons.models import DBSession, static  # pylint: disable=import-outside-toplevel

        authorization_code = (
            DBSession.query(static.OAuth2AuthorizationCode)
            .join(static.OAuth2AuthorizationCode.client)
            .filter(static.OAuth2AuthorizationCode.code == code)
            .filter(static.OAuth2Client.client_id == client_id)
            .filter(static.OAuth2AuthorizationCode.expire_at > datetime.now())
            .one_or_none()
        )
        if authorization_code is not None:
            request.user = authorization_code.user
        return authorization_code is not None

    def validate_grant_type(  # pylint: disable=no-self-use,useless-suppression
        self,
        client_id: str,
        grant_type: str,
        client,
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Ensure client is authorized to use the grant_type requested.

        :param client_id: Unicode client identifier
        :param grant_type: Unicode grant type, i.e. authorization_code, password.
        :param client: Client object set by you, see authenticate_client.
        :param request: The HTTP Request (oauthlib.common.Request)
        :rtype: True or False

        Method is used by:
            - Authorization Code Grant
            - Resource Owner Password Credentials Grant
            - Client Credentials Grant
            - Refresh Token Grant
        """
        del request, args, kwargs

        LOG.debug("validate_grant_type %s %s", client_id, grant_type)

        return grant_type in ("authorization_code", "refresh_token")

    def validate_redirect_uri(  # pylint: disable=no-self-use,useless-suppression
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

        :param client_id: Unicode client identifier
        :param redirect_uri: Unicode absolute URI
        :param request: The HTTP Request (oauthlib.common.Request)
        :rtype: True or False

        Method is used by:
            - Authorization Code Grant
            - Implicit Grant
        """
        del request, args, kwargs

        LOG.debug("validate_redirect_uri %s %s", client_id, redirect_uri)

        from c2cgeoportal_commons.models import DBSession, static  # pylint: disable=import-outside-toplevel

        client = (
            DBSession.query(static.OAuth2Client)
            .filter(static.OAuth2Client.client_id == client_id)
            .filter(static.OAuth2Client.redirect_uri == redirect_uri)
            .one_or_none()
        )
        LOG.debug("validate_redirect_uri %s", client is not None)
        return client is not None

    def validate_refresh_token(  # pylint: disable=no-self-use,useless-suppression
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

        :param refresh_token: Unicode refresh token
        :param client: Client object set by you, see authenticate_client.
        :param request: The HTTP Request (oauthlib.common.Request)
        :rtype: True or False

        Method is used by:
            - Authorization Code Grant (indirectly by issuing refresh tokens)
            - Resource Owner Password Credentials Grant (also indirectly)
            - Refresh Token Grant
        """
        del args, kwargs

        LOG.debug("validate_refresh_token %s", client.client_id if client else None)

        from c2cgeoportal_commons.models import DBSession, static  # pylint: disable=import-outside-toplevel

        bearer_token = (
            DBSession.query(static.OAuth2BearerToken)
            .filter(static.OAuth2BearerToken.refresh_token == refresh_token)
            .filter(static.OAuth2BearerToken.client_id == request.client.id)
            .filter(static.OAuth2BearerToken.expire_at > datetime.now())
            .one_or_none()
        )

        if bearer_token is not None:
            request.user = bearer_token.user

        return bearer_token is not None

    def validate_response_type(  # pylint: disable=no-self-use,useless-suppression
        self,
        client_id: str,
        response_type: str,
        client,
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Ensure client is authorized to use the response_type requested.

        :param client_id: Unicode client identifier
        :param response_type: Unicode response type, i.e. code, token.
        :param client: Client object set by you, see authenticate_client.
        :param request: The HTTP Request (oauthlib.common.Request)
        :rtype: True or False

        Method is used by:
            - Authorization Code Grant
            - Implicit Grant
        """
        del request, args, kwargs

        LOG.debug("validate_response_type %s %s", client_id, response_type)

        return response_type == "code"

    def validate_scopes(  # pylint: disable=no-self-use,useless-suppression
        self,
        client_id: str,
        scopes: List[str],
        client,
        request: oauthlib.common.Request,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Ensure the client is authorized access to requested scopes.

        :param client_id: Unicode client identifier
        :param scopes: List of scopes (defined by you)
        :param client: Client object set by you, see authenticate_client.
        :param request: The HTTP Request (oauthlib.common.Request)
        :rtype: True or False

        Method is used by all core grant types:
            - Authorization Code Grant
            - Implicit Grant
            - Resource Owner Password Credentials Grant
            - Client Credentials Grant
        """
        del request, args, kwargs

        LOG.debug("validate_scopes %s %s", client_id, scopes)

        return True

    def validate_user(  # pylint: disable=no-self-use,useless-suppression
        self,
        username,
        password,
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

        :param username: Unicode username
        :param password: Unicode password
        :param client: Client object set by you, see authenticate_client.
        :param request: The HTTP Request (oauthlib.common.Request)
        :rtype: True or False

        Method is used by:
            - Resource Owner Password Credentials Grant
        """
        del password, client, request, args, kwargs

        LOG.debug("validate_user %s", username)

        raise NotImplementedError("Not implemented.")


@OBJECT_CACHE_REGION.cache_on_arguments()
def get_oauth_client(settings):
    authentication_settings = settings.get("authentication", {})
    return oauthlib.oauth2.WebApplicationServer(
        RequestValidator(
            authorization_expires_in=authentication_settings.get("oauth2_authorization_expire_minutes", 10)
        ),
        token_expires_in=authentication_settings.get("oauth2_token_expire_minutes", 60) * 60,
    )
