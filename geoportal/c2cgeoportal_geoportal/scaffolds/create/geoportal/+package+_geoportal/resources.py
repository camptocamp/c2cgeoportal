# -*- coding: utf-8 -*-

import pyramid.request
from pyramid.security import ALL_PERMISSIONS, Allow


class Root:
    __acl__ = [(Allow, "role_admin", ALL_PERMISSIONS)]

    def __init__(self, request: pyramid.request.Request):
        self.request = request
