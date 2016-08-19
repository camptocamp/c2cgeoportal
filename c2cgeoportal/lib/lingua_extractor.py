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
from sqlalchemy.exc import ProgrammingError, NoSuchTableError
from sqlalchemy.orm.util import class_mapper
from sqlalchemy.orm.properties import ColumnProperty
from geoalchemy2.types import Geometry

from lingua.extractors import Extractor
from lingua.extractors import Message
from pyramid.paster import bootstrap
from c2c.template import get_config

from c2cgeoportal.lib import add_url_params
from c2cgeoportal.lib.print_ import *  # noqa
from c2cgeoportal.lib.bashcolor import colorize, RED
from c2cgeoportal.lib.dbreflection import get_class


class GeoMapfishAngularExtractor(Extractor):  # pragma: no cover
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


class GeoMapfishConfigExtractor(Extractor):  # pragma: no cover
    "GeoMapfish config extractor (raster layers, and print templates)"

    extensions = [".yaml"]

    def __call__(self, filename, options):
        with open(filename) as config_file:
            config = yaml.load(config_file)
            # for application config (.build/config.yaml)
            if "vars" in config:
                return [
                    Message(
                        None, raster_layer, None, [], u"", u"",
                        (filename, u"raster/%s" % raster_layer)
                    )
                    for raster_layer in config["vars"].get("raster", {}).keys()
                ]
            # for the print config
            elif "templates" in config:
                result = []
                for template in config.get("templates").keys():
                    result.append(Message(
                        None, template, None, [], u"", u"",
                        (filename, u"template/%s" % template)
                    ))
                    result += [
                        Message(
                            None, attribute, None, [], u"", u"",
                            (filename, u"template/%s/%s" % (template, attribute))
                        )
                        for attribute in config.get("templates")[template].attributes.keys()
                    ]
                return result
            else:
                raise Exception("Not a known config file")


class GeoMapfishThemeExtractor(Extractor):  # pragma: no cover
    "GeoMapfish theme extractor"

    # Run on the development.ini file
    extensions = [".ini"]
    featuretype_cache = {}

    def __call__(self, filename, options):
        messages = []

        self.env = bootstrap(filename)
        with open("project.yaml") as f:
            self.package = yaml.load(f)
        self.config = get_config(".build/config.yaml")

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
                (item.item_type, item.name.encode("ascii", errors="replace"))
            ))

            if callback is not None:
                callback(item, messages)

    def _import_layer_wms(self, layer, messages):
        server = layer.ogc_server
        url = server.url_wfs or server.url or \
            self.env["registry"].settings["mapserverproxy"]["mapserv_url"]
        for wms_layer in layer.layer.split(","):
            self._import_layer_attributes(
                url, wms_layer, layer.item_type, layer.name, layer.id, messages
            )
        if layer.geo_table is not None:
            exclude = [] if layer.exclude_properties is None else layer.exclude_properties.split(",")
            last_update_date = layer.get_metadatas("lastUpdateDateColumn")
            if len(last_update_date) == 1:
                exclude.append(last_update_date[0].value)
            last_update_user = layer.get_metadatas("lastUpdateUserColumn")
            if len(last_update_user) == 1:
                exclude.append(last_update_user[0].value)
            try:
                cls = get_class(layer.geo_table, exclude_properties=exclude)
                for column_property in class_mapper(cls).iterate_properties:
                    if isinstance(column_property, ColumnProperty) and \
                            len(column_property.columns) == 1 and \
                            not column_property.columns[0].primary_key and \
                            not column_property.columns[0].foreign_keys and \
                            not isinstance(column_property.columns[0].type, Geometry):
                        messages.append(Message(
                            None, column_property.key, None, [], "", "",
                            (".".join(["edit", layer.item_type, str(layer.id)]), layer.name)
                        ))
            except NoSuchTableError:
                exit(colorize("No such table '{}' for layer '{}'.".format(layer.geo_table, layer.name), RED))

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
                print("Unable to DescribeFeatureType from URL %s" % url)
                self.featuretype_cache[url] = None
                return []

            if resp.status < 200 or resp.status >= 300:  # pragma: no cover
                print(
                    "DescribeFeatureType from URL %s return the error: %i %s" %
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
                    "read the Mapfile and recover the themes."
                )
                print("URL: %s\nxml:\n%s" % (url, content))
        else:
            describe = self.featuretype_cache[url]

        if describe is None:
            return []

        attributes = []
        # Should probably be adapted for other king of servers
        for type_element in describe.getElementsByTagNameNS(
            "http://www.w3.org/2001/XMLSchema", "complexType"
        ):
            if type_element.getAttribute("name") == "%sType" % layer:
                for element in type_element.getElementsByTagNameNS(
                    "http://www.w3.org/2001/XMLSchema", "element"
                ):
                    if not element.getAttribute("type").startswith("gml:"):
                        attributes.append(element.getAttribute("name"))
        return attributes
