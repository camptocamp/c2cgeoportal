# -*- coding: utf-8 -*-

# Copyright (c) 2011-2019, Camptocamp SA
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


import subprocess
import os
import yaml
import re
import traceback
import requests
from typing import Dict  # noqa, pylint: disable=unused-import
from json import loads
from urllib.parse import urlsplit
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
from bottle import template, MakoTemplate
from mako.template import Template
from mako.lookup import TemplateLookup
from owslib.wms import WebMapService

import c2cgeoportal_geoportal
from c2c.template.config import config
from c2cgeoportal_geoportal import init_dbsessions
from c2cgeoportal_geoportal.lib import add_url_params, get_url2
from c2cgeoportal_geoportal.lib.bashcolor import colorize, RED
from c2cgeoportal_geoportal.lib.caching import init_region
from c2cgeoportal_geoportal.lib.print_ import *  # noqa


class _Registry:  # pragma: no cover
    settings = None

    def __init__(self, settings):
        self.settings = settings


class _Request:  # pragma: no cover
    registry = None  # type: _Registry
    params = {}  # type: Dict[str, str]
    matchdict = {}  # type: Dict[str, str]
    GET = {}  # type: Dict[str, str]
    user_agent = ""  # type: str

    def __init__(self, settings=None):
        self.registry = _Registry(settings)

    @staticmethod
    def static_url(*args, **kwargs):
        del args
        del kwargs
        return ""

    @staticmethod
    def static_path(*args, **kwargs):
        del args
        del kwargs
        return ""

    @staticmethod
    def route_url(*args, **kwargs):
        del args
        del kwargs
        return ""

    @staticmethod
    def current_route_url(*args, **kwargs):
        del args
        del kwargs
        return ""


class GeomapfishAngularExtractor(Extractor):  # pragma: no cover
    """
    GeoMapFish angular extractor
    """

    extensions = [".js", ".html"]

    def __init__(self):
        super().__init__()
        if os.path.exists("geoportal/config.yaml"):
            config.init("geoportal/config.yaml")
            self.config = config.get_config()
        else:
            self.config = None
        self.tpl = None

    def __call__(self, filename, options):

        init_region({"backend": "dogpile.cache.memory"})

        int_filename = filename
        if re.match("^" + re.escape("./{}/templates".format(self.config["package"])), filename):
            try:
                empty_template = Template("")

                class Lookup(TemplateLookup):
                    @staticmethod
                    def get_template(uri):
                        del uri  # unused
                        return empty_template

                class MyTemplate(MakoTemplate):
                    tpl = None

                    def prepare(self, **kwargs):
                        options.update({"input_encoding": self.encoding})
                        lookup = Lookup(**kwargs)
                        if self.source:
                            self.tpl = Template(self.source, lookup=lookup, **kwargs)
                        else:
                            self.tpl = Template(
                                uri=self.name,
                                filename=self.filename,
                                lookup=lookup, **kwargs)

                try:
                    processed = template(
                        filename,
                        {
                            "request": _Request(self.config),
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
                except Exception:
                    print(colorize(
                        "ERROR! Occurred during the '{}' template generation".format(filename),
                        RED
                    ))
                    print(colorize(traceback.format_exc(), RED))
                    if os.environ.get("IGNORE_I18N_ERRORS", "FALSE") == "TRUE":
                        # Continue with the original one
                        int_filename = filename
                    else:
                        raise
            except Exception:
                print(traceback.format_exc())

        message_str = subprocess.check_output([
            "node", "tools/extract-messages.js", int_filename
        ]).decode("utf-8")
        if int_filename != filename:
            os.unlink(int_filename)
        try:
            messages = []
            for contexts, message in loads(message_str):
                for context in contexts.split(", "):
                    messages.append(Message(
                        None, message, None, [], "", "", context.split(":")
                    ))
            return messages
        except Exception:
            print(colorize("An error occurred", RED))
            print(colorize(message_str, RED))
            print("------")
            raise


class GeomapfishConfigExtractor(Extractor):  # pragma: no cover
    """
    GeoMapFish config extractor (raster layers, and print templates)
    """

    extensions = [".yaml", ".tmpl"]

    def __call__(self, filename, options):
        init_region({"backend": "dogpile.cache.memory"})

        with open(filename) as config_file:
            config = yaml.safe_load(config_file)
            # for application config (config.yaml)
            if "vars" in config:
                return self._collect_app_config(filename)
            # for the print config
            elif "templates" in config:
                return self._collect_print_config(config, filename)
            else:
                raise Exception("Not a known config file")

    def _collect_app_config(self, filename):
        config.init(filename)
        settings = config.get_config()
        # Collect raster layers names
        raster = [
            Message(
                None, raster_layer, None, [], "", "",
                (filename, "raster/{}".format(raster_layer))
            )
            for raster_layer in list(settings.get("raster", {}).keys())
        ]

        # Collect layers enum values (for filters)

        class R:
            settings = None

        class C:
            registry = R()

        config_ = C()
        config_.registry.settings = settings
        init_dbsessions(settings, config_)
        from c2cgeoportal_commons.models import DBSessions
        from c2cgeoportal_commons.models.main import Metadata
        c2cgeoportal_geoportal.init_dbsessions(settings, config_)
        from c2cgeoportal_geoportal.views.layers import Layers
        enums = []
        enum_layers = settings.get("layers", {}).get("enum", {})
        for layername in list(enum_layers.keys()):
            layerinfos = enum_layers.get(layername, {})
            attributes = layerinfos.get("attributes", {})
            for fieldname in list(attributes.keys()):
                values = self._enumerate_attributes_values(DBSessions, Layers, layerinfos, fieldname)
                for value, in values:
                    if value is not None and isinstance(value, str) and value != "":
                        msgid = value
                        location = "/layers/{}/values/{}/{}".format(
                            layername,
                            fieldname,
                            value.encode("ascii", errors="replace") if isinstance(value, str) else value)
                        enums.append(Message(None, msgid, None, [], "", "", (filename, location)))

        metadata_list = []
        defs = config["admin_interface"]["available_metadata"]
        names = [e["name"] for e in defs if e.get("translate", False)]

        if len(names) > 0:
            import sqlalchemy
            engine = sqlalchemy.create_engine(config["sqlalchemy.url"])
            Session = sqlalchemy.orm.session.sessionmaker()  # noqa
            Session.configure(bind=engine)
            session = Session()

            query = session.query(Metadata).filter(Metadata.name.in_(names))
            for metadata in query.all():
                location = "metadata/{}/{}".format(metadata.name, metadata.id)
                metadata_list.append(
                    Message(None, metadata.value, None, [], u"", u"", (filename, location))
                )

        return raster + enums + metadata_list

    @staticmethod
    def _enumerate_attributes_values(dbsessions, layers, layerinfos, fieldname):
        dbname = layerinfos.get("dbsession", "dbsession")
        translate = layerinfos.get("attributes").get(fieldname, {}).get("translate", True)
        if not translate:
            return []
        try:
            dbsession = dbsessions.get(dbname)
            return layers.query_enumerate_attribute_values(dbsession, layerinfos, fieldname)
        except Exception as e:
            table = layerinfos.get("attributes").get(fieldname, {}).get("table")
            print(colorize(
                "ERROR! Unable to collect enumerate attributes for "
                "db: {}, table: {}, column: {} ({})".format(dbname, table, fieldname, e),
                RED
            ))
            if os.environ.get("IGNORE_I18N_ERRORS", "FALSE") == "TRUE":
                return []
            else:
                raise

    @staticmethod
    def _collect_print_config(config, filename):
        result = []
        for template_ in list(config.get("templates").keys()):
            result.append(Message(
                None, template_, None, [], "", "",
                (filename, "template/{}".format(template_))
            ))
            result += [
                Message(
                    None, attribute, None, [], "", "",
                    (filename, "template/{}/{}".format(template_, attribute))
                )
                for attribute in list(config.get("templates")[template_].attributes.keys())
            ]
        return result


class GeomapfishThemeExtractor(Extractor):  # pragma: no cover
    """
    GeoMapFish theme extractor
    """

    # Run on the development.ini file
    extensions = [".ini"]
    featuretype_cache = {}  # type: Dict[str, Dict]
    wmscap_cache = {}  # type: Dict[str, WebMapService]

    def __init__(self):
        super().__init__()
        if os.path.exists("geoportal/config.yaml"):
            config.init("geoportal/config.yaml")
            self.config = config.get_config()
        else:
            self.config = None
        if os.path.exists("project.yaml"):
            with open("project.yaml") as f:
                self.package = yaml.safe_load(f)
        else:
            self.package = None
        self.env = None

    def __call__(self, filename, options):
        messages = []

        try:
            self.env = bootstrap(filename, options=os.environ)

            try:
                from c2cgeoportal_commons.models import DBSession
                from c2cgeoportal_commons.models.main import Theme, LayerGroup, \
                    LayerWMS, LayerWMTS, FullTextSearch

                self._import(Theme, messages)
                self._import(LayerGroup, messages)
                self._import(LayerWMS, messages, self._import_layer_wms)
                self._import(LayerWMTS, messages, self._import_layer_wmts)

                for ln, in DBSession.query(FullTextSearch.layer_name).distinct().all():
                    if ln is not None and ln != "":
                        messages.append(Message(
                            None, ln, None, [], "", "",
                            ("fts", ln.encode("ascii", errors="replace"))
                        ))
            except ProgrammingError as e:
                print(colorize(
                    "ERROR! The database is probably not up to date "
                    "(should be ignored when happen during the upgrade)",
                    RED
                ))
                print(colorize(e, RED))
                if os.environ.get("IGNORE_I18N_ERRORS", "FALSE") != "TRUE":
                    raise
        except NoSuchTableError as e:
            print(colorize(
                "ERROR! The schema didn't seem to exists "
                "(should be ignored when happen during the deploy)",
                RED
            ))
            print(colorize(e, RED))
            if os.environ.get("IGNORE_I18N_ERRORS", "FALSE") != "TRUE":
                raise
        except OperationalError as e:
            print(colorize(
                "ERROR! The database didn't seem to exists "
                "(should be ignored when happen during the deploy)",
                RED
            ))
            print(colorize(e, RED))
            if os.environ.get("IGNORE_I18N_ERRORS", "FALSE") != "TRUE":
                raise

        return messages

    @staticmethod
    def _import(object_type, messages, callback=None):
        from c2cgeoportal_commons.models import DBSession

        items = DBSession.query(object_type)
        for item in items:
            messages.append(Message(
                None, item.name, None, [], "", "",
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
            self._import_layer_attributes(url, wms_layer, layer.item_type, layer.name, messages)
        if layer.geo_table is not None and layer.geo_table != "":
            try:
                from c2cgeoportal_geoportal.views.layers import get_layer_class
                cls = get_layer_class(layer, with_last_update_columns=True)
                for column_property in class_mapper(cls).iterate_properties:
                    if isinstance(column_property, ColumnProperty) and len(column_property.columns) == 1:
                        column = column_property.columns[0]
                        if not column.primary_key and not isinstance(column.type, Geometry):
                            if column.foreign_keys:
                                if column.name == "type_id":
                                    name = "type_"
                                elif column.name.endswith("_id"):
                                    name = column.name[:-3]
                                else:
                                    name = column.name + "_"
                            else:
                                name = column_property.key
                            messages.append(Message(
                                None, name, None, [], "", "",
                                (".".join(["edit", layer.item_type, str(layer.id)]), layer.name)
                            ))
            except NoSuchTableError:
                print(colorize(
                    "ERROR! No such table '{}' for layer '{}'.".format(layer.geo_table, layer.name),
                    RED
                ))
                print(colorize(traceback.format_exc(), RED))
                if os.environ.get("IGNORE_I18N_ERRORS", "FALSE") != "TRUE":
                    raise

    def _import_layer_wmts(self, layer, messages):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import OGCServer

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
                        layer.item_type, layer.name, messages
                    )
                except NoResultFound:
                    print(colorize(
                        "ERROR! the OGC server '{}' from the WMTS layer '{}' does not exist.".format(
                            server[0], layer.name
                        ),
                        RED
                    ))
                    if os.environ.get("IGNORE_I18N_ERRORS", "FALSE") != "TRUE":
                        raise

    def _import_layer_attributes(self, url, layer, item_type, name, messages):
        attributes, layers = self._layer_attributes(url, layer)
        for layer in layers:
            messages.append(Message(
                None, layer, None, [], "", "",
                (".".join([item_type, name]), layer.encode("ascii", "replace"))
            ))
        for attribute in attributes:
            messages.append(Message(
                None, attribute, None, [], "", "",
                (".".join([item_type, name]), layer.encode("ascii", "replace"))
            ))

    def _build_url(self, url):
        url_split = urlsplit(url)
        hostname = url_split.hostname
        host_map = self.config.get('lingua_extractor', {}).get('host_map', {})
        if hostname in host_map:
            map_ = host_map[hostname]
            if 'netloc' in map_:
                url_split = url_split._replace(netloc=map_['netloc'])
            if 'scheme' in map_:
                url_split = url_split._replace(scheme=map_['scheme'])
            kwargs = {'verify': map_['verify']} if 'verify' in map_ else {}
            return url_split.geturl(), map_.get('headers', {}), kwargs
        return url, {}, {}

    def _layer_attributes(self, url, layer):
        errors = set()

        request = _Request()
        request.registry.settings = self.config
        # static schema will not be supported
        url = get_url2("Layer", url, request, errors)
        if len(errors) > 0:
            print("\n".join(errors))
            return [], []
        url, headers, kwargs = self._build_url(url)

        if url not in self.wmscap_cache:
            print("Get WMS GetCapabilities for URL: {}".format(url))
            self.wmscap_cache[url] = None

            wms_getcap_url = add_url_params(url, {
                "SERVICE": "WMS",
                "VERSION": "1.1.1",
                "REQUEST": "GetCapabilities",
            })
            try:
                print("Get WMS GetCapabilities for URL {},\nwith headers: {}".format(
                    wms_getcap_url, " ".join(["=".join(h) for h in headers.items()])
                ))
                response = requests.get(wms_getcap_url, headers=headers, **kwargs)

                try:
                    self.wmscap_cache[url] = WebMapService(None, xml=response.content)
                except Exception as e:
                    print(colorize(
                        "ERROR! an error occurred while trying to "
                        "parse the GetCapabilities document.",
                        RED))
                    print(colorize(str(e), RED))
                    print("URL: {}\nxml:\n{}".format(wms_getcap_url, response.text))
                    if os.environ.get("IGNORE_I18N_ERRORS", "FALSE") != "TRUE":
                        raise
            except Exception as e:  # pragma: no cover
                print(colorize(str(e), RED))
                print(colorize(
                    "ERROR! Unable to GetCapabilities from URL: {},\nwith headers: {}".format(
                        wms_getcap_url, " ".join(["=".join(h) for h in headers.items()])
                    ),
                    RED,
                ))
                if os.environ.get("IGNORE_I18N_ERRORS", "FALSE") != "TRUE":
                    raise

        wmscap = self.wmscap_cache[url]

        if url not in self.featuretype_cache:
            print("Get WFS DescribeFeatureType for URL: {}".format(url))
            self.featuretype_cache[url] = None

            wfs_descrfeat_url = add_url_params(url, {
                "SERVICE": "WFS",
                "VERSION": "1.1.0",
                "REQUEST": "DescribeFeatureType",
            })
            try:
                response = requests.get(wfs_descrfeat_url, headers=headers, **kwargs)
            except Exception as e:  # pragma: no cover
                print(colorize(str(e), RED))
                print(colorize(
                    "ERROR! Unable to DescribeFeatureType from URL: {}".format(wfs_descrfeat_url),
                    RED,
                ))
                if os.environ.get("IGNORE_I18N_ERRORS", "FALSE") == "TRUE":
                    return [], []
                else:
                    raise

            if not response.ok:  # pragma: no cover
                print(colorize(
                    "ERROR! DescribeFeatureType from URL {} return the error: {:d} {}".format(
                        wfs_descrfeat_url, response.status_code, response.reason
                    ),
                    RED,
                ))
                if os.environ.get("IGNORE_I18N_ERRORS", "FALSE") == "TRUE":
                    return [], []
                else:
                    raise Exception("Aborted")

            try:
                describe = parseString(response.text)
                featurestype = {}
                self.featuretype_cache[url] = featurestype
                for type_element in describe.getElementsByTagNameNS(
                    "http://www.w3.org/2001/XMLSchema", "complexType"
                ):
                    featurestype[type_element.getAttribute("name")] = type_element
            except ExpatError as e:
                print(colorize(
                    "ERROR! an error occurred while trying to "
                    "parse the DescribeFeatureType document.",
                    RED
                ))
                print(colorize(str(e), RED))
                print("URL: {}\nxml:\n{}".format(wfs_descrfeat_url, response.text))
                if os.environ.get("IGNORE_I18N_ERRORS", "FALSE") == "TRUE":
                    return [], []
                else:
                    raise
            except AttributeError:
                print(colorize(
                    "ERROR! an error occurred while trying to "
                    "read the Mapfile and recover the themes.",
                    RED
                ))
                print("URL: {}\nxml:\n{}".format(wfs_descrfeat_url, response.text))
                if os.environ.get("IGNORE_I18N_ERRORS", "FALSE") == "TRUE":
                    return [], []
                else:
                    raise
        else:
            featurestype = self.featuretype_cache[url]

        if featurestype is None:
            return [], []

        layers = [layer]
        if wmscap is not None and layer in list(wmscap.contents):
            layer_obj = wmscap[layer]
            if len(layer_obj.layers) > 0:
                layers = [l.name for l in layer_obj.layers]

        attributes = []
        for sub_layer in layers:
            # Should probably be adapted for other king of servers
            type_element = featurestype.get("{}Type".format(sub_layer))
            if type_element is not None:
                for element in type_element.getElementsByTagNameNS(
                    "http://www.w3.org/2001/XMLSchema", "element"
                ):
                    if not element.getAttribute("type").startswith("gml:"):
                        attributes.append(element.getAttribute("name"))

        return attributes, layers
