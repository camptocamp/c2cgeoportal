# -*- coding: utf-8 -*-

# Copyright (c) 2014-2019, Camptocamp SA
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


import copy
import defusedxml.expatreader
import logging
import requests
import xml.sax.handler

from io import StringIO
from owslib.wms import WebMapService
from pyramid.httpexceptions import HTTPBadGateway
from typing import List  # noqa, pylint: disable=unused-import
from urllib.parse import urlsplit
from xml.sax.saxutils import XMLFilterBase, XMLGenerator

from c2cgeoportal_commons.models import static
from c2cgeoportal_geoportal.lib import caching, add_url_params, get_ogc_server_wms_url_ids,\
    get_ogc_server_wfs_url_ids
from c2cgeoportal_geoportal.lib.layers import get_protected_layers, get_writable_layers, get_private_layers

cache_region = caching.get_region()
log = logging.getLogger(__name__)


@cache_region.cache_on_arguments()
def wms_structure(wms_url, host, request):
    url = urlsplit(wms_url)
    wms_url = add_url_params(wms_url, {
        "SERVICE": "WMS",
        "VERSION": "1.1.1",
        "REQUEST": "GetCapabilities",
    })

    # Forward request to target (without Host Header)
    headers = dict()
    if url.hostname == "localhost" and host is not None:  # pragma: no cover
        headers["Host"] = host
    try:
        response = requests.get(
            wms_url, headers=headers,
            **request.registry.settings.get("http_options", {})
        )
    except Exception:  # pragma: no cover
        raise HTTPBadGateway("Unable to GetCapabilities from wms_url {0!s}".format(wms_url))

    if not response.ok:  # pragma: no cover
        raise HTTPBadGateway(
            "GetCapabilities from wms_url {0!s} return the error: {1:d} {2!s}".format(
                wms_url, response.status_code, response.reason
            )
        )

    try:
        wms = WebMapService(None, xml=response.content)
        result = {}

        def _fill(name, parent):
            if parent is None:
                return
            if parent.name not in result:
                result[parent.name] = []
            result[parent.name].append(name)
            _fill(name, parent.parent)

        for layer in list(wms.contents.values()):
            _fill(layer.name, layer.parent)
        return result

    except AttributeError:  # pragma: no cover
        error = "WARNING! an error occurred while trying to " \
            "read the mapfile and recover the themes."
        error = "{0!s}\nurl: {1!s}\nxml:\n{2!s}".format(error, wms_url, response.text)
        log.exception(error)
        raise HTTPBadGateway(error)

    except SyntaxError:  # pragma: no cover
        error = "WARNING! an error occurred while trying to " \
            "read the mapfile and recover the themes."
        error = "{0!s}\nurl: {1!s}\nxml:\n{2!s}".format(error, wms_url, response.text)
        log.exception(error)
        raise HTTPBadGateway(error)


def filter_capabilities(content, user: static.User, wms, url, headers, request):

    wms_structure_ = wms_structure(url, headers.get("Host"), request)

    ogc_server_ids = (
        get_ogc_server_wms_url_ids(request) if wms else
        get_ogc_server_wfs_url_ids(request)
    ).get(url)
    gmf_private_layers = copy.copy(get_private_layers(ogc_server_ids))
    for id_ in list(get_protected_layers(user, ogc_server_ids).keys()):
        if id_ in gmf_private_layers:
            del gmf_private_layers[id_]

    private_layers = set()
    for gmflayer in list(gmf_private_layers.values()):
        for ogclayer in gmflayer.layer.split(","):
            private_layers.add(ogclayer)
            if ogclayer in wms_structure_:
                private_layers.update(wms_structure_[ogclayer])

    parser = defusedxml.expatreader.create_parser(forbid_external=False)
    # skip inclusion of DTDs
    parser.setFeature(xml.sax.handler.feature_external_ges, False)
    parser.setFeature(xml.sax.handler.feature_external_pes, False)

    result = StringIO()
    downstream_handler = XMLGenerator(result, "utf-8")
    filter_handler = _CapabilitiesFilter(
        parser, downstream_handler,
        "Layer" if wms else "FeatureType",
        layers_blacklist=private_layers
    )
    filter_handler.parse(StringIO(content))
    return result.getvalue()


def filter_wfst_capabilities(content, user: static.User, wfs_url, request):
    writable_layers = []  # type: List[str]
    ogc_server_ids = get_ogc_server_wfs_url_ids(request).get(wfs_url)
    for gmflayer in list(get_writable_layers(user, ogc_server_ids).values()):
        writable_layers += gmflayer.layer.split(",")

    parser = defusedxml.expatreader.create_parser(forbid_external=False)
    # skip inclusion of DTDs
    parser.setFeature(xml.sax.handler.feature_external_ges, False)
    parser.setFeature(xml.sax.handler.feature_external_pes, False)

    result = StringIO()
    downstream_handler = XMLGenerator(result, "utf-8")
    filter_handler = _CapabilitiesFilter(
        parser, downstream_handler,
        "FeatureType",
        layers_whitelist=writable_layers
    )
    filter_handler.parse(StringIO(content))
    return result.getvalue()


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
            layers_blacklist is not None and layers_whitelist is not None
        ), "only either layers_blacklist OR layers_whitelist can be set"

        if layers_blacklist is not None:
            layers_blacklist = [layer.lower() for layer in layers_blacklist]
        if layers_whitelist is not None:
            layers_whitelist = [layer.lower() for layer in layers_whitelist]
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

    def startElementNS(self, name, qname, attrs):  # pragma: no cover  # noqa
        self._do(lambda: self._downstream.startElementNS(name, qname, attrs))

    def endElementNS(self, name, qname):  # pragma: no cover  # noqa
        self._do(lambda: self._downstream.endElementNS(name, qname))

    def _keep_layer(self, layer_name):
        return (
            self.layers_blacklist is not None and layer_name not in self.layers_blacklist
        ) or (
            self.layers_whitelist is not None and layer_name in self.layers_whitelist
        )

    def characters(self, content):
        if self.in_name and len(self.layers_path) != 0 and not \
                self.layers_path[-1].self_hidden is True:
            layer_name = normalize_typename(content)
            if self._keep_layer(layer_name):
                for layer in self.layers_path:
                    layer.hidden = False
            else:
                # remove layer
                self.layers_path[-1].self_hidden = True
                if len(self.layers_path) > 1:
                    self.layers_path[-2].children_nb -= 1

        self._do(lambda: self._accumulator.append(content))

    def ignorableWhitespace(self, chars):  # pragma: no cover  # noqa
        self._do(lambda: self._accumulator.append(chars))

    def processingInstruction(self, target, data):  # pragma: no cover  # noqa
        self._do(lambda: self._downstream.processingInstruction(target, data))

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
