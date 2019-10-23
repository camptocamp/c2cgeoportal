# -*- coding: utf-8 -*-

from pyramid.security import ALL_PERMISSIONS, Allow


class Root:
    __acl__ = [(Allow, "role_admin", ALL_PERMISSIONS)]

    def __init__(self, request):
        self.request = request
