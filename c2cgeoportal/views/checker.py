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


from pyramid.view import view_config
from pyramid.response import Response

from httplib2 import Http
import simplejson


class Checker(object):

    status_int = 200

    def __init__(self, request):
        self.request = request
        self.settings = self.request.registry.settings['checker']

    def update_status_int(self, code):
        self.status_int = max(self.status_int, int(code))

    def make_response(self, msg):
        return Response(body=msg, status_int=self.status_int)

    def testurl(self, url):
        h = Http()
        resp, content = h.request(url)

        if resp['status'] != '200':
            self.update_status_int(resp['status'])
            return url + "<br/>" + content

        return 'OK'

    @view_config(route_name='checker_main')
    def main(self):
        _url = self.request.route_url('home')
        return self.make_response(self.testurl(_url))

    @view_config(route_name='checker_viewer')
    def viewer(self):
        _url = self.request.route_url('viewer')
        return self.make_response(self.testurl(_url))

    @view_config(route_name='checker_edit')
    def edit(self):
        _url = self.request.route_url('edit')
        return self.make_response(self.testurl(_url))

    @view_config(route_name='checker_edit_js')
    def edit_js(self):
        _url = self.request.route_url('edit.js')
        return self.make_response(self.testurl(_url))

    @view_config(route_name='checker_api')
    def api_js(self):
        _url = self.request.route_url('apijs')
        return self.make_response(self.testurl(_url))

    @view_config(route_name='checker_xapi')
    def xapi_js(self):
        _url = self.request.route_url('xapijs')
        return self.make_response(self.testurl(_url))

    @view_config(route_name='checker_printcapabilities')
    def printcapabilities(self):
        _url = self.request.route_url('printproxy_info')
        return self.make_response(self.testurl(_url))

    @view_config(route_name='checker_pdf')
    def pdf(self):
        return self.make_response(self._pdf())

    def _pdf(self):
        body = {
            'comment': 'Foobar',
            'title': 'Bouchon',
            'units': 'm',
            'srs': "EPSG:%i" % self.request.registry.settings['srid'],
            'dpi': 254,
            'layers': [],
            'layout': self.settings['print_template'],
            'pages': [{
                'center': [self.settings['print_center_lon'], self.settings['print_center_lat']],
                'col0': '',
                'rotation': 0,
                'scale': self.settings['print_scale'],
                'table': {
                    'columns': ["col0"],
                    'data': [{
                        'col0': ''
                    }]
                }
            }]
        }
        body = simplejson.dumps(body)

        _url = self.request.route_url('printproxy_create')
        h = Http()
        headers = {'Content-type': 'application/json;charset=utf-8'}
        resp, content = h.request(_url, 'POST', headers=headers, body=body)

        if resp['status'] != '200':
            self.update_status_int(resp['status'])
            return 'Failed creating PDF: ' + content

        json = simplejson.loads(content)
        _url = json['getURL']
        resp, content = h.request(_url)

        if resp['status'] != '200':
            self.update_status_int(resp['status'])
            return 'Failed retrieving PDF: ' + content

        return 'OK'

    @view_config(route_name='checker_fts')
    def fts(self):
        return self.make_response(self._fts())

    def _fts(self):
        _url = '%s?query=%s&limit=1' % (
            self.request.route_url('fulltextsearch'),
            self.settings['fulltextsearch']
        )
        h = Http()
        resp, content = h.request(_url)

        if resp['status'] != '200':
            self.update_status_int(resp['status'])
            return content

        result = simplejson.loads(content)

        if len(result['features']) == 0:
            self.update_status_int(400)
            return 'No result'

        return 'OK'

    @view_config(route_name='checker_wmscapabilities')
    def wmscapabilities(self):
        _url = self.request.route_url('mapserverproxy')
        _url += "?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetCapabilities"
        return self.make_response(self.testurl(_url))

    @view_config(route_name='checker_wfscapabilities')
    def wfscapabilities(self):
        _url = self.request.route_url('mapserverproxy')
        _url += "?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetCapabilities"
        return self.make_response(self.testurl(_url))
