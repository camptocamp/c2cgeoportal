import httplib2
import urllib
from io import RawIOBase, StringIO
from xml.sax import make_parser, handler
from xml.sax.saxutils import XMLFilterBase, XMLGenerator
from xml.sax.xmlreader import InputSource

from pyramid.httpexceptions import HTTPBadGateway, HTTPNotAcceptable
from pyramid.response import Response
from pyramid.view import view_config
from pyramid.security import authenticated_userid

from c2cgeoportal.models import DBSession, User

@view_config(route_name='mapserverproxy')
def proxy(request):

    username = authenticated_userid(request)
    user = None if username is None \
            else DBSession.query(User).filter_by(username=username).one()
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
    except:
        return HTTPBadGateway()

    # check for allowed content types
    if not resp.has_key("content-type"):
        return HTTPNotAcceptable()

    if method == "POST" and _is_get_feature(request):
        class CurrentHandler(XMLFilterBase):
            def __init__(self, upstream, downstream):
                XMLFilterBase.__init__(self, upstream)
                self._count = 0
                self._downstream = downstream

            def startDocument(self):
                # Set the initial state, and set up the stack of states
                self._exportContent = True

            def startElement(self, name, attrs):
                if name == "gml:featureMember":
                    if self._count >= 200:
                        self._exportContent = False
                    else:
                        self._count += 1
                # Only forward the event if the state warrants it
                if self._exportContent:
                    self._downstream.startElement(name, attrs)

            def endElement(self, name):
                # Only forward the event if the state warrants it
                if self._exportContent:
                    self._downstream.endElement(name)

                if name == "gml:featureMember":
                    self._exportContent = True

            def characters(self, content):
                # Only forward the event if the state warrants it
                if self._exportContent:
                    self._downstream.characters(content)

        class StringStringIO(StringIO):
            def write(self, s):
                return StringIO.write(self, unicode(s))

        parser = make_parser()
        inputSource = InputSource()
        contentbuffer = StringIO(content, encoding='utf-8')
        inputSource.setByteStream(contentbuffer)
        resultbuffer = StringStringIO(encoding='utf-8')
        downstream_handler = XMLGenerator(resultbuffer, 'utf-8')
        filter_handler = CurrentHandler(parser, downstream_handler)
        filter_handler.parse(inputSource)
        content = resultbuffer.getvalue()
        contentbuffer.close()
        resultbuffer.close()

    return Response(content, status=resp.status,
            headers={"Content-Type": resp["content-type"]})

def _is_get_feature(request):
    class CurrentHandler(handler.ContentHandler):
        def __init__(self):
            self.result = False

        def startElement(self, name, attrs):
            if name == "wfs:GetFeature":
                self.result = True

    parser = make_parser()
    currentHandler = CurrentHandler()
    parser.setContentHandler(currentHandler)
    inputSource = InputSource()
    contentbuffer = StringIO(request.body)
    inputSource.setByteStream(contentbuffer)
    parser.parse(inputSource)
    contentbuffer.close()
    return currentHandler.result

