# -*- coding: utf-8 -*-

from pyramid.security import Allow, ALL_PERMISSIONS


class Root:
    __acl__ = [
        (Allow, 'role_admin', ALL_PERMISSIONS),
        ]

    def __init__(self, request):
        self.request = request
