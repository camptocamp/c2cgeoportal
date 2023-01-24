# Copyright (c) 2014-2023, Camptocamp SA
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
import logging
import xml.sax.handler  # nosec
from io import StringIO
from typing import Any, Callable, Dict, List, Optional, Set, Union
from xml.sax.saxutils import XMLFilterBase, XMLGenerator  # nosec

import defusedxml.expatreader
import pyramid.request
import requests
from owslib.map.wms111 import ContentMetadata as ContentMetadata111
from owslib.map.wms130 import ContentMetadata as ContentMetadata130
from owslib.wms import WebMapService
from pyramid.httpexceptions import HTTPBadGateway

from c2cgeoportal_commons.lib.url import Url
from c2cgeoportal_geoportal.lib import caching, get_ogc_server_wfs_url_ids, get_ogc_server_wms_url_ids
from c2cgeoportal_geoportal.lib.layers import get_private_layers, get_protected_layers, get_writable_layers

CACHE_REGION = caching.get_region("std")
LOG = logging.getLogger(__name__)
ContentMetadata = Union[ContentMetadata111, ContentMetadata130]


@CACHE_REGION.cache_on_arguments()  # type: ignore
def wms_structure(wms_url: Url, host: str, request: pyramid.request.Request) -> Dict[str, List[str]]:
    """Get a simple serializable structure of the WMS capabilities."""
    url = wms_url.clone().add_query({"SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetCapabilities"})

    # Forward request to target (without Host Header)
    headers = {}
    if url.hostname == "localhost" and host is not None:
        headers["Host"] = host
    try:
        response = requests.get(
            url.url(), headers=headers, **request.registry.settings.get("http_options", {})
        )
    except Exception:
        LOG.exception("Unable to GetCapabilities from wms_url '%s'", wms_url)
        raise HTTPBadGateway(  # pylint: disable=raise-missing-from
            "Unable to GetCapabilities, see logs for details"
        )

    if not response.ok:
        raise HTTPBadGateway(
            f"GetCapabilities from wms_url {url.url()} return the error: "
            f"{response.status_code:d} {response.reason}"
        )

    try:
        wms = WebMapService(None, xml=response.content)
        result: Dict[str, List[str]] = {}

        def _fill(name: str, parent: ContentMetadata) -> None:
            if parent is None:
                return
            if parent.name not in result:
                result[parent.name] = []
            result[parent.name].append(name)
            _fill(name, parent.parent)

        for layer in list(wms.contents.values()):
            _fill(layer.name, layer.parent)
        return result

    except AttributeError:
        error = "WARNING! an error occurred while trying to read the mapfile and recover the themes."
        error = f"{error}\nurl: {wms_url}\nxml:\n{response.text}"
        LOG.exception(error)
        raise HTTPBadGateway(error)  # pylint: disable=raise-missing-from

    except SyntaxError:
        error = "WARNING! an error occurred while trying to read the mapfile and recover the themes."
        error = f"{error}\nurl: {wms_url}\nxml:\n{response.text}"
        LOG.exception(error)
        raise HTTPBadGateway(error)  # pylint: disable=raise-missing-from


def filter_capabilities(
    content: str, wms: bool, url: Url, headers: Dict[str, str], request: pyramid.request.Request
) -> str:
    """Filter the WMS/WFS capabilities."""

    wms_structure_ = wms_structure(url, headers.get("Host"), request)

    ogc_server_ids = (
        get_ogc_server_wms_url_ids(request) if wms else get_ogc_server_wfs_url_ids(request)
    ).get(url.url())
    gmf_private_layers = copy.copy(get_private_layers(ogc_server_ids))
    for id_ in list(get_protected_layers(request, ogc_server_ids).keys()):
        if id_ in gmf_private_layers:
            del gmf_private_layers[id_]

    private_layers = set()
    for gmf_layer in list(gmf_private_layers.values()):
        for ogc_layer in gmf_layer.layer.split(","):
            private_layers.add(ogc_layer)
            if ogc_layer in wms_structure_:
                private_layers.update(wms_structure_[ogc_layer])

    LOG.debug(
        "Filter capabilities of OGC server %s\nprivate_layers: %s",
        ", ".join([str(e) for e in ogc_server_ids]),
        ", ".join(private_layers),
    )

    parser = defusedxml.expatreader.create_parser(forbid_external=False)
    # skip inclusion of DTDs
    parser.setFeature(xml.sax.handler.feature_external_ges, False)
    parser.setFeature(xml.sax.handler.feature_external_pes, False)

    result = StringIO()
    downstream_handler = XMLGenerator(result, "utf-8")
    filter_handler = _CapabilitiesFilter(
        parser, downstream_handler, "Layer" if wms else "FeatureType", layers_blacklist=private_layers
    )
    filter_handler.parse(StringIO(content))  # type: ignore
    return result.getvalue()


def filter_wfst_capabilities(content: str, wfs_url: Url, request: pyramid.request.Request) -> str:
    """Filter the WTS capabilities."""

    writable_layers: Set[str] = set()
    ogc_server_ids = get_ogc_server_wfs_url_ids(request).get(wfs_url.url())

    for gmf_layer in list(get_writable_layers(request, ogc_server_ids).values()):
        writable_layers |= set(gmf_layer.layer.split(","))

    LOG.debug(
        "Filter WFS-T capabilities of OGC server %s\nlayers: %s",
        ", ".join([str(e) for e in ogc_server_ids]),
        ", ".join(writable_layers),
    )

    parser = defusedxml.expatreader.create_parser(forbid_external=False)
    # skip inclusion of DTDs
    parser.setFeature(xml.sax.handler.feature_external_ges, False)
    parser.setFeature(xml.sax.handler.feature_external_pes, False)

    result = StringIO()
    downstream_handler = XMLGenerator(result, "utf-8")
    filter_handler = _CapabilitiesFilter(
        parser, downstream_handler, "FeatureType", layers_whitelist=writable_layers
    )
    filter_handler.parse(StringIO(content))  # type: ignore
    return result.getvalue()


class _Layer:
    def __init__(self, self_hidden: bool = False):
        self.accumulator: List[Callable[[], None]] = []
        self.hidden = True
        self.self_hidden = self_hidden
        self.has_children = False
        self.children_nb = 0


class _CapabilitiesFilter(XMLFilterBase):
    """
    SAX filter to show only the allowed layers in a GetCapabilities request.

    The filter removes elements of type `tag_name` where the `name` attribute is part of the set
    `layers_blacklist` (when `layers_blacklist` is given) or is not part of the set `layers_whitelist` (when
    `layers_whitelist` is given).
    """

    def __init__(
        self,
        upstream: XMLFilterBase,
        downstream: XMLGenerator,
        tag_name: str,
        layers_blacklist: Optional[Set[str]] = None,
        layers_whitelist: Optional[Set[str]] = None,
    ):
        XMLFilterBase.__init__(self, upstream)
        self._downstream = downstream
        self._accumulator: List[str] = []

        assert (
            layers_blacklist is not None or layers_whitelist is not None
        ), "either layers_blacklist OR layers_whitelist must be set"
        assert not (
            layers_blacklist is not None and layers_whitelist is not None
        ), "only either layers_blacklist OR layers_whitelist can be set"

        if layers_blacklist is not None:
            layers_blacklist = {layer.lower() for layer in layers_blacklist}
        if layers_whitelist is not None:
            layers_whitelist = {layer.lower() for layer in layers_whitelist}
        self.layers_blacklist = layers_blacklist
        self.layers_whitelist = layers_whitelist

        self.layers_path: List[_Layer] = []
        self.in_name = False
        self.tag_name = tag_name
        self.level = 0

    def _complete_text_node(self) -> None:
        if self._accumulator:
            self._downstream.characters("".join(self._accumulator))  # type: ignore
            self._accumulator = []

    def _do(self, action: Callable[[], Any]) -> None:
        if self.layers_path:
            self.layers_path[-1].accumulator.append(action)
        else:
            self._complete_text_node()
            action()

    def _add_child(self, layer: _Layer) -> None:
        if not layer.hidden and not (layer.has_children and layer.children_nb == 0):
            for action in layer.accumulator:
                self._complete_text_node()
                action()
            layer.accumulator = []

    def setDocumentLocator(self, locator: str) -> None:  # noqa: ignore=N802
        self._downstream.setDocumentLocator(locator)  # type: ignore

    def startDocument(self) -> None:  # noqa: ignore=N802
        self._downstream.startDocument()  # type: ignore

    def endDocument(self) -> None:  # noqa: ignore=N802
        self._downstream.endDocument()  # type: ignore

    def startPrefixMapping(self, prefix: str, uri: str) -> None:  # noqa: ignore=N802
        self._downstream.startPrefixMapping(prefix, uri)  # type: ignore

    def endPrefixMapping(self, prefix: str) -> None:  # noqa: ignore=N802
        self._downstream.endPrefixMapping(prefix)  # type: ignore

    def startElement(self, name: str, attrs: xml.sax.xmlreader.AttributesImpl) -> None:  # noqa: ignore=N802
        if name == self.tag_name:
            self.level += 1
            if self.layers_path:
                parent_layer = self.layers_path[-1]
                parent_layer.has_children = True
                parent_layer.children_nb += 1
                layer = _Layer(parent_layer.self_hidden) if len(self.layers_path) > 1 else _Layer()
                self.layers_path.append(layer)

                parent_layer.accumulator.append(lambda: self._add_child(layer))
            else:
                layer = _Layer()
                self.layers_path.append(layer)
        elif name == "Name" and self.layers_path:
            self.in_name = True

        self._do(lambda: self._downstream.startElement(name, attrs))  # type: ignore

    def endElement(self, name: str) -> None:  # noqa: ignore=N802
        self._do(lambda: self._downstream.endElement(name))  # type: ignore

        if name == self.tag_name:
            self.level -= 1
            if self.level == 0 and not self.layers_path[0].hidden:
                for action in self.layers_path[0].accumulator:
                    self._complete_text_node()
                    action()
            self.layers_path.pop()
        elif name == "Name":
            self.in_name = False

    def startElementNS(self, name: str, qname: str, attrs: Dict[str, str]) -> None:  # noqa: ignore=N802
        self._do(lambda: self._downstream.startElementNS(name, qname, attrs))  # type: ignore

    def endElementNS(self, name: str, qname: str) -> None:  # noqa: ignore=N802
        self._do(lambda: self._downstream.endElementNS(name, qname))  # type: ignore

    def _keep_layer(self, layer_name: str) -> bool:
        return (self.layers_blacklist is not None and layer_name not in self.layers_blacklist) or (
            self.layers_whitelist is not None and layer_name in self.layers_whitelist
        )

    def characters(self, content: str) -> None:
        if self.in_name and self.layers_path and not self.layers_path[-1].self_hidden is True:
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

    def ignorableWhitespace(self, chars: str) -> None:  # noqa: ignore=N802
        self._do(lambda: self._accumulator.append(chars))

    def processingInstruction(self, target: str, data: str) -> None:  # noqa: ignore=N802
        self._do(lambda: self._downstream.processingInstruction(target, data))  # type: ignore

    def skippedEntity(self, name: str) -> None:  # noqa: ignore=N802
        self._downstream.skippedEntity(name)  # type: ignore


def normalize_tag(tag: str) -> str:
    """
    Drop the namespace from a tag and converts to lower case.

    e.g. '{https://....}TypeName' -> 'TypeName'
    """
    normalized = tag
    if len(tag) >= 3:
        if tag[0] == "{":
            normalized = tag[1:].split("}")[1]
    return normalized.lower()


def normalize_typename(typename: str) -> str:
    """
    Drop the namespace from a type name and converts to lower case.

    e.g. 'tows:parks' -> 'parks'
    """
    normalized = typename
    if ":" in typename:
        normalized = typename.split(":")[1]
    return normalized.lower()
