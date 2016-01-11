# -*- coding: utf-8 -*-

# Copyright (c) 2014-2016, Camptocamp SA
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
from urlparse import urlsplit, urljoin
from urllib import urlopen

from xml import sax
from xml.sax import saxutils
from xml.sax.saxutils import XMLFilterBase, XMLGenerator
from xml.sax.xmlreader import InputSource

from pyramid.httpexceptions import HTTPBadGateway

from sqlalchemy import distinct

from owslib.wms import WebMapService

from c2cgeoportal.lib import caching, get_protected_layers_query, \
    get_writable_layers_query, add_url_params
from c2cgeoportal.models import DBSession, Layer

cache_region = caching.get_region()
log = logging.getLogger(__name__)


@cache_region.cache_on_arguments()
def get_protected_layers(role_id):
    q = get_protected_layers_query(role_id, distinct(Layer.name))
    return [r for r, in q.all()]


@cache_region.cache_on_arguments()
def get_private_layers():
    q = DBSession.query(Layer.name).filter(Layer.public.is_(False))
    return [r for r, in q.all()]


@cache_region.cache_on_arguments()
def get_writable_layers(role_id):
    q = get_writable_layers_query(role_id, distinct(Layer.name))
    return set([r for r, in q.all()])


@cache_region.cache_on_arguments()
def _wms_structure(wms_url, host):
    url = urlsplit(wms_url)
    wms_url = add_url_params(wms_url, {
        "SERVICE": "WMS",
        "VERSION": "1.1.1",
        "REQUEST": "GetCapabilities",
    })

    log.info("Get WMS GetCapabilities for URL: %s" % wms_url)

    # forward request to target (without Host Header)
    http = httplib2.Http()
    headers = dict()
    if url.hostname == "localhost" and host is not None:  # pragma: no cover
        headers["Host"] = host
    try:
        resp, content = http.request(wms_url, method="GET", headers=headers)
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
        if hasattr(full_uri, "getvalue"):
            full_uri = full_uri.getvalue()

        if not full_uri.startswith("http:"):
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

    wms_structure = _wms_structure(wms_url, headers.get("Host", None))
    tmp_private_layers = list(get_private_layers())
    for name in get_protected_layers(role_id):
        tmp_private_layers.remove(name)

    private_layers = set()
    for layer in tmp_private_layers:
        private_layers.add(layer)
        if layer in wms_structure:
            private_layers.update(wms_structure[layer])

    parser = sax.make_parser()
    result = StringIO()
    downstream_handler = XMLGenerator(result, "utf-8")
    filter_handler = _CapabilitiesFilter(
        parser, downstream_handler,
        u"Layer" if wms else u"FeatureType",
        layers_blacklist=private_layers
    )
    # skip inclusion of DTDs
    parser.setFeature(sax.handler.feature_external_ges, False)
    parser.setFeature(sax.handler.feature_external_pes, False)
    filter_handler.parse(StringIO(content))
    return unicode(result.getvalue(), "utf-8")


def filter_wfst_capabilities(content, role_id, wfs_url, proxies):

    if proxies:  # pragma: no cover
        enable_proxies(proxies)

    writable_layers = get_writable_layers(role_id)

    parser = sax.make_parser()
    result = StringIO()
    downstream_handler = XMLGenerator(result, "utf-8")
    filter_handler = _CapabilitiesFilter(
        parser, downstream_handler,
        u"FeatureType",
        layers_whitelist=writable_layers
    )
    filter_handler.parse(StringIO(content))
    filtered_content = unicode(result.getvalue(), "utf-8")
    return filtered_content


class _Layer:
    def __init__(self, self_hidden=False):
        self.accumul = []
        self.hidden = True
        self.self_hidden = self_hidden
        self.has_children = False
        self.children_nb = 0


class _CapabilitiesFilter(XMLFilterBase):
    """
    SAX filter to show only the allowed layers in a GetCapabilities request.
    The filter removes elements of type `tag_name` where the `name`
    attribute is part of the set `layers_blacklist` (when `layers_blacklist`
    is given) or is not part of the set `layers_whitelist` (when
    `layers_whitelist` is given).
    """

    def __init__(
            self, upstream, downstream, tag_name,
            layers_blacklist=None, layers_whitelist=None):
        XMLFilterBase.__init__(self, upstream)
        self._downstream = downstream
        self._accumulator = []

        assert layers_blacklist is not None or layers_whitelist is not None, \
            "either layers_blacklist OR layers_whitelist must be set"
        assert not (
            layers_blacklist is not None and
            layers_whitelist is not None), \
            "only either layers_blacklist OR layers_whitelist can be set"
        self.layers_blacklist = layers_blacklist
        self.layers_whitelist = layers_whitelist

        self.layers_path = []
        self.in_name = False
        self.tag_name = tag_name
        self.level = 0

    def _complete_text_node(self):
        if self._accumulator:
            self._downstream.characters("".join(self._accumulator))
            self._accumulator = []

    def _do(self, action):
        if len(self.layers_path) != 0:
            self.layers_path[-1].accumul.append(action)
        else:
            self._complete_text_node()
            action()

    def _add_child(self, layer):
        if not layer.hidden and not (
                layer.has_children and layer.children_nb == 0
        ):
            for action in layer.accumul:
                self._complete_text_node()
                action()
            layer.accumul = []

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
            self.level += 1
            parent_layer = None
            if len(self.layers_path) > 0:
                parent_layer = self.layers_path[-1]
                parent_layer.has_children = True
                parent_layer.children_nb += 1
            layer = _Layer(
                parent_layer.self_hidden
            ) if len(self.layers_path) > 1 else _Layer()
            self.layers_path.append(layer)

            if parent_layer is not None:
                parent_layer.accumul.append(
                    lambda: self._add_child(layer)
                )
        elif name == "Name" and len(self.layers_path) != 0:
            self.in_name = True

        self._do(lambda: self._downstream.startElement(name, attrs))

    def endElement(self, name):  # noqa
        self._do(lambda: self._downstream.endElement(name))

        if name == self.tag_name:
            self.level -= 1
            if self.level == 0 and not self.layers_path[0].hidden:
                for action in self.layers_path[0].accumul:
                    self._complete_text_node()
                    action()
            self.layers_path.pop()
        elif name == "Name":
            self.in_name = False

    def startElementNS(self, name, qname, attrs):  # pragma: nocover  # noqa
        self._do(lambda: self._downstream.startElementNS(name, qname, attrs))

    def endElementNS(self, name, qname):  # pragma: nocover  # noqa
        self._do(lambda: self._downstream.endElementNS(name, qname))

    def _keep_layer(self, layer_name):
        return (
            self.layers_blacklist is not None and
            layer_name not in self.layers_blacklist) or (
            self.layers_whitelist is not None and
            layer_name in self.layers_whitelist)

    def characters(self, text):
        if self.in_name and len(self.layers_path) != 0 and not \
                self.layers_path[-1].self_hidden is True:
            layer_name = normalize_typename(text)
            if self._keep_layer(layer_name):
                for layer in self.layers_path:
                    layer.hidden = False
            else:
                # remove layer
                self.layers_path[-1].self_hidden = True
                if len(self.layers_path) > 1:
                    self.layers_path[-2].children_nb -= 1

        self._do(lambda: self._accumulator.append(text.encode("utf-8")))

    def ignorableWhitespace(self, ws):  # pragma: nocover  # noqa
        self._do(lambda: self._accumulator.append(ws))

    def processingInstruction(self, target, body):  # pragma: nocover  # noqa
        self._do(lambda: self._downstream.processingInstruction(target, body))

    def skippedEntity(self, name):  # pragma: no cover  # noqa
        self._downstream.skippedEntity(name)


def normalize_tag(tag):
    """
    Drops the namespace from a tag and converts to lower case.
    e.g. '{http://....}TypeName' -> 'TypeName'
    """
    normalized = tag
    if len(tag) >= 3:
        if tag[0] == "{":
            normalized = tag[1:].split("}")[1]
    return normalized.lower()


def normalize_typename(typename):
    """
    Drops the namespace from a type name and converts to lower case.
    e.g. 'tows:parks' -> 'parks'
    """
    normalized = typename
    if ":" in typename:
        normalized = typename.split(":")[1]
    return normalized.lower()
