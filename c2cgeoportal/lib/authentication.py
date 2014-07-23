import binascii

from paste.httpheaders import AUTHORIZATION

from pyramid.authentication import AuthTktAuthenticationPolicy, \
    BasicAuthAuthenticationPolicy
from pyramid_multiauth import MultiAuthenticationPolicy

from c2cgeoportal.resources import defaultgroupsfinder


def _get_basicauth_credentials(request):
    authorization = AUTHORIZATION(request.environ)
    try:
        authmeth, auth = authorization.split(' ', 1)
    except ValueError:  # not enough values to unpack
        return None
    if authmeth.lower() == 'basic':
        try:
            auth = auth.strip().decode('base64')
        except binascii.Error:  # can't decode
            return None
        try:
            login, password = auth.split(':', 1)
        except ValueError:  # not enough values to unpack
            return None
        return {'login': login, 'password': password}

    return None


def create_authentication(settings):
    cookie_authentication_policy = AuthTktAuthenticationPolicy(
        settings.get('authtkt_secret'),
        callback=defaultgroupsfinder,
        cookie_name=settings.get('authtkt_cookie_name'),
        hashalg='sha512')
    basic_authentication_policy = BasicAuthAuthenticationPolicy(c2cgeoportal_check)
    policies = [cookie_authentication_policy, basic_authentication_policy]
    return MultiAuthenticationPolicy(policies)


def c2cgeoportal_check(credentials, request):
    if request.registry.validate_user(request, credentials['login'],
                                      credentials['password']):
        return []
    return None
