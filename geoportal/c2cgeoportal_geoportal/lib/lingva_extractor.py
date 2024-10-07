# Copyright (c) 2011-2024, Camptocamp SA
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


import json
import os
import re
import subprocess
import traceback
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Optional, cast
from xml.dom import Node
from xml.parsers.expat import ExpatError

import pyramid.threadlocal
import requests
import sqlalchemy.orm
import yaml
from bottle import MakoTemplate, template
from c2c.template.config import config
from defusedxml.minidom import parseString
from geoalchemy2.types import Geometry
from lingva.extractors import Extractor, Message
from mako.lookup import TemplateLookup
from mako.template import Template
from owslib.wms import WebMapService
from sqlalchemy.exc import NoSuchTableError, OperationalError, ProgrammingError
from sqlalchemy.orm.exc import NoResultFound  # type: ignore[attr-defined]
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.orm.util import class_mapper

import c2cgeoportal_geoportal
from c2cgeoportal_commons.lib.url import Url, get_url2
from c2cgeoportal_geoportal.lib.bashcolor import Color, colorize
from c2cgeoportal_geoportal.lib.caching import init_region
from c2cgeoportal_geoportal.views.layers import Layers, get_layer_class

if TYPE_CHECKING:
    from c2cgeoportal_commons.models import main  # pylint: disable=ungrouped-imports,useless-suppression


class LinguaExtractorException(Exception):
    """Exception raised when an error occurs during the extraction."""


def _get_config(key: str, default: str | None = None) -> str | None:
    """
    Return the config value for passed key.

    Passed throw environment variable for the command line,
    or throw the query string on HTTP request.
    """
    request = pyramid.threadlocal.get_current_request()
    if request is not None:
        return cast(Optional[str], request.params.get(key.lower(), default))

    return os.environ.get(key, default)


def _get_config_str(key: str, default: str) -> str:
    result = _get_config(key, default)
    assert result is not None
    return result


class _Registry:
    settings = None

    def __init__(self, settings: dict[str, Any] | None) -> None:
        self.settings = settings


class _Request:
    params: dict[str, str] = {}
    matchdict: dict[str, str] = {}
    GET: dict[str, str] = {}

    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        self.registry: _Registry = _Registry(settings)

    @staticmethod
    def static_url(*args: Any, **kwargs: Any) -> str:
        del args
        del kwargs
        return ""

    @staticmethod
    def static_path(*args: Any, **kwargs: Any) -> str:
        del args
        del kwargs
        return ""

    @staticmethod
    def route_url(*args: Any, **kwargs: Any) -> str:
        del args
        del kwargs
        return ""

    @staticmethod
    def current_route_url(*args: Any, **kwargs: Any) -> str:
        del args
        del kwargs
        return ""


class GeomapfishAngularExtractor(Extractor):  # type: ignore
    """GeoMapFish angular extractor."""

    extensions = [".js", ".html"]

    def __init__(self) -> None:
        super().__init__()
        if os.path.exists("/etc/geomapfish/config.yaml"):
            config.init("/etc/geomapfish/config.yaml")
            conf = config.get_config()
            assert conf is not None
            self.config = conf
        else:
            self.config = {}
        self.tpl = None

    @staticmethod
    def get_message_cleaner(filename: str) -> Callable[[str], str]:
        """Return a function for cleaning messages according to input file format."""
        ext = os.path.splitext(filename)[1]

        if ext in [".html", ".ejs"]:
            # Remove \n in HTML multi-line strings
            pattern = re.compile("\n *")
            return lambda s: re.sub(pattern, " ", s)

        return lambda s: s

    def __call__(
        self,
        filename: str,
        options: dict[str, Any],
        fileobj: dict[str, Any] | None = None,
        lineno: int = 0,
    ) -> list[Message]:
        del fileobj, lineno

        print(f"Running {self.__class__.__name__} on {filename}")

        cleaner = self.get_message_cleaner(filename)

        init_region({"backend": "dogpile.cache.memory"}, "std")
        init_region({"backend": "dogpile.cache.memory"}, "obj")

        int_filename = filename
        if re.match("^" + re.escape(f"./{self.config['package']}/templates"), filename):
            try:
                empty_template = Template("")  # nosec

                class Lookup(TemplateLookup):  # type: ignore
                    def get_template(self, uri: str) -> Template:
                        del uri  # unused
                        return empty_template

                class MyTemplate(MakoTemplate):  # type: ignore
                    tpl = None

                    def prepare(self, **kwargs: Any) -> None:
                        options.update({"input_encoding": self.encoding})
                        lookup = Lookup(**kwargs)
                        if self.source:
                            self.tpl = Template(self.source, lookup=lookup, **kwargs)  # nosec
                        else:
                            self.tpl = Template(  # nosec
                                uri=self.name, filename=self.filename, lookup=lookup, **kwargs
                            )

                try:
                    request = pyramid.threadlocal.get_current_request()
                    request = _Request() if request is None else request
                    processed = template(
                        filename,
                        {
                            "request": request,
                            "lang": "fr",
                            "debug": False,
                            "extra_params": {},
                            "permalink_themes": "",
                            "fulltextsearch_groups": [],
                            "wfs_types": [],
                            "_": lambda x: x,
                        },
                        template_adapter=MyTemplate,
                    )
                    int_filename = os.path.join(os.path.dirname(filename), "_" + os.path.basename(filename))
                    with open(int_filename, "wb") as file_open:
                        file_open.write(processed.encode("utf-8"))
                except Exception:  # pylint: disable=broad-exception-caught
                    print(colorize(f"ERROR! Occurred during the '{filename}' template generation", Color.RED))
                    print(colorize(traceback.format_exc(), Color.RED))
                    if _get_config_str("IGNORE_I18N_ERRORS", "FALSE") == "TRUE":
                        # Continue with the original one
                        int_filename = filename
                    else:
                        raise
            except Exception:  # pylint: disable=broad-exception-caught
                print(traceback.format_exc())

        # Path in geomapfish-tools
        script_path = "/opt/c2cgeoportal/geoportal/extract-messages.js"
        message_str = subprocess.check_output(["node", script_path, int_filename]).decode("utf-8")
        if int_filename != filename:
            os.unlink(int_filename)
        try:
            messages = []
            for contexts, message in json.loads(message_str):
                assert message is not None
                message = cleaner(message)
                for context in contexts.split(", "):
                    messages.append(Message(None, message, None, [], "", "", context.split(":")))
            return messages
        except Exception:
            print(colorize("An error occurred", Color.RED))
            print(colorize(message_str, Color.RED))
            print("------")
            raise


def init_db(settings: dict[str, Any]) -> None:
    """
    Initialize the SQLAlchemy Session.

    First test the connection, on when environment it should be OK, with the command line we should get
    an exception ind initialize the connection.
    """

    try:
        from c2cgeoportal_commons.models import DBSession  # pylint: disable=import-outside-toplevel
        from c2cgeoportal_commons.models.main import Theme  # pylint: disable=import-outside-toplevel

        assert DBSession is not None

        session = DBSession()
        session.query(Theme).count()
    except:  # pylint: disable=bare-except
        # Init db sessions

        class R:
            settings: dict[str, Any] = {}

        class C:
            registry = R()

            def get_settings(self) -> dict[str, Any]:
                return self.registry.settings

            def add_tween(self, *args: Any, **kwargs: Any) -> None:
                pass

        config_ = C()
        config_.registry.settings = settings

        c2cgeoportal_geoportal.init_db_sessions(settings, config_)


class GeomapfishConfigExtractor(Extractor):  # type: ignore
    """GeoMapFish config extractor (raster layers, and print templates)."""

    extensions = [".yaml", ".tmpl"]

    def __call__(
        self,
        filename: str,
        options: dict[str, Any],
        fileobj: dict[str, Any] | None = None,
        lineno: int = 0,
    ) -> list[Message]:
        del options, fileobj, lineno

        print(f"Running {self.__class__.__name__} on {filename}")

        init_region({"backend": "dogpile.cache.memory"}, "std")
        init_region({"backend": "dogpile.cache.memory"}, "obj")

        with open(filename, encoding="utf8") as config_file:
            gmf_config = yaml.load(config_file, Loader=yaml.BaseLoader)  # nosec
            # For application config (config.yaml)
            if "vars" in gmf_config:
                return self._collect_app_config(filename)
            # For the print config
            if "templates" in gmf_config:
                return self._collect_print_config(gmf_config, filename)
            raise Exception("Not a known config file")  # pylint: disable=broad-exception-raised

    def _collect_app_config(self, filename: str) -> list[Message]:
        config.init(filename)
        settings = config.get_config()
        assert settings is not None
        assert not [
            raster_layer for raster_layer in list(settings.get("raster", {}).keys()) if raster_layer is None
        ]
        # Collect raster layers names
        raster = [
            Message(None, raster_layer, None, [], "", "", (filename, f"raster/{raster_layer}"))
            for raster_layer in list(settings.get("raster", {}).keys())
        ]

        init_db(settings)

        # Collect layers enum values (for filters)

        from c2cgeoportal_commons.models import (  # pylint: disable=import-outside-toplevel
            DBSession,
            DBSessions,
        )
        from c2cgeoportal_commons.models.main import Metadata  # pylint: disable=import-outside-toplevel

        assert DBSession is not None

        enums = []
        enum_layers = settings.get("layers", {}).get("enum", {})
        for layername in list(enum_layers.keys()):
            layerinfos = enum_layers.get(layername, {})
            attributes = layerinfos.get("attributes", {})
            for fieldname in list(attributes.keys()):
                values = self._enumerate_attributes_values(DBSessions, layerinfos, fieldname)
                for (value,) in values:
                    if isinstance(value, str) and value != "":
                        msgid = value
                        location = (
                            f"/layers/{layername}/values/{fieldname}/"
                            f"{value.encode('ascii', errors='replace').decode('ascii')}"
                        )
                        assert msgid is not None
                        enums.append(Message(None, msgid, None, [], "", "", (filename, location)))

        metadata_list = []
        defs = config["admin_interface"]["available_metadata"]  # pylint: disable=unsubscriptable-object
        names = [e["name"] for e in defs if e.get("translate", False)]

        if names:
            session = DBSession()

            query = session.query(Metadata).filter(Metadata.name.in_(names))
            for metadata in query.all():
                location = f"metadata/{metadata.name}/{metadata.id}"
                assert metadata.value is not None
                metadata_list.append(Message(None, metadata.value, None, [], "", "", (filename, location)))

        interfaces_messages = []
        for interface, interface_config in config["interfaces_config"].items():
            for ds_index, datasource in enumerate(
                interface_config.get("constants", {}).get("gmfSearchOptions", {}).get("datasources", [])
            ):
                for a_index, action in enumerate(datasource.get("groupActions", [])):
                    location = (
                        f"interfaces_config/{interface}/constants/gmfSearchOptions/datasources[{ds_index}]/"
                        f"groupActions[{a_index}]/title"
                    )
                    assert action["title"] is not None
                    interfaces_messages.append(
                        Message(None, action["title"], None, [], "", "", (filename, location))
                    )

            for merge_tab in (
                interface_config.get("constants", {})
                .get("gmfDisplayQueryGridOptions", {})
                .get("mergeTabs", {})
                .keys()
            ):
                location = (
                    f"interfaces_config/{interface}/constants/gmfDisplayQueryGridOptions/"
                    f"mergeTabs/{merge_tab}/"
                )
                assert merge_tab is not None
                interfaces_messages.append(Message(None, merge_tab, None, [], "", "", (filename, location)))

        return raster + enums + metadata_list + interfaces_messages

    @staticmethod
    def _enumerate_attributes_values(
        dbsessions: dict[str, sqlalchemy.orm.scoped_session[sqlalchemy.orm.Session]],
        layerinfos: dict[str, Any],
        fieldname: str,
    ) -> set[tuple[str, ...]]:
        dbname = layerinfos.get("dbsession", "dbsession")
        translate = cast(dict[str, Any], layerinfos["attributes"]).get(fieldname, {}).get("translate", True)
        if not translate:
            return set()
        try:
            dbsession = dbsessions.get(dbname)
            assert dbsession is not None
            return Layers.query_enumerate_attribute_values(dbsession, layerinfos, fieldname)
        except Exception as e:
            table = cast(dict[str, Any], layerinfos["attributes"]).get(fieldname, {}).get("table")
            print(
                colorize(
                    "ERROR! Unable to collect enumerate attributes for "
                    f"db: {dbname}, table: {table}, column: {fieldname} ({e!s})",
                    Color.RED,
                )
            )
            if _get_config_str("IGNORE_I18N_ERRORS", "FALSE") == "TRUE":
                return set()
            raise

    @staticmethod
    def _collect_print_config(print_config: dict[str, Any], filename: str) -> list[Message]:
        result = []
        for template_ in list(cast(dict[str, Any], print_config.get("templates")).keys()):
            assert template_ is not None
            result.append(Message(None, template_, None, [], "", "", (filename, f"template/{template_}")))
            assert not [
                attribute
                for attribute in list(print_config["templates"][template_]["attributes"].keys())
                if attribute is None
            ]
            result += [
                Message(
                    None,
                    attribute,
                    None,
                    [],
                    "",
                    "",
                    (filename, f"template/{template_}/{attribute}"),
                )
                for attribute in list(print_config["templates"][template_]["attributes"].keys())
            ]
        return result


class GeomapfishThemeExtractor(Extractor):  # type: ignore
    """GeoMapFish theme extractor."""

    # Run on the development.ini file
    extensions = [".ini"]
    featuretype_cache: dict[str, dict[str, Any] | None] = {}
    wms_capabilities_cache: dict[str, WebMapService] = {}

    def __init__(self) -> None:
        super().__init__()
        if os.path.exists("/etc/geomapfish/config.yaml"):
            config.init("/etc/geomapfish/config.yaml")
            conf = config.get_config()
            assert conf is not None
            self.config = conf
        else:
            self.config = {}
        self.env = None

    def __call__(
        self, filename: str, options: dict[str, Any], fileobj: str | None = None, lineno: int = 0
    ) -> list[Message]:
        del fileobj, lineno

        print(f"Running {self.__class__.__name__} on {filename}")

        messages: list[Message] = []

        try:
            init_db(self.config)
            from c2cgeoportal_commons.models import DBSession  # pylint: disable=import-outside-toplevel

            assert DBSession is not None

            db_session = DBSession()

            try:
                from c2cgeoportal_commons.models.main import (  # pylint: disable=import-outside-toplevel
                    FullTextSearch,
                    LayerGroup,
                    LayerWMS,
                    LayerWMTS,
                    Theme,
                )

                self._import(Theme, messages, name_regex=_get_config_str("THEME_REGEX", ".*"))
                self._import(
                    LayerGroup,
                    messages,
                    name_regex=_get_config_str("GROUP_REGEX", ".*"),
                    has_interfaces=False,
                )
                self._import(
                    LayerWMS,
                    messages,
                    self._import_layer_wms,
                    name_regex=_get_config_str("WMSLAYER_REGEX", ".*"),
                )
                self._import(
                    LayerWMTS,
                    messages,
                    self._import_layer_wmts,
                    name_regex=_get_config_str("WMTSLAYER_REGEX", ".*"),
                )

                for (layer_name,) in db_session.query(FullTextSearch.layer_name).distinct().all():
                    if layer_name is not None and layer_name != "":
                        assert layer_name is not None
                        messages.append(
                            Message(
                                None,
                                layer_name,
                                None,
                                [],
                                "",
                                "",
                                ("fts", layer_name.encode("ascii", errors="replace")),
                            )
                        )

                for (actions,) in db_session.query(FullTextSearch.actions).distinct().all():
                    if actions is not None and actions != "":
                        for action in actions:
                            assert action["data"] is not None
                            messages.append(
                                Message(
                                    None,
                                    action["data"],
                                    None,
                                    [],
                                    "",
                                    "",
                                    ("fts", action["data"].encode("ascii", errors="replace")),
                                )
                            )
            except ProgrammingError as e:
                print(
                    colorize(
                        "ERROR! The database is probably not up to date "
                        "(should be ignored when happen during the upgrade)",
                        Color.RED,
                    )
                )
                print(colorize(str(e), Color.RED))
                if _get_config_str("IGNORE_I18N_ERRORS", "FALSE") != "TRUE":
                    raise
        except NoSuchTableError as e:
            print(
                colorize(
                    "ERROR! The schema didn't seem to exists "
                    "(should be ignored when happen during the deploy)",
                    Color.RED,
                )
            )
            print(colorize(str(e), Color.RED))
            if _get_config_str("IGNORE_I18N_ERRORS", "FALSE") != "TRUE":
                raise
        except OperationalError as e:
            print(
                colorize(
                    "ERROR! The database didn't seem to exists "
                    "(should be ignored when happen during the deploy)",
                    Color.RED,
                )
            )
            print(colorize(str(e), Color.RED))
            if _get_config_str("IGNORE_I18N_ERRORS", "FALSE") != "TRUE":
                raise

        return messages

    @staticmethod
    def _import(
        object_type: type[Any],
        messages: list[str],
        callback: Callable[["main.Layer", list[str]], None] | None = None,
        has_interfaces: bool = True,
        name_regex: str = ".*",
    ) -> None:
        from c2cgeoportal_commons.models import DBSession  # pylint: disable=import-outside-toplevel
        from c2cgeoportal_commons.models.main import Interface  # pylint: disable=import-outside-toplevel

        assert DBSession is not None

        filter_re = re.compile(name_regex)

        query = DBSession.query(object_type)

        interfaces = _get_config("INTERFACES")
        if has_interfaces and interfaces is not None:
            query.join(object_type.interface).filter(Interface.name in interfaces.split("."))  # type: ignore[arg-type]

        for item in query.all():
            assert item.name is not None
            if filter_re.match(item.name):
                messages.append(
                    Message(
                        None,
                        item.name,
                        None,
                        [],
                        "",
                        "",
                        (item.item_type, item.name.encode("ascii", errors="replace")),
                    )
                )

            if callback is not None:
                callback(item, messages)

    def _import_layer_wms(self, layer: "main.Layer", messages: list[str]) -> None:
        server = layer.ogc_server
        url = server.url_wfs or server.url
        if url is None:
            return
        if layer.ogc_server.wfs_support:
            for wms_layer in layer.layer.split(","):
                self._import_layer_attributes(url, wms_layer, layer.item_type, layer.name, messages)
        if layer.geo_table is not None and layer.geo_table != "":
            try:
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
                            assert name is not None
                            messages.append(
                                Message(
                                    None,
                                    name,
                                    None,
                                    [],
                                    "",
                                    "",
                                    (".".join(["edit", layer.item_type, str(layer.id)]), layer.name),
                                )
                            )
            except NoSuchTableError:
                print(
                    colorize(
                        f"ERROR! No such table '{layer.geo_table}' for layer '{layer.name}'.",
                        Color.RED,
                    )
                )
                print(colorize(traceback.format_exc(), Color.RED))
                if _get_config_str("IGNORE_I18N_ERRORS", "FALSE") != "TRUE":
                    raise

    def _import_layer_wmts(self, layer: "main.Layer", messages: list[str]) -> None:
        from c2cgeoportal_commons.models import DBSession  # pylint: disable=import-outside-toplevel
        from c2cgeoportal_commons.models.main import OGCServer  # pylint: disable=import-outside-toplevel

        assert DBSession is not None

        layers = [d.value for d in layer.metadatas if d.name == "queryLayers"]
        if not layers:
            layers = [d.value for d in layer.metadatas if d.name == "wmsLayer"]
        server = [d.value for d in layer.metadatas if d.name == "ogcServer"]
        if server and layers:
            layers = [layer for ls in layers for layer in ls.split(",")]
            for wms_layer in layers:
                try:
                    db_server = DBSession.query(OGCServer).filter(OGCServer.name == server[0]).one()
                    if db_server.wfs_support:
                        self._import_layer_attributes(
                            db_server.url_wfs or db_server.url,
                            wms_layer,
                            layer.item_type,
                            layer.name,
                            messages,
                        )
                except NoResultFound:
                    print(
                        colorize(
                            f"ERROR! the OGC server '{server[0]}' from the "
                            f"WMTS layer '{layer.name}' does not exist.",
                            Color.RED,
                        )
                    )
                    if _get_config_str("IGNORE_I18N_ERRORS", "FALSE") != "TRUE":
                        raise

    def _import_layer_attributes(
        self, url: str, layer: "main.Layer", item_type: str, name: str, messages: list[str]
    ) -> None:
        attributes, layers = self._layer_attributes(url, layer)
        for sub_layer in layers:
            assert sub_layer is not None
            messages.append(
                Message(
                    None,
                    sub_layer,
                    None,
                    [],
                    "",
                    "",
                    (".".join([item_type, name]), sub_layer.encode("ascii", "replace")),
                )
            )
        for attribute in attributes:
            assert attribute is not None
            messages.append(
                Message(
                    None,
                    attribute,
                    None,
                    [],
                    "",
                    "",
                    (".".join([item_type, name]), layer.encode("ascii", "replace")),
                )
            )

    def _build_url(self, url: Url) -> tuple[Url, dict[str, str], dict[str, Any]]:
        hostname = url.hostname
        host_map = self.config.get("lingva_extractor", {}).get("host_map", {})
        if hostname in host_map:
            map_ = host_map[hostname]
            if "netloc" in map_:
                url.netloc = map_["netloc"]
            if "scheme" in map_:
                url.scheme = map_["scheme"]
            kwargs = {"verify": map_["verify"]} if "verify" in map_ else {}
            return url, map_.get("headers", {}), kwargs
        return url, {}, {}

    def _layer_attributes(self, url: str, layer: str) -> tuple[list[str], list[str]]:
        errors: set[str] = set()

        request = pyramid.threadlocal.get_current_request()
        if request is None:
            request = _Request()
            request.registry.settings = self.config

        # Static schema will not be supported
        url_obj_ = get_url2("Layer", url, request, errors)
        if errors:
            print("\n".join(errors))
            return [], []
        if not url_obj_:
            print(f"No URL for: {url}")
            return [], []
        url_obj: Url = url_obj_
        url_obj, headers, kwargs = self._build_url(url_obj)

        if url not in self.wms_capabilities_cache:
            print(f"Get WMS GetCapabilities for URL: {url_obj}")
            self.wms_capabilities_cache[url] = None

            wms_getcap_url = (
                url_obj.clone()
                .add_query(
                    {
                        "SERVICE": "WMS",
                        "VERSION": "1.1.1",
                        "REQUEST": "GetCapabilities",
                        "ROLE_IDS": "0",
                        "USER_ID": "0",
                    }
                )
                .url()
            )
            try:
                rendered_headers = " ".join(
                    [
                        f"{h}={v if h not in ('Authorization', 'Cookies') else '***'}"
                        for h, v in headers.items()
                    ]
                )
                print(f"Get WMS GetCapabilities for URL {wms_getcap_url},\nwith headers: {rendered_headers}")
                response = requests.get(wms_getcap_url, headers=headers, timeout=60, **kwargs)

                if response.ok:
                    try:
                        self.wms_capabilities_cache[url] = WebMapService(None, xml=response.content)
                    except Exception as e:  # pylint: disable=broad-exception-caught
                        print(
                            colorize(
                                "ERROR! an error occurred while trying to parse "
                                "the GetCapabilities document.",
                                Color.RED,
                            )
                        )
                        print(colorize(str(e), Color.RED))
                        print(f"URL: {wms_getcap_url}\nxml:\n{response.text}")
                        if _get_config_str("IGNORE_I18N_ERRORS", "FALSE") != "TRUE":
                            raise
                else:
                    print(
                        colorize(
                            f"ERROR! Unable to GetCapabilities from URL: {wms_getcap_url},\n"
                            f"with headers: {rendered_headers}",
                            Color.RED,
                        )
                    )
                    print(f"Response: {response.status_code} {response.reason}\n{response.text}")
                    if _get_config_str("IGNORE_I18N_ERRORS", "FALSE") != "TRUE":
                        raise LinguaExtractorException(response.reason)
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(colorize(str(e), Color.RED))
                rendered_headers = " ".join(
                    [
                        f"{h}={v if h not in ('Authorization', 'Cookies') else '***'}"
                        for h, v in headers.items()
                    ]
                )
                print(
                    colorize(
                        f"ERROR! Unable to GetCapabilities from URL: {wms_getcap_url},\n"
                        f"with headers: {rendered_headers}",
                        Color.RED,
                    )
                )
                if _get_config_str("IGNORE_I18N_ERRORS", "FALSE") != "TRUE":
                    raise

        wms_capabilities = self.wms_capabilities_cache[url]

        if url not in self.featuretype_cache:
            print(f"Get WFS DescribeFeatureType for URL: {url_obj}")
            self.featuretype_cache[url] = None

            wfs_describe_feature_url = (
                url_obj.clone()
                .add_query(
                    {
                        "SERVICE": "WFS",
                        "VERSION": "1.1.0",
                        "REQUEST": "DescribeFeatureType",
                        "ROLE_IDS": "0",
                        "USER_ID": "0",
                    }
                )
                .url()
            )
            try:
                response = requests.get(wfs_describe_feature_url, headers=headers, timeout=60, **kwargs)
            except Exception as e:
                print(colorize(str(e), Color.RED))
                print(
                    colorize(
                        f"ERROR! Unable to DescribeFeatureType from URL: {wfs_describe_feature_url}",
                        Color.RED,
                    )
                )
                if _get_config_str("IGNORE_I18N_ERRORS", "FALSE") == "TRUE":
                    return [], []
                raise

            if not response.ok:
                print(
                    colorize(
                        f"ERROR! DescribeFeatureType from URL {wfs_describe_feature_url} return the error: "
                        f"{response.status_code:d} {response.reason}",
                        Color.RED,
                    )
                )
                if _get_config_str("IGNORE_I18N_ERRORS", "FALSE") == "TRUE":
                    return [], []
                raise Exception("Aborted")  # pylint: disable=broad-exception-raised

            try:
                describe = parseString(response.text)
                featurestype: dict[str, Node] | None = {}
                self.featuretype_cache[url] = featurestype
                for type_element in describe.getElementsByTagNameNS(
                    "http://www.w3.org/2001/XMLSchema", "complexType"
                ):
                    cast(dict[str, Node], featurestype)[type_element.getAttribute("name")] = type_element
            except ExpatError as e:
                print(
                    colorize(
                        "ERROR! an error occurred while trying to parse the DescribeFeatureType document.",
                        Color.RED,
                    )
                )
                print(colorize(str(e), Color.RED))
                print(f"URL: {wfs_describe_feature_url}\nxml:\n{response.text}")
                if _get_config_str("IGNORE_I18N_ERRORS", "FALSE") == "TRUE":
                    return [], []
                raise
            except AttributeError:
                print(
                    colorize(
                        "ERROR! an error occurred while trying to "
                        "read the Mapfile and recover the themes.",
                        Color.RED,
                    )
                )
                print(f"URL: {wfs_describe_feature_url}\nxml:\n{response.text}")
                if _get_config_str("IGNORE_I18N_ERRORS", "FALSE") == "TRUE":
                    return [], []
                raise
        else:
            featurestype = self.featuretype_cache[url]

        if featurestype is None:
            return [], []

        layers: list[str] = [layer]
        if wms_capabilities is not None and layer in list(wms_capabilities.contents):
            layer_obj = wms_capabilities[layer]
            if layer_obj.layers:
                layers = [layer.name for layer in layer_obj.layers]

        attributes: list[str] = []
        for sub_layer in layers:
            # Should probably be adapted for other king of servers
            type_element = featurestype.get(f"{sub_layer}Type")
            if type_element is not None:
                for element in type_element.getElementsByTagNameNS(
                    "http://www.w3.org/2001/XMLSchema", "element"
                ):
                    if not element.getAttribute("type").startswith("gml:"):
                        attributes.append(element.getAttribute("name"))

        return attributes, layers
