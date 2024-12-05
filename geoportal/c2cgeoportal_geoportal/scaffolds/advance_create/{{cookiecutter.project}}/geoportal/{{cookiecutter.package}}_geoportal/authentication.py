from c2cgeoportal_geoportal.lib.authentication import create_authentication
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator


def includeme(config: Configurator) -> None:
    """Initialize the authentication( for a Pyramid app."""
    config.set_authorization_policy(ACLAuthorizationPolicy())
    config.set_authentication_policy(create_authentication(config.get_settings()))
