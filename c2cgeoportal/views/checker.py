from pyramid.view import view_config
from pyramid.response import Response

from httplib2 import Http
import simplejson

class Checker(object):

    status_int = 200

    def __init__(self, request):
        self.request = request

    def update_status_int(self, code):
        self.status_int = max(self.status_int, int(code))
    
    def make_response(self, msg):
        return Response(body=msg, status_int=self.status_int)

    # Method called by the sysadmins to make sure that our app work well.
    # Then this name must not change.
    @view_config(route_name='checker_summary')
    def summary(self): 
        body = "<p>Main page: %s</p>\n" % (self._main()) + \
               "<p>API loader: %s</p>\n" % (self._apiloader()) + \
               "<p>Print capabilities: %s</p>\n" % (self._printcapabilities()) + \
               "<p>Print PDF: %s</p>\n" % (self._pdf()) + \
               "<p>FullTextSearch: %s</p>\n" % (self._fts()) + \
               "<p>WMS capabilities: %s</p>\n" % (self._wmscapabilities()) + \
               "<p>WFS capabilities: %s</p>" % (self._wfscapabilities())
        return Response(body=body, status_int=self.status_int)

    def testurl(self, url):
        h = Http()
        resp, content = h.request(url)
        
        if resp['status'] != '200':
            self.update_status_int(resp['status'])
            return url + "<br/>" + content

        return 'OK'
       
    @view_config(route_name='checker_main')
    def main(self):
        return self.make_response(self._main())

    def _main(self):
        _url = self.request.route_url('home')
        return self.testurl(_url)

    @view_config(route_name='checker_apiloader')
    def apiloader(self):
        return self.make_response(self._apiloader())

    def _apiloader(self):
        _url = self.request.route_url('apiloader')
        return self.testurl(_url)

    @view_config(route_name='checker_printcapabilities')
    def printcapabilities(self):
        return self.make_response(self._printcapabilities())

    def _printcapabilities(self):
        _url = self.request.route_url('printproxy_info')
        return self.testurl(_url)

    @view_config(route_name='checker_pdf')
    def pdf(self):
        return self.make_response(self._pdf())

    def _pdf(self):
        body = {
            'comment': 'Foobar',
            'title': 'Bouchon',
            'units': 'm',
            'srs': "EPSG:21781",
            'dpi': 254,
            'layers': [],
            'layout': "1 Wohlen A4 portrait",
            'pages': [{
                'center': [663000, 245000],
                'col0': '',
                'rotation': 0,
                'scale': 10000,
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
        _url = self.request.route_url('fulltextsearch') + '?query=4030&limit=20'
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
        return self.make_response(self._wmscapabilities())

    def _wmscapabilities(self):
        _url = self.request.route_url('mapserverproxy')
        _url += "?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetCapabilities"
        return self.testurl(_url)

    @view_config(route_name='checker_wfscapabilities')
    def wfscapabilities(self):
        return self.make_response(self._wfscapabilities())

    def _wfscapabilities(self):
        _url = self.request.route_url('mapserverproxy')
        _url += "?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetCapabilities"
        return self.testurl(_url)
