# -*- coding: utf-8 -*-

import httplib2
import urllib
import sys
import logging

from pyramid.httpexceptions import (HTTPBadGateway, HTTPNotAcceptable,
                                    HTTPInternalServerError)
from pyramid.response import Response
from pyramid.view import view_config

from c2cgeoportal.lib.wfsparsing import is_get_feature, limit_featurecollection
from c2cgeoportal.lib.functionality import get_functionality

log = logging.getLogger(__name__)


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

        # In some application we want to display the features owned by a user
        # than we need his id.
        if not external:
            params['user_id'] = user.id

    # don't allows direct variable substitution
    for k in params.keys():
        if k[:2].capitalize() == 'S_':
            log.warning("Direct substitution not allowed (%s=%s)." %
                        (k, params[k]))
            del params[k]

    mss = get_functionality('mapserver_substitution',
                            request.registry.settings, request)
    if mss:
        for s in mss:
            index = s.find('=')
            if index > 0:
                attribute = 's_' + s[:index]
                value = s[index + 1:]
                if attribute in params:
                    params[attribute] += "," + value
                else:
                    params[attribute] = value
            else:
                log.warning("Mapserver Substitution '%s' does not "
                            "respect pattern: <attribute>=<value>" % s)

    # get method
    method = request.method

    # we want the browser to cache GetLegendGraphic requests, so
    # we need to know if the current request is a GetLegendGraphic
    # request
    is_glg = False

    if method == "GET":
        _params = dict(
            (k.lower(), unicode(v).lower()) for k, v in params.iteritems()
            )

        # For GET requests, params are added only if the REQUEST
        # parameter is actually provided.
        if 'request' not in _params:
            params = {}
        else:
            # WMS GetLegendGraphic request?
            is_glg = _params['service'] == u'wms' and \
                     _params['request'] == u'getlegendgraphic'

    # get query string
    params_encoded = {}
    for k, v in params.iteritems():
        params_encoded[k] = unicode(v).encode('utf-8')
    query_string = urllib.urlencode(params_encoded)

    # get URL
    _url = request.registry.settings['external_mapserv_url'] \
        if external \
        else request.registry.settings['mapserv_url']
    _url += '?' + query_string
    log.info("Querying mapserver proxy at URL: %s." % _url)

    # get body
    body = None
    if method in ("POST", "PUT"):
        body = request.body

    # forward request to target (without Host Header)
    http = httplib2.Http()
    h = dict(request.headers)
    h.pop("Host", h)
    try:
        resp, content = http.request(_url, method=method,
                                     body=body, headers=h)
    except:  # pragma: no cover
        log.error(
            "Error '%s' while getting the URL: %s." %
            (sys.exc_info()[0], _url))
        if method == "POST":
            log.error("--- With body ---")
            log.error(body)
        return HTTPBadGateway("See logs for details")  # pragma: no cover

    if resp.status != 200:
        log.error("\nError\n '%s'\n in response from URL:\n %s\n "
                  "with query:\n %s" %
                  (resp.reason, _url, body))  # pragma: no cover
        return HTTPInternalServerError(
            "See logs for details")  # pragma: no cover

    # check for allowed content types
    if "content-type" not in resp:
        return HTTPNotAcceptable()  # pragma: no cover

    if method == "POST" and is_get_feature(request.body):
        content = limit_featurecollection(content, limit=200)

    headers = {"Content-Type": resp["content-type"]}
    if is_glg:
        # 30mn expiration for GetLegendGraphic
        headers.update({"Cache-Control": "public, max-age=1800"})

    return Response(content, status=resp.status, headers=headers)
