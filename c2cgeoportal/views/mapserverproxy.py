# -*- coding: utf-8 -*-

# Copyright (c) 2013, Camptocamp SA
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.


import httplib2
import urllib
import sys
import logging

from urlparse import urlparse

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

    # name of the JSON callback (value for the "callback" query string param
    # in the request). None if request has no "callback" param in the query
    # string
    callback = None

    if method == "GET":
        _params = dict(
            (k.lower(), unicode(v).lower()) for k, v in params.iteritems()
        )

        # For GET requests, params are added only if the REQUEST
        # parameter is actually provided.
        if 'request' not in _params:
            params = {}  # pragma: no cover
        else:
            # WMS GetLegendGraphic request?
            is_glg = ('service' not in _params or _params['service'] == u'wms') and \
                _params['request'] == u'getlegendgraphic'

        callback = params.get('callback')

    # get query string
    params_encoded = {}
    for k, v in params.iteritems():
        if k == 'callback':
            continue
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
    if urlparse(_url).hostname != 'localhost':
        h.pop('Host')
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

    content_type = None
    if callback:
        content_type = "application/javascript"
        # escape single quotes in the JavaScript string
        content = unicode(content.decode('utf8'))
        content = content.replace(u"'", ur"\'")
        content = u"%s('%s');" % (callback, u' '.join(content.splitlines()))
    else:
        content_type = resp["content-type"]

    headers = {"Content-Type": content_type}

    if is_glg:
        # 30min expiration for GetLegendGraphic
        headers.update({"Cache-Control": "public, max-age=1800"})

    return Response(content, status=resp.status, headers=headers)
