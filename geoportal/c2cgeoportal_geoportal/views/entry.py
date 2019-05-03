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


import json
import logging
import re
import sys
import urllib.parse
import xml.dom.minidom  # noqa # pylint: disable=unused-import
from collections import Counter
from math import sqrt
from random import Random
from typing import Dict, Set, Tuple  # noqa # pylint: disable=unused-import

import requests
import zope.event.classhandler
from c2cwsgiutils.auth import auth_view
from defusedxml import lxml
from owslib.wms import WebMapService
from pyramid.httpexceptions import HTTPBadRequest, HTTPForbidden, HTTPFound, HTTPUnauthorized
from pyramid.i18n import TranslationStringFactory
from pyramid.path import AssetResolver
from pyramid.response import Response
from pyramid.security import remember, forget
from pyramid.view import view_config
from sqlalchemy.orm import subqueryload
from sqlalchemy.orm.exc import NoResultFound

from c2cgeoportal_commons import models
from c2cgeoportal_commons.lib.email_ import send_email_config
from c2cgeoportal_commons.models import main, static
from c2cgeoportal_geoportal import is_valid_referer
from c2cgeoportal_geoportal.lib import add_url_params, get_setting, get_typed, get_types_map, get_url2
from c2cgeoportal_geoportal.lib.caching import (
    NO_CACHE, PRIVATE_CACHE, PUBLIC_CACHE, get_region, set_common_headers)
from c2cgeoportal_geoportal.lib.functionality import get_functionality, get_mapserver_substitution_params
from c2cgeoportal_geoportal.lib.layers import get_protected_layers_query
from c2cgeoportal_geoportal.lib.wmstparsing import TimeInformation, parse_extent
from c2cgeoportal_geoportal.views.layers import get_layer_metadatas

_ = TranslationStringFactory("c2cgeoportal")
LOG = logging.getLogger(__name__)
CACHE_REGION = get_region()


class DimensionInformation:

    URL_PART_RE = re.compile(r"[a-zA-Z0-9_\-\+~\.]*$")

    def __init__(self):
        self._dimensions = {}
        self._dimension_filters = {}

    def merge(self, layer, layer_node, mixed):
        errors = set()

        dimensions = {}
        dimensions_filters = {}
        for dimension in layer.dimensions:
            if not isinstance(layer, main.LayerWMS) and dimension.value is not None and \
                    not self.URL_PART_RE.match(dimension.value):
                errors.add(u"The layer '{}' has an unsupported dimension value '{}' ('{}').".format(
                    layer.name, dimension.value, dimension.name
                ))
            elif dimension.name in dimensions:  # pragma: nocover
                errors.add("The layer '{}' has a duplicated dimension name '{}'.".format(
                    layer.name, dimension.name
                ))
            else:
                if dimension.field:
                    dimensions_filters[dimension.name] = {
                        'field': dimension.field,
                        'value': dimension.value
                    }
                else:
                    dimensions[dimension.name] = dimension.value

        if dimensions_filters:
            layer_node["dimensionsFilters"] = dimensions_filters
        if mixed:
            layer_node["dimensions"] = dimensions
        else:
            for name, value in list(dimensions.items()):
                if name not in self._dimensions or self._dimensions[name] is None:
                    self._dimensions[name] = value
                elif self._dimensions[name] != value and value is not None:
                    errors.add(
                        "The layer '{}' has a wrong dimension value '{}' for '{}', "
                        "expected '{}' or empty.".format(
                            layer.name, value, name, self._dimensions[name]
                        )
                    )
        return errors

    def get_dimensions(self):
        return self._dimensions


class Entry:

    WFS_NS = "http://www.opengis.net/wfs"
    server_wms_capabilities = {}  # type: Dict[int, Tuple[WebMapService, Set[str]]]
    server_wfs_feature_type = {}  # type: Dict[int, xml.dom.minidom.Document]

    def __init__(self, request):
        self.request = request
        self.settings = request.registry.settings
        self.http_options = self.request.registry.settings.get("http_options", {})
        self.debug = "debug" in request.params
        self.lang = request.locale_name
        self.metadata_type = get_types_map(
            self.settings.get("admin_interface", {}).get("available_metadata", [])
        )
        self._layerswms_cache = None
        self._layerswmts_cache = None
        self._layergroup_cache = None
        self._themes_cache = None

        from c2cgeoportal_commons.models.main import InvalidateCacheEvent

        @zope.event.classhandler.handler(InvalidateCacheEvent)
        def handle(event: InvalidateCacheEvent):  # pylint: disable=unused-variable
            del event
            Entry.server_wms_capabilities = {}
            Entry.server_wfs_feature_type = {}

    @view_config(route_name="testi18n", renderer="testi18n.html")
    def testi18n(self):  # pragma: no cover
        _ = self.request.translate
        return {"title": _("title i18n")}

    def _get_capabilities_cache_role_key(self, ogc_server):
        return self._get_role_ids() if (
            ogc_server.auth != main.OGCSERVER_AUTH_NOAUTH
            and ogc_server.type != main.OGCSERVER_TYPE_MAPSERVER
        ) else None

    def _get_metadata(self, item, metadata, errors):
        metadatas = item.get_metadatas(metadata)
        return \
            None if len(metadatas) == 0 \
            else get_typed(
                metadata, metadatas[0].value,
                self.metadata_type, self.request, errors,
                layer_name=item.name
            )

    def _get_metadatas(self, item, errors):
        metadatas = {}
        for metadata in item.metadatas:
            value = get_typed(
                metadata.name, metadata.value,
                self.metadata_type, self.request, errors
            )
            if value is not None:
                metadatas[metadata.name] = value

        return metadatas

    def _wms_getcap(self, ogc_server):
        if ogc_server.id in self.server_wms_capabilities:
            return self.server_wms_capabilities[ogc_server.id]

        url, content, errors = self._wms_getcap_cached(
            ogc_server, self._get_capabilities_cache_role_key(ogc_server)
        )

        if len(errors) != 0:
            return None, errors

        wms = None
        try:
            wms = WebMapService(None, xml=content)
        except Exception:  # pragma: no cover
            error = "WARNING! an error occurred while trying to read the mapfile and recover the themes." \
                "\nURL: {}\n{}".format(url, content)
            errors.add(error)
            LOG.error(error, exc_info=True)

        self.server_wms_capabilities[ogc_server.id] = (wms, errors)

        return wms, errors

    @CACHE_REGION.cache_on_arguments()
    def get_http_cached(self, url, headers):
        return requests.get(url, headers=headers, **self.http_options)

    @CACHE_REGION.cache_on_arguments()
    def _wms_getcap_cached(self, ogc_server, _):
        """ _ is just for cache on the role id """

        errors = set()
        url = get_url2(
            "The OGC server '{}'".format(ogc_server.name),
            ogc_server.url, self.request, errors
        )
        if len(errors):  # pragma: no cover
            return url, None, errors

        # Add functionality params
        sparams = get_mapserver_substitution_params(self.request)
        url = add_url_params(url, sparams)

        errors = set()

        url = add_url_params(url, {
            "SERVICE": "WMS",
            "VERSION": "1.1.1",
            "REQUEST": "GetCapabilities",
            "ROLE_ID": "0",
            "USER_ID": "0",
        })

        LOG.info("Get WMS GetCapabilities for url: %s", url)

        # Forward request to target (without Host Header)
        headers = dict(self.request.headers)

        # Add headers for Geoserver
        if ogc_server.auth == main.OGCSERVER_AUTH_GEOSERVER and self.request.user is not None:
            headers["sec-username"] = self.request.user.username
            headers["sec-roles"] = "" if self.request.user is None else \
                ";".join([role.name for role in self.request.user.roles])

        if urllib.parse.urlsplit(url).hostname != "localhost" and "Host" in headers:  # pragma: no cover
            headers.pop("Host")

        try:
            response = self.get_http_cached(url, headers)
        except Exception:  # pragma: no cover
            error = "Unable to GetCapabilities from URL {}".format(url)
            errors.add(error)
            LOG.error(error, exc_info=True)
            return url, None, errors

        if not response.ok:  # pragma: no cover
            error = "GetCapabilities from URL {} return the error: {:d} {}".format(
                url, response.status_code, response.reason
            )
            errors.add(error)
            LOG.error(error)
            return url, None, errors

        # With wms 1.3 it returns text/xml also in case of error :-(
        if response.headers["Content-Type"].split(";")[0].strip() not in \
                ["application/vnd.ogc.wms_xml", "text/xml"]:
            error = "GetCapabilities from URL {} returns a wrong Content-Type: {}\n{}".format(
                url, response.headers["Content-Type"], response.text
            )
            errors.add(error)
            LOG.error(error)
            return url, None, errors

        return url, response.content, errors

    def _create_layer_query(self, interface):
        """
        Create an SQLAlchemy query for Layer and for the role
        identified to by ``role_id``.
        """

        query = models.DBSession.query(main.Layer.name).filter(main.Layer.public.is_(True))

        if interface is not None:
            query = query.join(main.Layer.interfaces)
            query = query.filter(main.Interface.name == interface)

        if self.request.user is not None:
            query2 = get_protected_layers_query(self.request.user, None, what=main.LayerWMS.name)
            if interface is not None:
                query2 = query2.join(main.Layer.interfaces)
                query2 = query2.filter(main.Interface.name == interface)
            query = query.union(query2)
            query3 = get_protected_layers_query(self.request.user, None, what=main.LayerWMTS.name)
            if interface is not None:
                query3 = query3.join(main.Layer.interfaces)
                query3 = query3.filter(main.Interface.name == interface)
            query = query.union(query3)

        return query

    def _get_layer_metadata_urls(self, layer):
        metadata_urls = []
        if len(layer.metadataUrls) > 0:
            metadata_urls = layer.metadataUrls
        for child_layer in layer.layers:
            metadata_urls.extend(self._get_layer_metadata_urls(child_layer))
        return metadata_urls

    def _get_layer_resolution_hint_raw(self, layer):
        resolution_hint_min = None
        resolution_hint_max = None
        if layer.scaleHint:
            # scaleHint is based upon a pixel diagonal length whereas we use
            # resolutions based upon a pixel edge length. There is a sqrt(2)
            # ratio between edge and diagonal of a square.
            resolution_hint_min = float(layer.scaleHint["min"]) / sqrt(2)
            resolution_hint_max = float(layer.scaleHint["max"]) / sqrt(2) \
                if layer.scaleHint["max"] != "0" else 999999999
        for child_layer in layer.layers:
            resolution = self._get_layer_resolution_hint_raw(child_layer)
            resolution_hint_min = resolution[0] if resolution_hint_min is None else (
                resolution_hint_min if resolution[0] is None else
                min(resolution_hint_min, resolution[0])
            )
            resolution_hint_max = resolution[1] if resolution_hint_max is None else (
                resolution_hint_max if resolution[1] is None else
                max(resolution_hint_max, resolution[1])
            )

        return (resolution_hint_min, resolution_hint_max)

    def _get_layer_resolution_hint(self, layer):
        resolution_hint_min, resolution_hint_max = self._get_layer_resolution_hint_raw(layer)
        return (
            0.0 if resolution_hint_min is None else resolution_hint_min,
            999999999 if resolution_hint_max is None else resolution_hint_max,
        )

    def _get_child_layers_info_1(self, layer):
        """ Return information about sub layers of a layer.

            Arguments:

            * ``layer`` The layer object in the WMS capabilities.
        """
        child_layers_info = []
        for child_layer in layer.layers:
            resolution = self._get_layer_resolution_hint(child_layer)
            child_layer_info = {
                "name": child_layer.name,
                "minResolutionHint": float("{:0.2f}".format(resolution[0])),
                "maxResolutionHint": float("{:0.2f}".format(resolution[1])),
            }
            if hasattr(child_layer, "queryable"):
                child_layer_info["queryable"] = child_layer.queryable
            child_layers_info.append(child_layer_info)
        return child_layers_info

    def _get_child_layers_info(self, layer):
        """ Return information about sub layers of a layer.

            Arguments:

            * ``layer`` The layer object in the WMS capabilities.
        """
        resolution = self._get_layer_resolution_hint(layer)
        layer_info = {
            "name": layer.name,
            "minResolutionHint": float("{:0.2f}".format(resolution[0])),
            "maxResolutionHint": float("{:0.2f}".format(resolution[1])),
        }
        layer_info["queryable"] = layer.queryable == 1 \
            if hasattr(layer, "queryable") else True
        return layer_info

    def _layer(self, layer, time=None, dim=None, mixed=True):
        errors = set()
        layer_info = {
            "id": layer.id,
            "name": layer.name,
            "metadata": self._get_metadatas(layer, errors),
        }
        if re.search("[/?#]", layer.name):  # pragma: no cover
            errors.add("The layer has an unsupported name '{}'.".format(layer.name))
        if isinstance(layer, main.LayerWMS) and re.search("[/?#]", layer.layer):  # pragma: no cover
            errors.add("The layer has an unsupported layers '{}'.".format(layer.layer))
        if layer.geo_table:
            errors |= self._fill_editable(layer_info, layer)
        if mixed:
            assert time is None
            time = TimeInformation()
        assert time is not None

        errors |= dim.merge(layer, layer_info, mixed)

        if isinstance(layer, main.LayerWMS):
            wms, wms_layers, wms_errors = self._wms_layers(layer.ogc_server)
            errors |= wms_errors
            if layer.layer is None or layer.layer == "":
                errors.add("The layer '{}' do not have any layers".format(layer.name))
                return None, errors
            layer_info["type"] = "WMS"
            layer_info["layers"] = layer.layer
            self._fill_wms(layer_info, layer, errors, mixed=mixed)
            errors |= self._merge_time(time, layer_info, layer, wms, wms_layers)

        elif isinstance(layer, main.LayerWMTS):
            layer_info["type"] = "WMTS"
            self._fill_wmts(layer_info, layer, errors)

        return layer_info, errors

    @staticmethod
    def _merge_time(time, l, layer, wms, wms_layers):
        errors = set()
        wmslayer = layer.layer
        try:
            if wmslayer in wms_layers:
                wms_layer_obj = wms[wmslayer]

                if wms_layer_obj.timepositions:
                    extent = parse_extent(
                        wms_layer_obj.timepositions,
                        wms_layer_obj.defaulttimeposition
                    )
                    time.merge(l, extent, layer.time_mode, layer.time_widget)

                for child_layer in wms_layer_obj.layers:
                    if child_layer.timepositions:
                        extent = parse_extent(
                            child_layer.timepositions,
                            child_layer.defaulttimeposition
                        )
                        # The time mode comes from the layer group
                        time.merge(l, extent, layer.time_mode, layer.time_widget)

        except ValueError:  # pragma no cover
            errors.add(
                "Error while handling time for layer '{}': {}".format(layer.name, sys.exc_info()[1])
            )

        return errors

    def _fill_editable(self, l, layer):
        errors = set()
        try:
            if self.request.user:
                count = models.DBSession.query(main.RestrictionArea) \
                    .join(main.RestrictionArea.roles) \
                    .filter(main.Role.id.in_([r.id for r in self.request.user.roles])) \
                    .filter(main.RestrictionArea.layers.any(main.Layer.id == layer.id)) \
                    .filter(main.RestrictionArea.readwrite.is_(True)) \
                    .count()
                if count > 0:
                    l["edit_columns"] = get_layer_metadatas(layer)
                    l["editable"] = True
        except Exception as exception:
            LOG.exception(str(exception))
            errors.add(str(exception))
        return errors

    def _fill_wms(self, l, layer, errors, mixed):
        wms, wms_layers, wms_errors = self._wms_layers(layer.ogc_server)
        errors |= wms_errors

        l["imageType"] = layer.ogc_server.image_type
        if layer.style:  # pragma: no cover
            l["style"] = layer.style

        # now look at what is in the WMS capabilities doc
        l["childLayers"] = []
        for layer_name in layer.layer.split(","):
            if layer_name in wms_layers:
                wms_layer_obj = wms[layer_name]
                if len(wms_layer_obj.layers) == 0:
                    l["childLayers"].append(self._get_child_layers_info(wms_layer_obj))
                else:
                    for child_layer in wms_layer_obj.layers:
                        l["childLayers"].append(self._get_child_layers_info(child_layer))
            else:
                errors.add(
                    "The layer '{}' ({}) is not defined in WMS capabilities from '{}'".format(
                        layer_name, layer.name, layer.ogc_server.name
                    )
                )

        if "minResolutionHint" not in l:
            resolution_min = self._get_metadata(layer, "minResolution", errors)

            if resolution_min is not None:
                l["minResolutionHint"] = resolution_min
            else:
                min_resolutions_hint = [
                    l_["minResolutionHint"]
                    for l_ in l["childLayers"]
                    if "minResolutionHint" in l_
                ]
                if len(min_resolutions_hint) > 0:
                    l["minResolutionHint"] = min(min_resolutions_hint)
        if "maxResolutionHint" not in l:
            resolution_max = self._get_metadata(layer, "maxResolution", errors)

            if resolution_max is not None:
                l["maxResolutionHint"] = resolution_max
            else:
                max_resolutions_hint = [
                    l_["maxResolutionHint"]
                    for l_ in l["childLayers"]
                    if "maxResolutionHint" in l_
                ]
                if len(max_resolutions_hint) > 0:
                    l["maxResolutionHint"] = max(max_resolutions_hint)

        if mixed:
            l["ogcServer"] = layer.ogc_server.name

    @staticmethod
    def _fill_legend_rule_query_string(l, layer, url):
        if layer.legend_rule and url:
            l["icon"] = add_url_params(url, {
                "SERVICE": "WMS",
                "VERSION": "1.1.1",
                "REQUEST": "GetLegendGraphic",
                "LAYER": layer.name,
                "FORMAT": "image/png",
                "TRANSPARENT": "TRUE",
                "RULE": layer.legend_rule,
            })

    def _fill_wmts(self, l, layer, errors):
        l["url"] = get_url2(
            "The WMTS layer '{}'".format(layer.name),
            layer.url, self.request, errors=errors
        )

        if layer.style:
            l["style"] = layer.style
        if layer.matrix_set:
            l["matrixSet"] = layer.matrix_set

        l["layer"] = layer.layer
        l["imageType"] = layer.image_type

    @staticmethod
    def _layer_included(tree_item):
        return isinstance(tree_item, main.Layer)

    def _get_ogc_servers(self, group, depth):
        """ Recurse on all children to get unique identifier for each child. """
        ogc_servers = set()

        # escape loop
        if depth > 30:
            LOG.error("Error: too many recursions with group '%s'", group.name)
            return ogc_servers

        # recurse on children
        if isinstance(group, main.LayerGroup) and len(group.children) > 0:
            for tree_item in group.children:
                ogc_servers.update(self._get_ogc_servers(tree_item, depth + 1))

        if isinstance(group, main.LayerWMS):
            ogc_servers.add(group.ogc_server.name)

        if isinstance(group, main.LayerWMTS):
            ogc_servers.add(False)

        return ogc_servers

    def _group(
        self, path, group, layers, depth=1, min_levels=1, mixed=True, time=None,
        dim=None, wms_layers=None, layers_name=None, **kwargs
    ):
        if wms_layers is None:
            wms_layers = []
        if layers_name is None:
            layers_name = []
        children = []
        errors = set()

        if re.search("[/?#]", group.name):  # pragma: no cover
            errors.add("The group has an unsupported name '{}'.".format(group.name))

        # escape loop
        if depth > 30:
            errors.add(
                "Too many recursions with group '{}'".format(group.name)
            )
            return None, errors

        ogc_servers = None
        org_depth = depth
        if depth == 1:
            ogc_servers = list(self._get_ogc_servers(group, 1))
            # check if mixed content
            mixed = len(ogc_servers) != 1 or ogc_servers[0] is False
            if not mixed:
                time = TimeInformation()
            dim = DimensionInformation()

        for tree_item in group.children:
            if isinstance(tree_item, main.LayerGroup):
                gp, gp_errors = self._group(
                    u"{}/{}".format(path, tree_item.name), tree_item, layers,
                    depth=depth + 1, min_levels=min_levels,
                    mixed=mixed, time=time, dim=dim, wms_layers=wms_layers, layers_name=layers_name, **kwargs
                )
                errors |= gp_errors
                if gp is not None:
                    children.append(gp)
            elif self._layer_included(tree_item):
                if tree_item.name in layers:
                    layers_name.append(tree_item.name)
                    if isinstance(tree_item, main.LayerWMS):
                        wms_layers.extend(tree_item.layer.split(","))

                    l, l_errors = self._layer(tree_item, mixed=mixed, time=time, dim=dim, **kwargs)
                    errors |= l_errors
                    if l is not None:
                        if depth < min_levels:
                            errors.add("The Layer '{}' is under indented ({:d}/{:d}).".format(
                                path + "/" + tree_item.name, depth, min_levels
                            ))
                        else:
                            children.append(l)

        if len(children) > 0:
            g = {
                "id": group.id,
                "name": group.name,
                "children": children,
                "metadata": self._get_metadatas(group, errors),
                "mixed": False,
            }
            if not mixed:
                for name, nb in list(Counter(layers_name).items()):
                    if nb > 1:
                        errors.add(
                            "The GeoMapFish layer name '{}', cannot be two times "
                            "in the same block (first level group).".format(name)
                        )

            g["mixed"] = mixed
            if org_depth == 1:
                if not mixed:
                    g["ogcServer"] = ogc_servers[0]
                    if time.has_time() and time.layer is None:
                        g["time"] = time.to_dict()

                    g["dimensions"] = dim.get_dimensions()

            return g, errors
        else:
            return None, errors

    def _layers(self, interface):
        query = self._create_layer_query(interface=interface)
        return [name for (name,) in query.all()]

    def _wms_layers(self, ogc_server):
        # retrieve layers metadata via GetCapabilities
        wms, wms_errors = self._wms_getcap(ogc_server)
        if len(wms_errors) > 0:
            return None, [], wms_errors

        return wms, list(wms.contents), wms_errors

    def _load_tree_items(self):
        self._layerswms_cache = models.DBSession.query(main.LayerWMS).options(
            subqueryload(main.LayerWMS.dimensions), subqueryload(main.LayerWMS.metadatas)
        ).all()
        self._layerswmts_cache = models.DBSession.query(main.LayerWMTS).options(
            subqueryload(main.LayerWMTS.dimensions), subqueryload(main.LayerWMTS.metadatas)
        ).all()
        self._layergroup_cache = models.DBSession.query(main.LayerGroup).options(
            subqueryload(main.LayerGroup.metadatas), subqueryload(main.LayerGroup.children_relation)
        ).all()
        self._themes_cache = models.DBSession.query(main.Theme).options(
            subqueryload(main.Theme.functionalities),
            subqueryload(main.Theme.metadatas),
            subqueryload(main.Theme.children_relation)
        ).all()

    def _themes(self, interface="desktop", filter_themes=True, min_levels=1):
        """
        This function returns theme information for the role identified
        by ``role_id``.
        """
        self._load_tree_items()
        errors = set()
        layers = self._layers(interface)

        themes = models.DBSession.query(main.Theme)
        themes = themes.filter(main.Theme.public.is_(True))
        if self.request.user is not None:
            auth_themes = models.DBSession.query(main.Theme)
            auth_themes = auth_themes.filter(main.Theme.public.is_(False))
            auth_themes = auth_themes.join(main.Theme.restricted_roles)
            auth_themes = auth_themes.filter(main.Role.id.in_([r.id for r in self.request.user.roles]))

            themes = themes.union(auth_themes)

        themes = themes.order_by(main.Theme.ordering.asc())

        if filter_themes and interface is not None:
            themes = themes.join(main.Theme.interfaces)
            themes = themes.filter(main.Interface.name == interface)

        export_themes = []
        for theme in themes.all():
            if re.search("[/?#]", theme.name):
                errors.add("The theme has an unsupported name '{}'.".format(theme.name))
                continue

            children, children_errors = self._get_children(theme, layers, min_levels)
            errors |= children_errors

            # test if the theme is visible for the current user
            if len(children) > 0:
                icon = get_url2(
                    "The Theme '{}'".format(theme.name),
                    theme.icon, self.request, errors,
                ) if theme.icon is not None and len(theme.icon) > 0 else self.request.static_url(
                    "{}_geoportal:static/images/blank.png".format(self.request.registry.settings["package"])
                )

                t = {
                    "id": theme.id,
                    "name": theme.name,
                    "icon": icon,
                    "children": children,
                    "functionalities": self._get_functionalities(theme),
                    "metadata": self._get_metadatas(theme, errors),
                }
                export_themes.append(t)

        return export_themes, errors

    @staticmethod
    def _get_functionalities(theme):
        result = {}
        for functionality in theme.functionalities:
            if functionality.name in result:
                result[functionality.name].append(functionality.value)
            else:
                result[functionality.name] = [functionality.value]
        return result

    @view_config(route_name="invalidate", renderer="json")
    def invalidate_cache(self):  # pragma: no cover
        auth_view(self.request)
        main.cache_invalidate_cb()
        return {
            "success": True
        }

    def _get_children(self, theme, layers, min_levels):
        children = []
        errors = set()
        for item in theme.children:
            if isinstance(item, main.LayerGroup):
                gp, gp_errors = self._group(
                    "{}/{}".format(theme.name, item.name), item, layers, min_levels=min_levels
                )
                errors |= gp_errors
                if gp is not None:
                    children.append(gp)
            elif self._layer_included(item):
                if min_levels > 0:
                    errors.add("The Layer '{}' cannot be directly in the theme '{}' (0/{:d}).".format(
                        item.name, theme.name, min_levels
                    ))
                elif item.name in layers:
                    l, l_errors = self._layer(item, dim=DimensionInformation())
                    errors |= l_errors
                    if l is not None:
                        children.append(l)
        return children, errors

    def _functionality(self):
        functionality = {}
        for func_ in get_setting(
                self.settings,
                ("functionalities", "available_in_templates"), []
        ):
            functionality[func_] = get_functionality(
                func_, self.request
            )
        return functionality

    @CACHE_REGION.cache_on_arguments()
    def _get_layers_enum(self):
        layers_enum = {}
        if "enum" in self.settings.get("layers", {}):
            for layer_name, layer in \
                    list(self.settings["layers"]["enum"].items()):
                layer_enum = {}
                layers_enum[layer_name] = layer_enum
                for attribute in list(layer["attributes"].keys()):
                    layer_enum[attribute] = self.request.route_url(
                        "layers_enumerate_attribute_values",
                        layer_name=layer_name,
                        field_name=attribute,
                        path=""
                    )
        return layers_enum

    def _get_role_ids(self):
        return None if self.request.user is None else \
            {role.id for role in self.request.user.roles}

    def get_ngeo_index_vars(self):
        set_common_headers(self.request, "index", NO_CACHE, content_type="text/html")
        return {}

    @view_config(route_name="apijs")
    def apijs(self):
        resolver = AssetResolver('c2cgeoportal_geoportal')
        asset = resolver.resolve('{}_geoportal:static-ngeo/build/api.js'.format(
            self.request.registry.settings['package']
        ))
        self.request.response.body = asset.stream().read()
        response = self.request.response
        set_common_headers(
            self.request, "api", PUBLIC_CACHE,
            response=response, content_type="application/javascript",
        )
        return response

    def favicon(self):
        set_common_headers(
            self.request, 'api', NO_CACHE,
            content_type='image/vnd.microsoft.icon',
        )
        return {}

    def apijsmap(self):
        set_common_headers(
            self.request, "api", NO_CACHE,
            content_type="application/octet-stream",
        )
        return {}

    def apicss(self):
        set_common_headers(
            self.request, "api", PUBLIC_CACHE,
            content_type="text/css",
        )
        return {}

    def apihelp(self):
        set_common_headers(self.request, "index", NO_CACHE)
        return {}

    def _wms_get_features_type(self, ogc_server_id, wfs_url):
        errors = set()

        if ogc_server_id in self.server_wfs_feature_type:
            return self.server_wfs_feature_type[ogc_server_id], errors

        params = {
            "SERVICE": "WFS",
            "VERSION": "1.0.0",
            "REQUEST": "DescribeFeatureType",
        }
        wfs_url = add_url_params(wfs_url, params)

        LOG.info("WFS DescribeFeatureType for base url: %s", wfs_url)

        # forward request to target (without Host Header)
        headers = dict(self.request.headers)
        if urllib.parse.urlsplit(wfs_url).hostname != "localhost" and "Host" in headers:
            headers.pop("Host")  # pragma nocover

        try:
            response = self.get_http_cached(wfs_url, headers)
        except Exception:  # pragma: no cover
            errors.add("Unable to get DescribeFeatureType from URL {}".format(wfs_url))
            return None, errors

        if not response.ok:  # pragma: no cover
            errors.add("DescribeFeatureType from URL {} return the error: {:d} {}".format(
                wfs_url, response.status_code, response.reason
            ))
            return None, errors

        try:
            self.server_wfs_feature_type[ogc_server_id] = lxml.XML(response.text.encode('utf-8'))
            return self.server_wfs_feature_type[ogc_server_id], errors
        except Exception as e:  # pragma: no cover
            errors.add("Error '{}' on reading DescribeFeatureType from URL {}:\n{}".format(
                str(e), wfs_url, response.text
            ))
            return None, errors

    @view_config(route_name="themes", renderer="json")
    def themes(self):
        interface = self.request.params.get("interface", "desktop")
        sets = self.request.params.get("set", "all")
        min_levels = int(self.request.params.get("min_levels", 1))
        group = self.request.params.get("group")
        background_layers_group = self.request.params.get("background")

        export_themes = sets in ("all", "themes")
        export_group = group is not None and sets in ("all", "group")
        export_background = background_layers_group is not None and sets in ("all", "background")

        set_common_headers(self.request, "themes", PRIVATE_CACHE)

        result = {}
        all_errors = set()
        result["ogcServers"] = {}
        for ogc_server in models.DBSession.query(main.OGCServer).all():
            # required to do every time to validate the url.
            if ogc_server.auth != main.OGCSERVER_AUTH_NOAUTH:
                url = self.request.route_url("mapserverproxy", _query={"ogcserver": ogc_server.name})
                url_wfs = url
                url_internal_wfs = get_url2(
                    "The OGC server (WFS) '{}'".format(ogc_server.name),
                    ogc_server.url_wfs or ogc_server.url, self.request, errors=all_errors
                )
            else:
                url = get_url2(
                    "The OGC server '{}'".format(ogc_server.name),
                    ogc_server.url, self.request, errors=all_errors
                )
                url_wfs = get_url2(
                    "The OGC server (WFS) '{}'".format(ogc_server.name),
                    ogc_server.url_wfs, self.request, errors=all_errors
                ) if ogc_server.url_wfs is not None else url
                url_internal_wfs = url_wfs
            feature_type, errors = self._wms_get_features_type(ogc_server.id, url_internal_wfs)
            all_errors |= errors
            attributes = None

            if feature_type is not None:
                types = {}
                elements = {}
                for child in feature_type.getchildren():
                    if child.tag == '{http://www.w3.org/2001/XMLSchema}element':
                        elements[child.attrib['name']] = child.attrib['type'].split(':')[1]

                    if child.tag == '{http://www.w3.org/2001/XMLSchema}complexType':
                        s = child.find('.//{http://www.w3.org/2001/XMLSchema}sequence')
                        attrib = {}
                        for c in s.getchildren():
                            namespace = None
                            type_ = c.attrib['type']
                            if len(type_.split(':')) == 2:
                                namespace, type_ = type_.split(':')
                            namespace = c.nsmap[namespace]
                            attrib[c.attrib['name']] = {
                                'namespace': namespace,
                                'type': type_,
                            }
                            if 'alias' in c.attrib:
                                attrib[c.attrib['name']] = c.attrib['alias']
                        types[child.attrib['name']] = attrib
                attributes = {}
                for name, type_ in elements.items():
                    if type_ in types:
                        attributes[name] = types[type_]
                    else:
                        LOG.warning(
                            "The provided type '%s' does not exist, available types are %s.",
                            type_, ', '.join(types.keys())
                        )
            result["ogcServers"][ogc_server.name] = {
                "url": url,
                "urlWfs": url_wfs,
                "type": ogc_server.type,
                "credential": ogc_server.auth != main.OGCSERVER_AUTH_NOAUTH,
                "imageType": ogc_server.image_type,
                "wfsSupport": ogc_server.wfs_support,
                "isSingleTile": ogc_server.is_single_tile,
                "namespace": feature_type.attrib["targetNamespace"]
                if feature_type is not None and "targetNamespace" in feature_type.attrib else None,
                "attributes": attributes,
            }
        if export_themes:
            themes, errors = self._themes(interface, True, min_levels)

            result["themes"] = themes
            all_errors |= errors

        if export_group:
            group, errors = self._get_group(group, interface)
            if group is not None:
                result["group"] = group
            all_errors |= errors

        if export_background:
            group, errors = self._get_group(background_layers_group, interface)
            result["background_layers"] = group["children"] if group is not None else []
            all_errors |= errors

        result["errors"] = list(all_errors)
        if len(all_errors) > 0:
            LOG.info("Theme errors:\n%s", "\n".join(all_errors))
        return result

    def _get_group(self, group, interface):
        layers = self._layers(interface)
        try:
            lg = models.DBSession.query(main.LayerGroup).filter(main.LayerGroup.name == group).one()
            return self._group(lg.name, lg, layers)
        except NoResultFound:  # pragma: no cover
            return None, set(["Unable to find the Group named: {}, Available Groups: {}".format(
                group, ", ".join([i[0] for i in models.DBSession.query(main.LayerGroup.name).all()])
            )])

    def _referer_log(self):
        if not hasattr(self.request, "is_valid_referer"):
            self.request.is_valid_referer = is_valid_referer(self.request)
        if not self.request.is_valid_referer:
            LOG.error(
                "Invalid referer for %s: %s", self.request.path_qs, repr(self.request.referer)
            )

    @view_config(context=HTTPForbidden, renderer="login.html")
    def loginform403(self):
        self._referer_log()

        if self.request.authenticated_userid:
            return HTTPUnauthorized()  # pragma: no cover

        set_common_headers(self.request, "login", NO_CACHE)

        return {
            "lang": self.lang,
            "came_from": self.request.path,
        }

    @view_config(route_name="loginform", renderer="login.html")
    def loginform(self):
        self._referer_log()

        set_common_headers(self.request, "login", PUBLIC_CACHE, vary=True)

        return {
            "lang": self.lang,
            "came_from": self.request.params.get("came_from") or "/",
        }

    @view_config(route_name="login")
    def login(self):
        self._referer_log()

        login = self.request.POST.get("login")
        password = self.request.POST.get("password")
        if login is None or password is None:  # pragma nocover
            LOG.info("'login' and 'password' should be available in request params.")
            raise HTTPBadRequest("See server logs for details")
        username = self.request.registry.validate_user(self.request, login, password)
        if username is not None:
            user = models.DBSession.query(static.User).filter(static.User.username == username).one_or_none()
            if user:
                user.update_last_login()
            headers = remember(self.request, username)
            LOG.info("User '%s' logged in.", username)
            came_from = self.request.params.get("came_from")
            if came_from:
                return HTTPFound(location=came_from, headers=headers)
            else:
                headers.append(("Content-Type", "text/json"))
                return set_common_headers(
                    self.request, "login", NO_CACHE,
                    response=Response(json.dumps(self._user(
                        self.request.get_user(username)
                    )), headers=headers),
                )
        else:
            raise HTTPUnauthorized("See server logs for details")

    @view_config(route_name="logout")
    def logout(self):
        headers = forget(self.request)

        if not self.request.user:
            LOG.info("Logout on non login user.")
            raise HTTPBadRequest("See server logs for details")

        LOG.info("User '%s' (%s) logging out.", self.request.user.username, self.request.user.id)

        headers.append(("Content-Type", "text/json"))
        return set_common_headers(
            self.request, "login", NO_CACHE,
            response=Response("true", headers=headers),
        )

    def _user(self, user=None):
        user = self.request.user if user is None else user
        result = {
            "success": True,  # for Extjs
            "username": user.username,
            "email": user.email,
            "is_password_changed": user.is_password_changed,
            "roles": [{"name": r.name, "id": r.id} for r in user.roles],
        } if user else {}

        result["functionalities"] = self._functionality()

        return result

    @view_config(route_name="loginuser", renderer="json")
    def loginuser(self):
        self._referer_log()

        set_common_headers(self.request, "login", NO_CACHE)

        return self._user()

    @view_config(route_name="loginchange", renderer="json")
    def loginchange(self):
        set_common_headers(self.request, "login", NO_CACHE)

        old_password = self.request.POST.get("oldPassword")
        new_password = self.request.POST.get("newPassword")
        new_password_confirm = self.request.POST.get("confirmNewPassword")
        if new_password is None or new_password_confirm is None or old_password is None:
            LOG.info(
                "'oldPassword', 'newPassword' and 'confirmNewPassword' should be "
                "available in request params."
            )
            raise HTTPBadRequest("See server logs for details")

        # check if logged in
        if not self.request.user:  # pragma nocover
            LOG.info("Change password on non login user.")
            raise HTTPBadRequest("See server logs for details")

        user = self.request.registry.validate_user(
            self.request, self.request.user.username, old_password
        )
        if user is None:
            LOG.info("The old password is wrong for user '%s'.", user)
            raise HTTPBadRequest("See server logs for details")

        if new_password != new_password_confirm:
            LOG.info(
                "The new password and the new password "
                "confirmation do not match for user '%s'.", user
            )
            raise HTTPBadRequest("See server logs for details")

        u = self.request.user
        u.password = new_password
        u.is_password_changed = True
        models.DBSession.flush()
        LOG.info("Password changed for user '%s'", self.request.user.username)

        return {
            "success": "true"
        }

    @staticmethod
    def generate_password():
        allchars = "123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        rand = Random()

        password = ""
        for _ in range(8):
            password += rand.choice(allchars)

        return password

    def _loginresetpassword(self):
        username = self.request.POST["login"]
        try:
            user = models.DBSession.query(static.User).filter(static.User.username == username).one()
        except NoResultFound:  # pragma: no cover
            return None, None, None, "The login '{}' does not exist.".format(username)

        if user.email is None or user.email == "":  # pragma: no cover
            return \
                None, None, None, \
                "The user '{}' has no registered email address.".format(user.username),

        password = self.generate_password()
        user.set_temp_password(password)

        return user, username, password, None

    @view_config(route_name="loginresetpassword", renderer="json")
    def loginresetpassword(self):  # pragma: no cover
        set_common_headers(
            self.request, "login", NO_CACHE
        )

        user, username, password, error = self._loginresetpassword()
        if error is not None:
            LOG.info(error)
            raise HTTPBadRequest("See server logs for details")

        send_email_config(
            self.request.registry.settings, "reset_password", user.email,
            user=username, password=password
        )

        return {
            "success": True
        }
