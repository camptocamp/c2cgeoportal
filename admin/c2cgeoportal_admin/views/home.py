from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config


@view_config(route_name='home')
def home_view(request):
    return HTTPFound(request.route_url('layertree'))
