# -*- coding: utf-8 -*-

from pyramid.security import Allow, Authenticated, ALL_PERMISSIONS
from pyramid_formalchemy.resources import Models

class Root(object):
    def __init__(self, request):
        self.request = request

class FAModels(Models):
    __acl__ = [
        (Allow, Authenticated, ALL_PERMISSIONS),
    ]
