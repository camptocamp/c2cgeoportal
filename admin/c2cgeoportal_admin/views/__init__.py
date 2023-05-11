import pyramid.httpexceptions
import pyramid.request
from pyramid.view import view_config


class IsAdminPredicate:
    """
    A custom predicate that checks if the request is for the admin interface.
    """

    def __init__(self, val, info):
        del info

        self.val = val

    def text(self):
        return f"is_admin = {self.val}"

    phash = text

    def __call__(self, context, request):
        return request.path.startswith("/admin/") or request.path == "/admin"


@view_config(context=pyramid.httpexceptions.HTTPNotFound, is_admin=True, renderer="../templates/404.jinja2")
def _not_found_view(request=pyramid.request.Request):
    del request

    return {}
