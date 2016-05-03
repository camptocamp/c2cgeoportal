# -*- coding: utf-8 -*-

# Copyright (c) 2011-2016, Camptocamp SA
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

import yaml
from json import loads
from urlparse import urlsplit
from xml.dom.minidom import parseString
from sqlalchemy.exc import ProgrammingError

from lingua.extractors import Extractor
from lingua.extractors import Message
from pyramid.paster import bootstrap

from c2cgeoportal.lib import add_url_params
from c2cgeoportal.lib.bashcolor import colorize, RED


class GeoMapfishAngularExtractor(Extractor):  # pragma: nocover
    "GeoMapfish angular extractor"

    extensions = [".js", ".html"]

    def __call__(self, filename, options):
        message_str = subprocess.check_output(["node", "tools/extract-messages.js", filename])
        try:
            messages = []
            for contexts, message in loads(message_str):
                for context in contexts.split(", "):
                    messages.append(Message(
                        None, message, None, [], u"", u"", context.split(":")
                    ))
            return messages
        except:
            print(colorize("An error occurred", RED))
            print(colorize(message_str, RED))
            print("------")
            raise


class GeoMapfishConfigExtractor(Extractor):  # pragma: nocover
    "GeoMapfish config extractor (raster layers)"

    extensions = [".yaml"]

    def __call__(self, filename, options):
        with open(filename) as config_file:
            config = yaml.load(config_file)
            return [
                Message(
                    None, raster_layer, None, [], u"", u"",
                    (filename, u"raster/%s" % raster_layer)
                )
                for raster_layer in config.get("raster", {}).keys()
            ]


class GeoMapfishThemeExtractor(Extractor):  # pragma: nocover
    "GeoMapfish theme extractor"

    # Run on the development.ini file
    extensions = [".ini"]
    featuretype_cache = {}

    def __call__(self, filename, options):
        messages = []

        self.env = bootstrap(filename)
        with open("project.yaml") as f:
            self.package = yaml.load(f)

        try:
            from c2cgeoportal.models import Theme, LayerGroup, \
                LayerWMS, LayerWMTS

            self._import(Theme, messages)
            self._import(LayerGroup, messages)
            self._import(LayerWMS, messages, self._import_layer_wms)
            self._import(LayerWMTS, messages, self._import_layer_wmts)
        except ProgrammingError as e:
            print(colorize("ERROR: The database is probably not up to date", RED))
            print(colorize(e, RED))

        return messages

    def _import(self, object_type, messages, callback=None):
        from c2cgeoportal.models import DBSession

        items = DBSession.query(object_type)
        for item in items:
            messages.append(Message(
                None, item.name, None, [], u"", u"",
                (item.item_type, item.name)
            ))

            if callback is not None:
                callback(item, messages)

    def _import_layer_wms(self, layer, messages):
        server = layer.server_ogc
        url = server.url_wfs or server.url or \
            self.env["registry"].settings["mapserverproxy"]["mapserv_url"]
        for wms_layer in layer.layer.split(","):
            self._import_layer_attributes(
                url, wms_layer, layer.item_type, layer.name, layer.id, messages
            )

    def _import_layer_wmts(self, layer, messages):
        layers = [d.value for d in layer.ui_metadatas if d.name == "wmsLayer"]
        url = [d.value for d in layer.ui_metadatas if d.name == "wmsUrl"]
        if len(url) == 1 and len(layers) >= 1:
            for wms_layer in layers:
                self._import_layer_attributes(
                    url[0], wms_layer, layer.item_type, layer.name, layer.id, messages
                )

    def _import_layer_attributes(self, url, layer, item_type, name, layer_id, messages):
        for attribute in self._layer_attributes(url, layer):
            messages.append(Message(
                None, attribute, None, [], "", "", (".".join([item_type, name]), layer)
            ))

    def _layer_attributes(self, url, layer):
        url = add_url_params(url, {
            "SERVICE": "WFS",
            "VERSION": "1.1.0",
            "REQUEST": "DescribeFeatureType",
        })

        if url not in self.featuretype_cache:
            print("Get DescribeFeatureType for url: %s" % url)
            self.featuretype_cache[url] = None

            # forward request to target (without Host Header)
            http = httplib2.Http()
            h = {}
            if urlsplit(url).hostname == "localhost":  # pragma: no cover
                h["Host"] = self.package["host"]
            try:
                resp, content = http.request(url, method="GET", headers=h)
            except:  # pragma: no cover
                print("Unable to DescribeFeatureType from url %s" % url)
                self.featuretype_cache[url] = None
                return []

            if resp.status < 200 or resp.status >= 300:  # pragma: no cover
                print(
                    "DescribeFeatureType from url %s return the error: %i %s" %
                    (url, resp.status, resp.reason)
                )
                self.featuretype_cache[url] = None
                return []

            try:
                describe = parseString(content)
                self.featuretype_cache[url] = describe
            except AttributeError:
                print(
                    "WARNING! an error occured while trying to "
                    "read the mapfile and recover the themes."
                )
                print("url: %s\nxml:\n%s" % (url, content))
        else:
            describe = self.featuretype_cache[url]

        if describe is None:
            return []

        attributes = []
        # Should probably be adapted for other king of servers
        for type_element in describe.getElementsByTagName("complexType"):
            if type_element.getAttribute("name") == "%sType" % layer:
                for element in type_element.getElementsByTagName("element"):
                    if not element.getAttribute("type").startswith("gml:"):
                        attributes.append(element.getAttribute("name"))
        return attributes
