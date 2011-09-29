import httplib2
import urllib

import simplejson as json
from simplejson.decoder import JSONDecodeError

from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPBadGateway
from pyramid.security import authenticated_userid

from c2cgeoportal.models import DBSession, User
from c2cgeoportal.lib.functionality import get_functionalities

class Printproxy(object):

    def __init__(self, request):
        self.request = request
        self.config = self.request.registry.settings

    @view_config(route_name='printproxy_info')
    def info(self):
        """ Get print capabilities. """

        templates = get_functionalities('print_template', \
                self.config, self.request)

        # get query string
        params = dict(self.request.params)
        query_string = urllib.urlencode(params)

        # get URL
        _url = self.config['print.url'] + 'info.json' + '?' + query_string

        # forward request to target (without Host Header)
        http = httplib2.Http()
        h = dict(self.request.headers)
        h.pop("Host", h) # not sure this is needed TODO
        try:
            resp, content = http.request(_url, method='GET', headers=h)
        except:
            return HTTPBadGateway()

        try:
            capabilities = json.loads(content)
        except JSONDecodeError:
            #raise
            return content

        capabilities['layouts'] = list(
                layout for layout in capabilities['layouts'] if
                layout['name'] in templates)

        headers = dict(resp)
        headers["Expires"] = "-1"
        headers["Pragma"] = "no-cache"
        headers["CacheControl"] = "no-cache"
        return Response(json.dumps(capabilities, separators=(',',':')),
                        status=resp.status, headers=headers)

    @view_config(route_name='printproxy_create')
    def create(self):
        """ Create PDF. """

        # get query string
        params = dict(self.request.params)
        query_string = urllib.urlencode(params)

        # get URL
        _url = self.config['print.url'] + 'create.json' + '?' + query_string

        # transform print request body as appropriate
        body = self._transform_body()

        # forward request to target (without Host Header)
        http = httplib2.Http()
        h = dict(self.request.headers)
        h.pop("Host", h) # not sure this is needed TODO
        h['Content-Length'] = str(len(body))
        try:
            resp, content = http.request(_url, method='POST', body=body, headers=h)
        except:
            return HTTPBadGateway()

        return Response(content, status=resp.status, headers=dict(resp))

    @view_config(route_name='printproxy_get')
    def get(self):
        """ Get created PDF. """
        
        id = self.request.matchdict.get('id')

        # get URL
        _url = self.config['print.url'] + id + '.pdf.printout'

        # forward request to target (without Host Header)
        http = httplib2.Http()
        h = dict(self.request.headers)
        h.pop("Host", h) # not sure this is needed TODO
        try:
            resp, content = http.request(_url, method='GET', headers=h)
        except:
            return HTTPBadGateway()

        headers = {}
        headers['content-type'] = resp['content-type']
        headers['content-disposition'] = resp['content-disposition']
        # remove Pragma and Cache-Control headers because of ie bug:
        # http://support.microsoft.com/default.aspx?scid=KB;EN-US;q316431
        #del response.headers['Pragma']
        #del response.headers['Cache-Control']
        return Response(content, status=resp.status, headers=headers)

    def _read_request_body(self):
        content_length = int(self.request.environ['CONTENT_LENGTH'])
        return self.request.environ['wsgi.input'].read(content_length)

    def _transform_body(self):

        body = self._read_request_body()

        username = authenticated_userid(self.request)
        user = None if username is None \
                else DBSession.query(User) \
                        .filter_by(username=username).one()

        root = json.loads(body)

        for layer in root['layers']:
            layer['customParams'] = dict(map_resolution=root['dpi'])

        if user:
            role_id = user.role.id

            for layer in root['layers']:
                layer['customParams']['role_id'] = role_id

        return json.dumps(root)
