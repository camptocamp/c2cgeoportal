# -*- coding: utf-8 -*-

from pyramid.security import Allow, Authenticated, ALL_PERMISSIONS
from pyramid_formalchemy.resources import Models


class Root(object):
    def __init__(self, request):
        self.request = request  # pragma: nocover


class FAModels(Models):
    __acl__ = [
        (Allow, Authenticated, ALL_PERMISSIONS),
    ]


def defaultgroupsfinder(username, request):
    """ The c2cgeoportal default group finder. To be used as the callback of
    the ``AuthTktAuthenticationPolicy`` or any callback-based authentication
    policy. """
    role = request.user.role
    return [role.name] if role else []
