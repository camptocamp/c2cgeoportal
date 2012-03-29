# -*- coding: utf-8 -*-

import httplib2
import urllib

from pyramid.httpexceptions import HTTPBadGateway, HTTPNotAcceptable
from pyramid.response import Response
from pyramid.view import view_config

from c2cgeoportal.models import DBSession, User
from c2cgeoportal.lib.wfsparsing import (is_get_feature,
                                         limit_featurecollection)

@view_config(route_name='mapserverproxy')
def proxy(request):

    user = request.user
    external = bool(request.params.get("EXTERNAL", None))

    # params hold the parameters we're going to send to MapServer
    params = dict(request.params)

    if user:

        # We have a user logged in. We need to set group_id and
        # possible layer_name in the params. We set layer_name
        # when either QUERY_PARAMS or LAYERS is set in the
        # WMS params, i.e. for GetMap and GetFeatureInfo
        # requests. For GetLegendGraphic requests we don't
        # send layer_name, but MapServer shouldn't use the DATA
        # string for GetLegendGraphic.

        params['role_id'] = user.parent_role.id if external else user.role.id

    # get query string
    query_string = urllib.urlencode(params)

    # get URL
    _url = request.registry.settings['external_mapserv.url'] if external \
           else request.registry.settings['mapserv.url']
    _url += '?' + query_string

    # get method
    method = request.method

    # get body
    body = None
    if method in ("POST", "PUT"):
        body = request.body

    # forward request to target (without Host Header)
    http = httplib2.Http()
    h = dict(request.headers)
    h.pop("Host", h)
    try:
        resp, content = http.request(_url, method=method, body=body, headers=h)
    except: # pragma: no cover
        return HTTPBadGateway() # pragma: no cover

    # check for allowed content types
    if not resp.has_key("content-type"):
        return HTTPNotAcceptable() # pragma: no cover

    if method == "POST" and is_get_feature(request.body):
        content = limit_featurecollection(content, limit=200)

    return Response(content, status=resp.status,
            headers={"Content-Type": resp["content-type"]})
