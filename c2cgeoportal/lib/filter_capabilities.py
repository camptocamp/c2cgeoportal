# -*- coding: utf-8 -*-

# Copyright (c) 2014-2015, Camptocamp SA
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


import logging
import httplib2
from StringIO import StringIO
from urlparse import urlparse, urljoin
from urllib import urlopen

from xml import sax
from xml.sax import saxutils
from xml.sax.saxutils import XMLFilterBase, XMLGenerator
from xml.sax.xmlreader import InputSource

from pyramid.httpexceptions import HTTPBadGateway

from sqlalchemy import distinct

from owslib.wms import WebMapService

from c2cgeoportal.lib import caching, get_protected_layers_query
from c2cgeoportal.models import DBSession, Layer

cache_region = caching.get_region()
log = logging.getLogger(__name__)


@cache_region.cache_on_arguments()
def _get_protected_layers(role_id):
    q = get_protected_layers_query(role_id, distinct(Layer.name))
    return [r for r, in q.all()]


@cache_region.cache_on_arguments()
def _get_private_layers():
    q = DBSession.query(Layer.name).filter(Layer.public.is_(False))
    return [r for r, in q.all()]


@cache_region.cache_on_arguments()
def _wms_structure(wms_url, host):
    params = (
        ('SERVICE', 'WMS'),
        ('VERSION', '1.1.1'),
        ('REQUEST', 'GetCapabilities'),
    )

    url = urlparse(wms_url)
    wms_url = "%s://%s%s?%s%s%s" % (
        url.scheme, url.hostname, url.path, url.query,
        "&" if len(url.query) > 0 else "",
        '&'.join(['='.join(p) for p in params])
    )

    log.info("Get WMS GetCapabilities for URL: %s" % wms_url)

    # forward request to target (without Host Header)
    http = httplib2.Http()
    headers = dict()
    if url.hostname == 'localhost' and host is not None:  # pragma: no cover
        headers['Host'] = host
    try:
        resp, content = http.request(wms_url, method='GET', headers=headers)
    except:  # pragma: no cover
        raise HTTPBadGateway("Unable to GetCapabilities from wms_url %s" % wms_url)

    if resp.status < 200 or resp.status >= 300:  # pragma: no cover
        raise HTTPBadGateway(
            "GetCapabilities from wms_url %s return the error: %i %s" %
            (wms_url, resp.status, resp.reason)
        )

    try:
        wms = WebMapService(None, xml=content)
        result = {}

        def _fill(name, parent):
            if parent is None:
                return
            if parent.name not in result:
                result[parent.name] = []
            result[parent.name].append(name)
            _fill(name, parent.parent)

        for layer in wms.contents.values():
            _fill(layer.name, layer.parent)
        return result

    except AttributeError:  # pragma: no cover
        error = "WARNING! an error occured while trying to " \
            "read the mapfile and recover the themes."
        error = "%s\nurl: %s\nxml:\n%s" % (error, wms_url, content)
        log.exception(error)
        raise HTTPBadGateway(error)


def enable_proxies(proxies):  # pragma: no cover
    old_prepare_input_source = saxutils.prepare_input_source

    def caching_prepare_input_source(source, base=None):
        if isinstance(source, InputSource):
            return source

        full_uri = urljoin(base or "", source)

        # Convert StringIO to string
        if hasattr(full_uri, 'getvalue'):
            full_uri = full_uri.getvalue()

        if not full_uri.startswith('http:'):
            args = (source,) if base is None else (source, base)
            return old_prepare_input_source(*args)

        document = urlopen(full_uri, proxies=proxies)

        input_source = InputSource()
        input_source.setSystemId(source)
        input_source.setByteStream(document)

        return input_source

    saxutils.prepare_input_source = caching_prepare_input_source


def filter_capabilities(content, role_id, wms, wms_url, headers, proxies):

    if proxies:  # pragma: no cover
        enable_proxies(proxies)

    wms_structure = _wms_structure(wms_url, headers.get('Host', None))
    tmp_private_layers = list(_get_private_layers())
    for name in _get_protected_layers(role_id):
        tmp_private_layers.remove(name)

    private_layers = set()
    for layer in tmp_private_layers:
        private_layers.add(layer)
        if layer in wms_structure:
            private_layers.update(wms_structure[layer])

    parser = sax.make_parser()
    result = StringIO()
    downstream_handler = XMLGenerator(result, 'utf-8')
    filter_handler = _CapabilitiesFilter(
        parser, downstream_handler, private_layers,
        u'Layer' if wms else u'FeatureType'
    )
    filter_handler.parse(StringIO(content))
    return unicode(result.getvalue(), 'utf-8')


class _Layer:
    def __init__(self, self_hidden=False):
        self.accumul = []
        self.hidden = True
        self.self_hidden = self_hidden


class _CapabilitiesFilter(XMLFilterBase):
    """
    SAX filter to ensure that contiguous white space nodes are
    delivered merged into a single node
    """

    def __init__(self, upstream, downstream, private_layers, tag_name):
        XMLFilterBase.__init__(self, upstream)
        self._downstream = downstream
        self._accumulator = []
        self.private_layers = private_layers
        self.layers_path = []
        self.in_name = False
        self.tag_name = tag_name

    def _complete_text_node(self):
        if self._accumulator:
            self._downstream.characters(''.join(self._accumulator))
            self._accumulator = []

    def _do(self, action):
        if len(self.layers_path) != 0 and self.layers_path[-1].hidden:
            self.layers_path[-1].accumul.append(action)
        else:
            self._complete_text_node()
            action()

    def setDocumentLocator(self, locator):  # noqa
        self._downstream.setDocumentLocator(locator)

    def startDocument(self):  # noqa
        self._downstream.startDocument()

    def endDocument(self):  # noqa
        self._downstream.endDocument()

    def startPrefixMapping(self, prefix, uri):  # pragma: no cover  # noqa
        self._downstream.startPrefixMapping(prefix, uri)

    def endPrefixMapping(self, prefix):  # pragma: no cover  # noqa
        self._downstream.endPrefixMapping(prefix)

    def startElement(self, name, attrs):  # noqa
        if name == self.tag_name:
            if len(self.layers_path) > 1:
                self.layers_path.append(_Layer(
                    self.layers_path[-1].self_hidden
                ))
            else:
                self.layers_path.append(_Layer())
        elif name == 'Name' and len(self.layers_path) != 0:
            self.in_name = True

        self._do(lambda: self._downstream.startElement(name, attrs))

    def endElement(self, name):  # noqa
        self._do(lambda: self._downstream.endElement(name))

        if name == self.tag_name:
            self.layers_path.pop()
        elif name == 'Name':
            self.in_name = False

    def startElementNS(self, name, qname, attrs):  # pragma: nocover  # noqa
        self._do(lambda: self._downstream.startElementNS(name, qname, attrs))

    def endElementNS(self, name, qname):  # pragma: nocover  # noqa
        self._do(lambda: self._downstream.endElementNS(name, qname))

    def characters(self, text):
        if self.in_name and len(self.layers_path) != 0 and not \
                self.layers_path[-1].self_hidden is True:
            if text not in self.private_layers:
                for layer in self.layers_path:
                    layer.hidden = False
                    for action in layer.accumul:
                        self._complete_text_node()
                        action()
                    layer.accumul = []
            else:
                self.layers_path[-1].self_hidden = True

        self._do(lambda: self._accumulator.append(text.encode('utf-8')))

    def ignorableWhitespace(self, ws):  # pragma: nocover  # noqa
        self._do(lambda: self._accumulator.append(ws))

    def processingInstruction(self, target, body):  # pragma: nocover  # noqa
        self._do(lambda: self._downstream.processingInstruction(target, body))

    def skippedEntity(self, name):  # pragma: no cover  # noqa
        self._downstream.skippedEntity(name)
