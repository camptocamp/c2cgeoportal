# -*- coding: utf-8 -*-

# Copyright (c) 2011-2014, Camptocamp SA
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

from pyramid.httpexceptions import HTTPBadGateway, HTTPNotAcceptable, \
    HTTPInternalServerError
from pyramid.response import Response
from pyramid.view import view_config

from c2cgeoportal.lib.caching import get_region, init_cache_control
from c2cgeoportal.lib.wfsparsing import is_get_feature, limit_featurecollection
from c2cgeoportal.lib.functionality import get_mapserver_substitution_params
from c2cgeoportal.lib.filter_capabilities import filter_capabilities

cache_region = get_region()
log = logging.getLogger(__name__)


class MapservProxy:

    def __init__(self, request):
        self.request = request
        self.settings = request.registry.settings.get('wfs', {})

    def _get_wfs_url(self):
        if 'mapserv_wfs_url' in self.request.registry.settings and \
                self.request.registry.settings['mapserv_wfs_url']:
            return self.request.registry.settings['mapserv_wfs_url']
        return self.request.registry.settings['mapserv_url']

    def _get_external_wfs_url(self):
        if 'external_mapserv_wfs_url' in self.request.registry.settings and \
                self.request.registry.settings['external_mapserv_wfs_url']:
            return self.request.registry.settings['external_mapserv_wfs_url']
        if 'external_mapserv_url' in self.request.registry.settings and \
                self.request.registry.settings['external_mapserv_url']:
            return self.request.registry.settings['external_mapserv_url']

    @view_config(route_name='mapserverproxy')
    def proxy(self):

        self.user = self.request.user
        self.external = bool(self.request.params.get("EXTERNAL", None))

        # params hold the parameters we're going to send to MapServer
        params = dict(self.request.params)

        # reset possible value of role_id and user_id
        if 'role_id' in params:  # pragma: no cover
            del params['role_id']
        if 'user_id' in params:  # pragma: no cover
            del params['user_id']

        self.lower_params = dict(
            (k.lower(), unicode(v).lower()) for k, v in params.iteritems()
        )

        if self.user is not None:
            # We have a user logged in. We need to set group_id and
            # possible layer_name in the params. We set layer_name
            # when either QUERY_PARAMS or LAYERS is set in the
            # WMS params, i.e. for GetMap and GetFeatureInfo
            # requests. For GetLegendGraphic requests we don't
            # send layer_name, but MapServer shouldn't use the DATA
            # string for GetLegendGraphic.

            params['role_id'] = self.user.parent_role.id if self.external else self.user.role.id

            # In some application we want to display the features owned by a user
            # than we need his id.
            if not self.external:
                params['user_id'] = self.user.id  # pragma: nocover

        # don't allows direct variable substitution
        for k in params.keys():
            if k[:2].capitalize() == 'S_':
                log.warning("Direct substitution not allowed (%s=%s)." %
                            (k, params[k]))
                del params[k]

        # add functionalities params
        params.update(get_mapserver_substitution_params(self.request))

        # get method
        method = self.request.method

        # we want the browser to cache GetLegendGraphic and
        # DescribeFeatureType requests
        use_cache = False
        public_cache = False

        if method == "GET":
            # For GET requests, params are added only if the self.request
            # parameter is actually provided.
            if 'request' not in self.lower_params:
                params = {}  # pragma: no cover
            else:
                use_cache = (
                    self.lower_params['request'] == u'getcapabilities'
                ) or (
                    (
                        'service' not in self.lower_params or
                        self.lower_params['service'] == u'wms'
                    ) and (
                        self.lower_params['request'] == u'getlegendgraphic'
                    )
                ) or (
                    (
                        'service' in self.lower_params and
                        self.lower_params['service'] == u'wfs'
                    ) and (
                        self.lower_params['request'] == u'describefeaturetype'
                    )
                )

                public_cache = self.lower_params['request'] == u'getlegendgraphic'

                # no user_id and role_id or cached queries
                if use_cache and 'user_id' in params:
                    del params['user_id']
                if use_cache and 'role_id' in params:
                    del params['role_id']

            if 'service' in self.lower_params and self.lower_params['service'] == u'wfs':
                _url = self._get_external_wfs_url() if self.external else self._get_wfs_url()
            else:
                _url = self.request.registry.settings['external_mapserv_url'] \
                    if self.external \
                    else self.request.registry.settings['mapserv_url']
        else:
            # POST means WFS
            _url = self._get_external_wfs_url() if self.external else self._get_wfs_url()

        role_id = None if self.user is None else \
            self.user.parent_role.id if self.external else self.user.role.id
        if use_cache:
            return self._proxy_cache(
                _url, params, public_cache, method, self.request.headers, role_id
            )
        else:
            return self._proxy(
                _url, params, use_cache, public_cache, method, self.request.body,
                self.request.headers, role_id
            )

    @cache_region.cache_on_arguments()
    def _proxy_cache(self, _url, params, public_cache, method, headers, role_id):
        return self._proxy(_url, params, True, public_cache, method, None, headers, role_id)

    def _proxy(self, _url, params, use_cache, public_cache, method, body, headers, role_id):
        # name of the JSON callback (value for the "callback" query string param
        # in the self.request). None if self.request has no "callback" param in the query
        # string
        callback = params.get('callback')

        # get query string
        params_encoded = {}
        for k, v in params.iteritems():
            if k == 'callback':
                continue
            params_encoded[k] = unicode(v).encode('utf-8')
        query_string = urllib.urlencode(params_encoded)

        parsed_url = urlparse(_url)
        _url = "%s://%s%s?%s%s%s" % (
            parsed_url.scheme, parsed_url.hostname,
            parsed_url.path, parsed_url.query,
            "&" if len(parsed_url.query) > 0 else "", query_string
        )
        log.info("Querying mapserver proxy at URL: %s." % _url)

        # forward self.request to target (without Host Header)
        http = httplib2.Http()
        headers = dict(headers)
        if urlparse(_url).hostname != 'localhost':  # pragma: no cover
            headers.pop('Host')
        # mapserver don't need the cookie, and sometimes it failed with it.
        if 'Cookie' in headers:  # pragma: no cover
            headers.pop('Cookie')
        try:
            resp, content = http.request(
                _url, method=method, body=body, headers=headers
            )
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

        if method == "POST" and is_get_feature(body) and \
                self.settings.get('enable_limit_featurecollection', True):
            content = limit_featurecollection(
                content,
                limit=self.settings.get('maxfeatures', 200)
            )

        if self.lower_params.get('request') == 'getcapabilities':
            content = filter_capabilities(
                content, role_id, self.lower_params.get('service') == 'wms',
                self.request.registry.settings['mapserv_url'],
                self.request.headers,
                self.request.registry.settings.get('proxies', None)
            )

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
        response = Response(content, status=resp.status, headers=headers)

        if use_cache:
            init_cache_control(
                self.request, "mapserver",
                self.request.user and not public_cache,
                response=response
            )
            response.cache_control.public = public_cache
        else:
            response.cache_control.no_cache = True

        return response
