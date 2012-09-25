# -*- coding: utf-8 -*-

from pyramid.httpexceptions import HTTPBadRequest
from pyramid.response import Response
from pyramid.view import view_config


@view_config(route_name='csvecho')
def echo(request):
    if request.method != 'POST':
        return HTTPBadRequest('Wrong method')

    csv = request.params.get('csv', None)
    if csv is None:
        return HTTPBadRequest('csv parameter is required')
    name = request.params.get('name', 'export')
    return Response(csv, headers={
        'Content-Type': 'text/csv; charset=iso-8859-1',
        'Content-Disposition': 'attachment; filename="%s.csv"' %
        name.encode('iso-8859-1')
    })
