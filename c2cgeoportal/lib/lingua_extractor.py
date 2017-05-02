# -*- coding: utf-8 -*-

# Copyright (c) 2011-2017, Camptocamp SA
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
import os
import yaml
import re
import traceback
from json import loads
from urlparse import urlsplit
from defusedxml.minidom import parseString
from xml.parsers.expat import ExpatError
from sqlalchemy.exc import ProgrammingError, NoSuchTableError, OperationalError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.util import class_mapper
from sqlalchemy.orm.properties import ColumnProperty
from geoalchemy2.types import Geometry

from lingua.extractors import Extractor
from lingua.extractors import Message
from pyramid.paster import bootstrap
from c2c.template import get_config
from bottle import template, MakoTemplate
from mako.template import Template
from mako.lookup import TemplateLookup
from owslib.wms import WebMapService

from c2cgeoportal.lib import add_url_params, get_url2
from c2cgeoportal.lib.bashcolor import colorize, RED, YELLOW
from c2cgeoportal.lib.dbreflection import get_class
from c2cgeoportal.lib.caching import init_region


class GeoMapfishAngularExtractor(Extractor):  # pragma: no cover
    "GeoMapfish angular extractor"

    extensions = [".js", ".html"]

    def __call__(self, filename, options):
        config = get_config(".build/config.yaml")

        class Registry:
            settings = config

        class Request:
            registry = Registry()
            params = {}
            GET = {}
            user_agent = ""

            @staticmethod
            def static_url(*args, **kwargs):
                return ""

            @staticmethod
            def static_path(*args, **kwargs):
                return ""

            @staticmethod
            def route_url(*args, **kwargs):
                return ""

            @staticmethod
            def current_route_url(*args, **kwargs):
                return ""

        init_region({"backend": "dogpile.cache.memory"})

        int_filename = filename
        if re.match("^" + re.escape("./{}/templates".format(config["package"])), filename):
            try:
                empty_template = Template("")

                class Lookup(TemplateLookup):
                    @staticmethod
                    def get_template(uri):
                        return empty_template

                class MyTemplate(MakoTemplate):
                    def prepare(self, **options):
                        options.update({"input_encoding": self.encoding})
                        lookup = Lookup(**options)
                        if self.source:
                            self.tpl = Template(self.source, lookup=lookup, **options)
                        else:
                            self.tpl = Template(
                                uri=self.name,
                                filename=self.filename,
                                lookup=lookup, **options)

                try:
                    processed = template(
                        filename,
                        {
                            "request": Request(),
                            "lang": "fr",
                            "debug": False,
                            "extra_params": {},
                            "permalink_themes": "",
                            "fulltextsearch_groups": [],
                            "wfs_types": [],
                            "_": lambda x: x,
                        },
                        template_adapter=MyTemplate
                    )
                    int_filename = os.path.join(os.path.dirname(filename), "_" + os.path.basename(filename))
                    with open(int_filename, "wb") as file_open:
                        file_open.write(processed.encode("utf-8"))
                except:
                    print(colorize(
                        u"An error occurred during the '{}' template generation".format(filename),
                        YELLOW
                    ))
                    print(colorize(traceback.format_exc(), YELLOW))
                    print("------")
                    # Continue with the original one
                    int_filename = filename
            except:
                print(traceback.format_exc())

        message_str = subprocess.check_output(["node", "tools/extract-messages.js", int_filename])
        if int_filename != filename:
            os.unlink(int_filename)
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
            from c2cgeoportal.lib.print_ import *  # noqa
            config = yaml.load(config_file)
            # for application config (.build/config.yaml)
            if "vars" in config:
                return self._collect_app_config(config, filename)
            # for the print config
            elif "templates" in config:
                return self._collect_print_config(config, filename)
            else:
                raise Exception("Not a known config file")

    @classmethod
    def _collect_app_config(cls, config, filename):
        # Collect raster layers names
        raster = [
            Message(
                None, raster_layer, None, [], u"", u"",
                (filename, u"raster/{0!s}".format(raster_layer))
            )
            for raster_layer in config["vars"].get("raster", {}).keys()
        ]
        # Collect layers enum values (for filters)
        settings = get_config(".build/config.yaml")
        from c2cgeoportal.pyramid_ import init_dbsessions
        init_dbsessions(settings)
        from c2cgeoportal.models import DBSessions
        from c2cgeoportal.views.layers import Layers
        enums = []
        enum_layers = config["vars"].get("layers", {}).get("enum", {})
        for layername in enum_layers.keys():
            layerinfos = enum_layers.get(layername, {})
            attributes = layerinfos.get("attributes", {})
            for fieldname in attributes.keys():
                values = cls._enumerate_attributes_values(DBSessions, Layers, layerinfos, fieldname)
                enums += [
                    Message(
                        None, value[0], None, [], u"", u"",
                        (filename, u"/layers/{0!s}/values/{1!s}/{2!s}".format(layername, fieldname, value[0]))
                    )
                    for value in values
                ]

        return raster + enums

    @classmethod
    def _enumerate_attributes_values(cls, dbsessions, layers, layerinfos, fieldname):
        dbname = layerinfos.get("dbsession")
        try:
            dbsession = dbsessions.get(dbname)
            return layers.query_enumerate_attribute_values(dbsession, layerinfos, fieldname)
        except:
            table = layerinfos.get("attributes").get(fieldname, {}).get("table")
            print(colorize(
                u"Unable to collect enumerate attributes for "
                u"db: {0!s}, table: {1!s}, column: {2!s}".format(dbname, table, fieldname),
                YELLOW
            ))
            return []

    @classmethod
    def _collect_print_config(cls, config, filename):
        result = []
        for template_ in config.get("templates").keys():
            result.append(Message(
                None, template_, None, [], u"", u"",
                (filename, u"template/{0!s}".format(template_))
            ))
            result += [
                Message(
                    None, attribute, None, [], u"", u"",
                    (filename, u"template/{0!s}/{1!s}".format(template_, attribute))
                )
                for attribute in config.get("templates")[template_].attributes.keys()
            ]
        return result


class GeoMapfishThemeExtractor(Extractor):  # pragma: no cover
    "GeoMapfish theme extractor"

    # Run on the development.ini file
    extensions = [".ini"]
    featuretype_cache = {}
    wmscap_cache = {}

    def __call__(self, filename, options):
        messages = []

        try:
            self.env = bootstrap(filename)
            with open("project.yaml") as f:
                self.package = yaml.safe_load(f)
            self.config = get_config(".build/config.yaml")

            try:
                from c2cgeoportal.models import DBSession, Theme, LayerGroup, \
                    LayerWMS, LayerWMTS, FullTextSearch

                self._import(Theme, messages)
                self._import(LayerGroup, messages)
                self._import(LayerWMS, messages, self._import_layer_wms)
                self._import(LayerWMTS, messages, self._import_layer_wmts)

                for ln, in DBSession.query(FullTextSearch.layer_name).distinct().all():
                    if ln is not None and ln != "":
                        messages.append(Message(
                            None, ln, None, [], u"", u"",
                            ("fts", ln.encode("ascii", errors="replace"))
                        ))
            except ProgrammingError as e:
                print(colorize(
                    "ERROR: The database is probably not up to date "
                    "(should be ignored when happen during the upgrade)",
                    RED
                ))
                print(colorize(e, RED))
        except NoSuchTableError as e:
            print(colorize(
                "ERROR: The schema didn't seem to exists "
                "(should be ignored when happen during the deploy)",
                RED
            ))
            print(colorize(e, RED))
        except OperationalError as e:
            print(colorize(
                "ERROR: The database didn't seem to exists "
                "(should be ignored when happen during the deploy)",
                RED
            ))
            print(colorize(e, RED))

        return messages

    @staticmethod
    def _import(object_type, messages, callback=None):
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
        url = server.url_wfs or server.url
        if url is None:
            return
        for wms_layer in layer.layer.split(","):
            self._import_layer_attributes(
                url, wms_layer, layer.item_type, layer.name, layer.id, messages
            )
        if layer.geo_table is not None and layer.geo_table != "":
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
                print(colorize(
                    u"No such table '{}' for layer '{}'.".format(layer.geo_table, layer.name),
                    YELLOW
                ))
                print(colorize(traceback.format_exc(), YELLOW))

    def _import_layer_wmts(self, layer, messages):
        from c2cgeoportal.models import DBSession, OGCServer

        layers = [d.value for d in layer.metadatas if d.name == "queryLayers"]
        if len(layers) == 0:
            layers = [d.value for d in layer.metadatas if d.name == "wmsLayer"]
        server = [d.value for d in layer.metadatas if d.name == "ogcServer"]
        if len(server) >= 1 and len(layers) >= 1:
            for wms_layer in layers:
                try:
                    db_server = DBSession.query(OGCServer).filter(OGCServer.name == server[0]).one()
                    self._import_layer_attributes(
                        db_server.url_wfs or db_server.url, wms_layer,
                        layer.item_type, layer.name, layer.id, messages
                    )
                except NoResultFound:
                    print(colorize(
                        u"Error: the OGC server '{}' from the WMTS layer '{}' does not exist.".format(
                            server[0], layer.name
                        ),
                        YELLOW
                    ))

    def _import_layer_attributes(self, url, layer, item_type, name, layer_id, messages):
        for attribute in self._layer_attributes(url, layer):
            messages.append(Message(
                None, attribute, None, [], "", "", (".".join([item_type, name]), layer)
            ))

    def _layer_attributes(self, url, layer):
        errors = set()

        class Registry:
            setting = None

        class Request:
            registry = Registry()

        request = Request()
        request.registry.settings = self.config
        # static schema will not be supported
        url = get_url2("Layer", url, request, errors)
        if len(errors) > 0:
            print("\n".join(errors))
            return []

        wms_getcap_url = add_url_params(url, {
            "SERVICE": "WMS",
            "VERSION": "1.1.1",
            "REQUEST": "GetCapabilities",
        })

        hostname = urlsplit(url).hostname
        if url not in self.wmscap_cache:
            print(u"Get WMS GetCapabilities for URL: {}".format(url))
            self.wmscap_cache[url] = None

            # forward request to target (without Host Header)
            http = httplib2.Http()
            h = {}
            if hostname == "localhost":  # pragma: no cover
                h["Host"] = self.package["host"]
            try:
                resp, content = http.request(wms_getcap_url, method="GET", headers=h)

                try:
                    self.wmscap_cache[url] = WebMapService(None, xml=content)
                except Exception as e:
                    print(colorize(
                        "WARNING! an error occurred while trying to "
                        "parse the GetCapabilities document."
                    ), YELLOW)
                    print(colorize(str(e), YELLOW))
                    print(u"URL: {0!s}\nxml:\n{1!s}".format(wms_getcap_url, content))
            except Exception as e:  # pragma: no cover
                print(colorize(str(e), YELLOW))
                print(colorize(
                    u"WARNING! Unable to GetCapabilities from URL: {0!s}".format(wms_getcap_url),
                    YELLOW,
                ))

        wmscap = self.wmscap_cache[url]

        wfs_descrfeat_url = add_url_params(url, {
            "SERVICE": "WFS",
            "VERSION": "1.1.0",
            "REQUEST": "DescribeFeatureType",
        })

        if url not in self.featuretype_cache:
            print(u"Get WFS DescribeFeatureType for URL: {}".format(wfs_descrfeat_url))
            self.featuretype_cache[url] = None

            # forward request to target (without Host Header)
            http = httplib2.Http()
            h = {}
            if hostname == "localhost":  # pragma: no cover
                h["Host"] = self.package["host"]
            try:
                resp, content = http.request(wfs_descrfeat_url, method="GET", headers=h)
            except Exception as e:  # pragma: no cover
                print(colorize(str(e), YELLOW))
                print(colorize(
                    u"Unable to DescribeFeatureType from URL: {0!s}".format(wfs_descrfeat_url),
                    YELLOW,
                ))
                return []

            if resp.status < 200 or resp.status >= 300:  # pragma: no cover
                print(colorize(
                    u"WARNING DescribeFeatureType from URL {0!s} return the error: {1:d} {2!s}".format(
                        wfs_descrfeat_url, resp.status, resp.reason
                    ),
                    YELLOW,
                ))
                return []

            try:
                describe = parseString(content)
                featurestype = {}
                self.featuretype_cache[url] = featurestype
                for type_element in describe.getElementsByTagNameNS(
                    "http://www.w3.org/2001/XMLSchema", "complexType"
                ):
                    featurestype[type_element.getAttribute("name")] = type_element
            except ExpatError as e:
                print(colorize(
                    "WARNING! an error occurred while trying to "
                    "parse the DescribeFeatureType document.",
                    YELLOW
                ))
                print(colorize(str(e), YELLOW))
                print(u"URL: {0!s}\nxml:\n{1!s}".format(wfs_descrfeat_url, content))
            except AttributeError:
                print(colorize(
                    "WARNING! an error occurred while trying to "
                    "read the Mapfile and recover the themes.",
                    YELLOW
                ))
                print(u"URL: {0!s}\nxml:\n{1!s}".format(wfs_descrfeat_url, content))
        else:
            featurestype = self.featuretype_cache[url]

        if featurestype is None:
            return []

        layers = [layer]
        if wmscap is not None and layer in list(wmscap.contents):
            layer_obj = wmscap[layer]
            if len(layer_obj.layers) > 0:
                layers = [l.name for l in layer_obj.layers]

        attributes = []
        for sub_layer in layers:
            # Should probably be adapted for other king of servers
            type_element = featurestype.get(u"{}Type".format(sub_layer))
            if type_element is not None:
                for element in type_element.getElementsByTagNameNS(
                    "http://www.w3.org/2001/XMLSchema", "element"
                ):
                    if not element.getAttribute("type").startswith("gml:"):
                        attributes.append(element.getAttribute("name"))

        return attributes
