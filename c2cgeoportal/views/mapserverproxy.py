# -*- coding: utf-8 -*-

import httplib2
import urllib
import sys
import logging

from pyramid.httpexceptions import HTTPBadGateway, HTTPNotAcceptable
from pyramid.response import Response
from pyramid.view import view_config

from c2cgeoportal.lib.wfsparsing import is_get_feature, limit_featurecollection
from c2cgeoportal.lib.functionality import get_functionalities

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

    # don't allows direct variable substitution
    toRemove = []
    for p in params:
        if p[:2].capitalize() == 'S_':
            log.warning("Direct Substitution is not allowed (%s=%s)." \
                        % (p, params[p]))
            toRemove.append(p)
    for p in toRemove:
        del params[p]

    mss = get_functionalities('mapserver_substitution', \
            request.registry.settings, request)
    if (mss):
        for s in mss:
            index = s.find('=');
            if index > 0:
                attribute = 's_' + s[:index]
                value = s[index+1:]
                if (attribute in params):
                    params[attribute] += "," + value
                else:
                    params[attribute] = value
                log.warning(params[attribute])
            else:
                log.warning(("The Mapserver Substitution '%s' don't" \
                        + " respect the pattern: <attribute>=<value>") % s);

    # get query string
    query_string = urllib.urlencode(params)

    # get URL
    _url = request.registry.settings['external_mapserv.url'] if external \
           else request.registry.settings['mapserv.url']
    _url += '?' + query_string
    log.info("Querying mapserver proxy at URL: %s." % _url)

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
    except:  # pragma: no cover
        log.error("Error '%s' while getting the URL: %s." %
                (sys.exc_info()[0], _url))
        if method == "POST":
            log.error("--- With body ---")
            log.error(body)
        return HTTPBadGateway("See logs for details")  # pragma: no cover

    # check for allowed content types
    if "content-type" not in resp:
        return HTTPNotAcceptable()  # pragma: no cover

    if method == "POST" and is_get_feature(request.body):
        content = limit_featurecollection(content, limit=200)

    return Response(content, status=resp.status,
            headers={"Content-Type": resp["content-type"]})
