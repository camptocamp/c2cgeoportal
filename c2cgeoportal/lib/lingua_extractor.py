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
import subprocess

from json import loads
from urlparse import urlsplit
from xml.dom.minidom import parseString

from lingua.extractors import Extractor
from lingua.extractors import Message
from pyramid.paster import bootstrap

from c2cgeoportal.lib import add_url_params


class GeoMapfishAngularExtractor(Extractor):  # pragma: nocover
    "GeoMapfish angular extractor"

    extensions = [".js", ".html"]

    def __call__(self, filename, options):
        message_str = subprocess.check_output(["node", "tools/extract-messages.js", filename])
        try:
            messages = loads(message_str)
            return [Message(
                None, message, None, [], u"", u"", context.split(":")
            ) for context, message in messages]
        except:
            print("An error occurred")
            print(message_str)
            print("------")
            raise


class GeoMapfishThemeExtractor(Extractor):  # pragma: nocover
    "GeoMapfish theme extractor"

    # Run on the development.ini file
    extensions = [".ini"]

    def __call__(self, filename, options):
        messages = []
        self.capabilities_cache = {}

        self.env = bootstrap(filename)

        from c2cgeoportal.models import Theme, LayerGroup, \
            LayerWMS, LayerWMTS

        self._import(Theme, messages)
        self._import(LayerGroup, messages)
        self._import(LayerWMS, messages)
        self._import(LayerWMTS, messages)

        return messages

    def _import(self, object_type, messages, callback=None):
        from c2cgeoportal.models import DBSession

        items = DBSession.query(object_type)
        for item in items:
            messages.append(Message(
                None, item.name, None, [], u"", u"",
                (".".join([item.item_type, item.name]), item.id)
            ))

            if callback is not None:
                callback(item, messages)

    def _import_layer_internal_wms(self, layer, messages):
        url = self._get_capabilities(self.env["registry"].settings["mapserverproxy"]["mapserv_url"])
        for wms_layer in layer.layerplit(","):
            self._import_layer_attributes(
                url, wms_layer, layer.item_type, layer.name, layer.id, messages
            )

    def _import_layer_external_wms(self, layer, messages):
        for wms_layer in layer.layerplit(","):
            self._import_layer_attributes(
                layer.url, wms_layer, layer.item_type, layer.name, layer.id, messages
            )

    def _import_layer_wmts(self, layer, messages):
        layers = [d.value for d in layer.ui_metadata if d.name == "wms_layer"]
        url = [d.value for d in layer.ui_metadata if d.name == "wms_url"]
        if len(url) == 1 and len(layers) >= 1:
            for wms_layer in layers:
                self._import_layer_attributes(
                    url[0], wms_layer, layer.item_type, layer.name, layer.id, messages
                )

    def _import_layer_attributes(self, url, layer, item_type, name, layer_id, messages):
        for attribute in self._layer_attributes(url, layer):
            messages.append(Message(
                None, attribute, None, [], "", "", (".".join([item_type, name]), layer_id)
            ))

    def _layer_attributes(self, url, layer):
        url = add_url_params(url, {
            "SERVICE": "WFS",
            "VERSION": "1.1.0",
            "REQUEST": "DescribeFeatureType",
            "TYPENAME": layer,
        })

        print("Get DescribeFeatureType for url: %s" % url)

        # forward request to target (without Host Header)
        http = httplib2.Http()
        h = dict(self.request.headers)
        if urlsplit(url).hostname != "localhost":  # pragma: no cover
            h.pop("Host")
        try:
            resp, content = http.request(url, method="GET", headers=h)
        except:  # pragma: no cover
            print("Unable to DescribeFeatureType from url %s" % url)
            self.capabilities_cache[url] = None
            return []

        if resp.status < 200 or resp.status >= 300:  # pragma: no cover
            print(
                "DescribeFeatureType from url %s return the error: %i %s" %
                (url, resp.status, resp.reason)
            )
            self.capabilities_cache[url] = None
            return []

        try:
            describe = parseString(content)
        except AttributeError:
            print(
                "WARNING! an error occured while trying to "
                "read the mapfile and recover the themes."
            )
            print("url: %s\nxml:\n%s" % (url, content))

        attributes = []
        for element in describe.getElementsByTagName("element"):
            if element.getAttribute("type") not in [
                "gml:PointPropertyType", "gml:LineStringPropertyType", "gml:PolygonPropertyType"
            ]:
                attributes.append(element.getAttribute("name"))
