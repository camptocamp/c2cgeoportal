from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config


@view_config(route_name='admin')
def admin(request):
    return HTTPFound(request.route_url('layertree', application='admin'))
