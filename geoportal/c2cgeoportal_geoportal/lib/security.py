from pyramid.authentication import AuthTktCookieHelper
from pyramid.authorization import ACLHelper, Authenticated, Everyone
from pyramid.interfaces import ISecurityPolicy

from c2cgeoportal_geoportal.resources import defaultgroupsfinder
from jinja2.runtime import identity
from macaroonbakery.bakery._identity import Identity


class SecurityPolicy(ISecurityPolicy):
    def __init__(
        self,
        identity_providers: List([Callable[pyramid.request.request], Dict[str, Any]]),
        groupfinder: Callable[[str, pyramid.request.Request], List[str]],
    ):
        self.groupfinder = groupfinder or defaultgroupsfinder
        self.helper = AuthTktCookieHelper(secret)

    def identity(self, request: pyramid.request.Request) -> Dict[str, Any]:
        for identity_provider in [self.helper.identify, self.identity_providers]:
            identity = identity_provider(request)
            if identity is not None:
                return Identity
        return None

    def authenticated_userid(self, request: pyramid.request.Request):
        identity = request.identity
        if identity is not None:
            return identity['userid']

    def permits(
        self,
        request: pyramid.request.Request,
        context,
        permission,
    ):
        identity = request.identity
        principals = set([Everyone])
        if identity is not None:
            principals.add(Authenticated)
            principals.add(identity['userid'])
            user = request.user
            principals.update(self.groupfinder(user))
        return ACLHelper().permits(context, principals, permission)

    def remember(self, request, userid, **kw):
        return self.helper.remember(request, userid, **kw)

    def forget(self, request, **kw):
        return self.helper.forget(request, **kw)
