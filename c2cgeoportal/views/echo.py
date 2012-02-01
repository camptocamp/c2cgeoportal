import os.path
import re

from pyramid.httpexceptions import HTTPBadRequest
from pyramid.response import Response
from pyramid.view import view_config


@view_config(route_name='echo')
def echo(request):
    if request.method != 'POST':
        raise HTTPBadRequest()
    try:
        file = request.POST['file']
    except KeyError:
        raise HTTPBadRequest()
    response = Response()
    response.app_iter = file.file
    response.content_type = 'application/octet-stream'
    return response
