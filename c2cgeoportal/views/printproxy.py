# -*- coding: utf-8 -*-

# Copyright (c) 2011-2015, Camptocamp SA
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
import logging

from urlparse import urlparse
import simplejson as json
from simplejson.decoder import JSONDecodeError

from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPBadGateway

from c2cgeoportal.lib import caching
from c2cgeoportal.lib.functionality import get_functionality

log = logging.getLogger(__name__)
cache_region = caching.get_region()


class Printproxy(object):  # pragma: no cover

    def __init__(self, request):
        self.request = request
        self.config = self.request.registry.settings

    @view_config(route_name='printproxy_info')
    def info(self):
        """ Get print capabilities. """

        templates = get_functionality(
            'print_template', self.config, self.request)

        # get query string
        params = dict(self.request.params)
        query_string = urllib.urlencode(params)

        return self._info(templates, query_string)

    @cache_region.cache_on_arguments()
    def _info(self, templates, query_string):
        # get URL
        _url = self.config['print_url'] + 'info.json' + '?' + query_string
        log.info("Get print capabilities from %s." % _url)

        # forward request to target (without Host Header)
        http = httplib2.Http()
        h = dict(self.request.headers)
        if urlparse(_url).hostname != 'localhost':
            h.pop('Host')
        try:
            resp, content = http.request(_url, method='GET', headers=h)
        except:
            return HTTPBadGateway()

        try:
            capabilities = json.loads(content)
        except JSONDecodeError:
            # log and raise
            log.error("Unable to parse capabilities.")
            log.info(content)
            return content

        capabilities['layouts'] = list(
            layout for layout in capabilities['layouts'] if
            layout['name'] in templates)

        headers = dict(resp)
        if 'content-length' in headers:
            del headers['content-length']
        if 'transfer-encoding' in headers:
            del headers['transfer-encoding']

        response = Response(
            json.dumps(capabilities, separators=(',', ':')),
            status=resp.status, headers=headers,
        )
        response.cache_control.max_age = \
            self.request.registry.settings["default_max_age"]
        return response

    @view_config(route_name='printproxy_create')
    def create(self):
        """ Create PDF. """

        # get query string
        params = dict(self.request.params)
        query_string = urllib.urlencode(params)

        # get URL
        _url = self.config['print_url'] + 'create.json' + '?' + query_string
        log.info("Send print query to %s." % _url)

        content_length = int(self.request.environ['CONTENT_LENGTH'])
        body = self.request.environ['wsgi.input'].read(content_length)

        # forward request to target (without Host Header)
        http = httplib2.Http()
        h = dict(self.request.headers)
        if urlparse(_url).hostname != 'localhost':
            h.pop('Host')
        h['Content-Length'] = str(len(body))
        h["Cache-Control"] = "no-cache"

        try:
            resp, content = http.request(
                _url, method='POST', body=body, headers=h
            )
        except:
            return HTTPBadGateway()

        return Response(
            content, status=resp.status, headers=dict(resp),
            cache_control="no-cache"
        )

    @view_config(route_name='printproxy_get')
    def get(self):
        """ Get created PDF. """

        file = self.request.matchdict.get('file')

        # get URL
        _url = self.config['print_url'] + file + '.printout'
        log.info("Get print document from %s." % _url)

        # forward request to target (without Host Header)
        http = httplib2.Http()
        h = dict(self.request.headers)
        if urlparse(_url).hostname != 'localhost':
            h.pop('Host')

        h["Cache-Control"] = "no-cache"

        try:
            resp, content = http.request(_url, method='GET', headers=h)
        except:
            return HTTPBadGateway()

        headers = {}
        if 'content-type' in resp:
            headers['content-type'] = resp['content-type']
        if 'content-disposition' in resp:
            headers['content-disposition'] = resp['content-disposition']
        # Pragma and Cache-Control headers because of ie 8 bug:
        # http://support.microsoft.com/default.aspx?scid=KB;EN-US;q316431
        # del response.headers['Pragma']
        # del response.headers['Cache-Control']
        return Response(
            content, status=resp.status, headers=headers
        )
