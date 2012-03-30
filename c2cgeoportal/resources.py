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


def defaultgroupsfinder(userid, request):
    # should be after the application initialisation
    from c2cgeoportal.models import DBSession, Role, User, AUTHORIZED_ROLE

    role = DBSession.query(Role).join(Role.users).filter(User.username == userid).one()

    if role and role.name == 'role_admin':
        return  [AUTHORIZED_ROLE]
    else:
        return []
