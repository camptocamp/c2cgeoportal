# -*- coding: utf-8 -*-

# Copyright (c) 2011-2020, Camptocamp SA
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

import asyncio
from collections import Counter
import gc
import logging
from math import sqrt
import re
import sys
import time
from typing import Any, Dict, List, Set, Union, cast
import urllib.parse

from c2cwsgiutils.auth import auth_view
from defusedxml import lxml
from owslib.wms import WebMapService
from pyramid.view import view_config
import requests
from sqlalchemy.orm import subqueryload
from sqlalchemy.orm.exc import NoResultFound

from c2cgeoportal_commons import models
from c2cgeoportal_commons.models import main
from c2cgeoportal_geoportal.lib import (
    add_url_params,
    get_roles_id,
    get_typed,
    get_types_map,
    get_url2,
    is_intranet,
)
from c2cgeoportal_geoportal.lib.caching import PRIVATE_CACHE, get_region, set_common_headers
from c2cgeoportal_geoportal.lib.functionality import get_mapserver_substitution_params
from c2cgeoportal_geoportal.lib.layers import (
    get_private_layers,
    get_protected_layers,
    get_protected_layers_query,
)
from c2cgeoportal_geoportal.lib.wmstparsing import TimeInformation, parse_extent
from c2cgeoportal_geoportal.views.layers import get_layer_metadatas

LOG = logging.getLogger(__name__)
CACHE_REGION = get_region("std")


def get_http_cached(http_options, url, headers):
    @CACHE_REGION.cache_on_arguments()
    def do_get_http_cached(url):
        response = requests.get(url, headers=headers, timeout=300, **http_options)
        LOG.info("Get url '%s' in %.1fs.", url, response.elapsed.total_seconds())
        return response

    return do_get_http_cached(url)


class DimensionInformation:

    URL_PART_RE = re.compile(r"[a-zA-Z0-9_\-\+~\.]*$")

    def __init__(self) -> None:
        self._dimensions: Dict[str, str] = {}

    def merge(self, layer, layer_node, mixed):
        errors = set()

        dimensions: Dict[str, str] = {}
        dimensions_filters = {}
        for dimension in layer.dimensions:
            if (
                not isinstance(layer, main.LayerWMS)
                and dimension.value is not None
                and not self.URL_PART_RE.match(dimension.value)
            ):
                errors.add(
                    "The layer '{}' has an unsupported dimension value '{}' ('{}').".format(
                        layer.name, dimension.value, dimension.name
                    )
                )
            elif dimension.name in dimensions:  # pragma: nocover
                errors.add(
                    "The layer '{}' has a duplicated dimension name '{}'.".format(layer.name, dimension.name)
                )
            else:
                if dimension.field:
                    dimensions_filters[dimension.name] = {"field": dimension.field, "value": dimension.value}
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
                        "expected '{}' or empty.".format(layer.name, value, name, self._dimensions[name])
                    )
        return errors

    def get_dimensions(self):
        return self._dimensions


class Theme:
    def __init__(self, request):
        self.request = request
        self.settings = request.registry.settings
        self.http_options = self.request.registry.settings.get("http_options", {})
        self.metadata_type = get_types_map(
            self.settings.get("admin_interface", {}).get("available_metadata", [])
        )

        self._ogcservers_cache = None
        self._treeitems_cache = None
        self._layerswms_cache = None
        self._layerswmts_cache = None
        self._layergroup_cache = None
        self._themes_cache = None

    def _get_capabilities_cache_role_key(self, ogc_server):
        return (
            self._get_role_ids()
            if (
                ogc_server.auth != main.OGCSERVER_AUTH_NOAUTH
                and ogc_server.type != main.OGCSERVER_TYPE_MAPSERVER
            )
            else None
        )

    def _get_metadata(self, item, metadata, errors):
        metadatas = item.get_metadatas(metadata)
        return (
            None
            if not metadatas
            else get_typed(
                metadata, metadatas[0].value, self.metadata_type, self.request, errors, layer_name=item.name
            )
        )

    def _get_metadatas(self, item, errors):
        metadatas = {}
        for metadata in item.metadatas:
            value = get_typed(metadata.name, metadata.value, self.metadata_type, self.request, errors)
            if value is not None:
                metadatas[metadata.name] = value

        return metadatas

    async def _wms_getcap(self, ogc_server, preload=False):
        url, content, errors = await self._wms_getcap_cached(
            ogc_server, self._get_capabilities_cache_role_key(ogc_server)
        )

        if errors or preload:
            return None, errors

        @CACHE_REGION.cache_on_arguments()
        def build_web_map_service(ogc_server_id):
            del ogc_server_id  # Just for cache

            layers = {}
            try:
                wms = WebMapService(None, xml=content)
            except Exception as e:  # pragma: no cover
                error = (
                    "WARNING! an error '{}' occurred while trying to read the mapfile and recover the themes."
                    "\nURL: {}\n{}".format(e, url, content)
                )
                LOG.error(error, exc_info=True)
                return None, {error}
            wms_layers_name = list(wms.contents)
            for layer_name in wms_layers_name:
                wms_layer = wms[layer_name]
                resolution = self._get_layer_resolution_hint(wms_layer)
                info = {
                    "name": wms_layer.name,
                    "minResolutionHint": float("{:0.2f}".format(resolution[0])),
                    "maxResolutionHint": float("{:0.2f}".format(resolution[1])),
                }
                if hasattr(wms_layer, "queryable"):
                    info["queryable"] = wms_layer.queryable == 1

                layers[layer_name] = {
                    "info": info,
                    "timepositions": wms_layer.timepositions,
                    "defaulttimeposition": wms_layer.defaulttimeposition,
                    "children": [l.name for l in wms_layer.layers],
                }

            del wms
            LOG.debug("Run garbage collection: %s", ", ".join([str(gc.collect(n)) for n in range(3)]))

            return {"layers": layers}, set()

        return build_web_map_service(ogc_server.id)

    async def _wms_getcap_cached(self, ogc_server, _):
        """ _ is just for cache on the role id """

        errors: Set[str] = set()
        url = get_url2("The OGC server '{}'".format(ogc_server.name), ogc_server.url, self.request, errors)
        if errors or url is None:  # pragma: no cover
            return url, None, errors

        # Add functionality params
        sparams = get_mapserver_substitution_params(self.request)
        url = add_url_params(url, sparams)

        url = add_url_params(
            url,
            {
                "SERVICE": "WMS",
                "VERSION": "1.1.1",
                "REQUEST": "GetCapabilities",
                "ROLE_ID": "0",
                "USER_ID": "0",
            },
        )

        LOG.debug("Get WMS GetCapabilities for url: %s", url)

        # Forward request to target (without Host Header)
        headers = dict(self.request.headers)

        # Add headers for Geoserver
        if ogc_server.auth == main.OGCSERVER_AUTH_GEOSERVER:
            headers["sec-username"] = "root"
            headers["sec-roles"] = "root"

        if urllib.parse.urlsplit(url).hostname != "localhost" and "Host" in headers:  # pragma: no cover
            headers.pop("Host")

        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, get_http_cached, self.http_options, url, headers
            )
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
        if response.headers.get("Content-Type", "").split(";")[0].strip() not in [
            "application/vnd.ogc.wms_xml",
            "text/xml",
        ]:
            error = "GetCapabilities from URL {} returns a wrong Content-Type: {}\n{}".format(
                url, response.headers.get("Content-Type", ""), response.text
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

        query2 = get_protected_layers_query(self.request, None, what=main.LayerWMS.name)
        if interface is not None:
            query2 = query2.join(main.Layer.interfaces)
            query2 = query2.filter(main.Interface.name == interface)
        query = query.union(query2)
        query3 = get_protected_layers_query(self.request, None, what=main.LayerWMTS.name)
        if interface is not None:
            query3 = query3.join(main.Layer.interfaces)
            query3 = query3.filter(main.Interface.name == interface)
        query = query.union(query3)

        return query

    def _get_layer_metadata_urls(self, layer):
        metadata_urls: List[str] = []
        if layer.metadataUrls:
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
            resolution_hint_max = (
                float(layer.scaleHint["max"]) / sqrt(2)
                if layer.scaleHint["max"] not in ("0", "Infinity")
                else 999999999
            )
        for child_layer in layer.layers:
            resolution = self._get_layer_resolution_hint_raw(child_layer)
            resolution_hint_min = (
                resolution[0]
                if resolution_hint_min is None
                else (
                    resolution_hint_min if resolution[0] is None else min(resolution_hint_min, resolution[0])
                )
            )
            resolution_hint_max = (
                resolution[1]
                if resolution_hint_max is None
                else (
                    resolution_hint_max if resolution[1] is None else max(resolution_hint_max, resolution[1])
                )
            )

        return (resolution_hint_min, resolution_hint_max)

    def _get_layer_resolution_hint(self, layer):
        resolution_hint_min, resolution_hint_max = self._get_layer_resolution_hint_raw(layer)
        return (
            0.0 if resolution_hint_min is None else resolution_hint_min,
            999999999 if resolution_hint_max is None else resolution_hint_max,
        )

    def _layer(self, layer, time_=None, dim=None, mixed=True):
        errors: Set[str] = set()
        layer_info = {"id": layer.id, "name": layer.name, "metadata": self._get_metadatas(layer, errors)}
        if re.search("[/?#]", layer.name):  # pragma: no cover
            errors.add("The layer has an unsupported name '{}'.".format(layer.name))
        if isinstance(layer, main.LayerWMS) and re.search("[/?#]", layer.layer):  # pragma: no cover
            errors.add("The layer has an unsupported layers '{}'.".format(layer.layer))
        if layer.geo_table:
            errors |= self._fill_editable(layer_info, layer)
        if mixed:
            assert time_ is None
            time_ = TimeInformation()
        assert time_ is not None

        errors |= dim.merge(layer, layer_info, mixed)

        if isinstance(layer, main.LayerWMS):
            wms, wms_errors = self._wms_layers(layer.ogc_server)
            errors |= wms_errors
            if wms is None:
                return layer_info, errors
            if layer.layer is None or layer.layer == "":
                errors.add("The layer '{}' do not have any layers".format(layer.name))
                return None, errors
            layer_info["type"] = "WMS"
            layer_info["layers"] = layer.layer
            self._fill_wms(layer_info, layer, errors, mixed=mixed)
            errors |= self._merge_time(time_, layer_info, layer, wms)

        elif isinstance(layer, main.LayerWMTS):
            layer_info["type"] = "WMTS"
            self._fill_wmts(layer_info, layer, errors)

        elif isinstance(layer, main.LayerVectorTiles):
            layer_info["type"] = "VectorTiles"
            self._vectortiles_layers(layer_info, layer)

        return layer_info, errors

    @staticmethod
    def _merge_time(time_, layer_theme, layer, wms):
        errors = set()
        wmslayer = layer.layer
        try:
            if wmslayer in wms["layers"]:
                wms_layer_obj = wms["layers"][wmslayer]

                if layer.time_mode != "disabled":
                    if wms_layer_obj["timepositions"]:
                        extent = parse_extent(
                            wms_layer_obj["timepositions"], wms_layer_obj["defaulttimeposition"]
                        )
                        time_.merge(layer_theme, extent, layer.time_mode, layer.time_widget)
                    else:
                        errors.add(
                            "Error: time layer '{}' has no time information in capabilities".format(
                                layer.name
                            )
                        )

                for child_layer_name in wms_layer_obj["children"]:
                    child_layer = wms["layers"][child_layer_name]
                    if child_layer["timepositions"]:
                        extent = parse_extent(
                            child_layer["timepositions"], child_layer["defaulttimeposition"]
                        )
                        # The time mode comes from the layer group
                        time_.merge(layer_theme, extent, layer.time_mode, layer.time_widget)

        except ValueError:  # pragma no cover
            errors.add("Error while handling time for layer '{}': {}".format(layer.name, sys.exc_info()[1]))

        return errors

    def _fill_editable(self, layer_theme, layer):
        errors = set()
        try:
            if self.request.user:
                count = (
                    models.DBSession.query(main.RestrictionArea)
                    .join(main.RestrictionArea.roles)
                    .filter(main.Role.id.in_(get_roles_id(self.request)))
                    .filter(main.RestrictionArea.layers.any(main.Layer.id == layer.id))
                    .filter(main.RestrictionArea.readwrite.is_(True))
                    .count()
                )
                if count > 0:
                    layer_theme["edit_columns"] = get_layer_metadatas(layer)
                    layer_theme["editable"] = True
        except Exception as exception:
            LOG.exception(str(exception))
            errors.add(str(exception))
        return errors

    def _fill_wms(self, layer_theme, layer, errors, mixed):
        wms, wms_errors = self._wms_layers(layer.ogc_server)
        errors |= wms_errors
        if wms is None:
            return

        layer_theme["imageType"] = layer.ogc_server.image_type
        if layer.style:  # pragma: no cover
            layer_theme["style"] = layer.style

        # now look at what is in the WMS capabilities doc
        layer_theme["childLayers"] = []
        for layer_name in layer.layer.split(","):
            if layer_name in wms["layers"]:
                wms_layer_obj = wms["layers"][layer_name]
                if not wms_layer_obj["children"]:
                    layer_theme["childLayers"].append(wms["layers"][layer_name]["info"])
                else:
                    for child_layer in wms_layer_obj["children"]:
                        layer_theme["childLayers"].append(wms["layers"][child_layer]["info"])
            else:
                errors.add(
                    "The layer '{}' ({}) is not defined in WMS capabilities from '{}'".format(
                        layer_name, layer.name, layer.ogc_server.name
                    )
                )

        if "minResolutionHint" not in layer_theme:
            resolution_min = self._get_metadata(layer, "minResolution", errors)

            if resolution_min is not None:
                layer_theme["minResolutionHint"] = resolution_min
            else:
                min_resolutions_hint = [
                    l_["minResolutionHint"] for l_ in layer_theme["childLayers"] if "minResolutionHint" in l_
                ]
                if min_resolutions_hint:
                    layer_theme["minResolutionHint"] = min(min_resolutions_hint)
        if "maxResolutionHint" not in layer_theme:
            resolution_max = self._get_metadata(layer, "maxResolution", errors)

            if resolution_max is not None:
                layer_theme["maxResolutionHint"] = resolution_max
            else:
                max_resolutions_hint = [
                    l_["maxResolutionHint"] for l_ in layer_theme["childLayers"] if "maxResolutionHint" in l_
                ]
                if max_resolutions_hint:
                    layer_theme["maxResolutionHint"] = max(max_resolutions_hint)

        if mixed:
            layer_theme["ogcServer"] = layer.ogc_server.name

    @staticmethod
    def _fill_legend_rule_query_string(layer_theme, layer, url):
        if layer.legend_rule and url:
            layer_theme["icon"] = add_url_params(
                url,
                {
                    "SERVICE": "WMS",
                    "VERSION": "1.1.1",
                    "REQUEST": "GetLegendGraphic",
                    "LAYER": layer.name,
                    "FORMAT": "image/png",
                    "TRANSPARENT": "TRUE",
                    "RULE": layer.legend_rule,
                },
            )

    def _fill_wmts(self, layer_theme, layer, errors):
        layer_theme["url"] = get_url2(
            "The WMTS layer '{}'".format(layer.name), layer.url, self.request, errors=errors
        )

        if layer.style:
            layer_theme["style"] = layer.style
        if layer.matrix_set:
            layer_theme["matrixSet"] = layer.matrix_set

        layer_theme["layer"] = layer.layer
        layer_theme["imageType"] = layer.image_type

    @staticmethod
    def _vectortiles_layers(layer_theme, layer):
        layer_theme["style"] = layer.style
        if layer.xyz:
            layer_theme["xyz"] = layer.xyz

    @staticmethod
    def _layer_included(tree_item):
        return isinstance(tree_item, main.Layer)

    def _get_ogc_servers(self, group, depth):
        """ Recurse on all children to get unique identifier for each child. """

        ogc_servers: Set[Union[str, bool]] = set()

        # escape loop
        if depth > 30:
            LOG.error("Error: too many recursions with group '%s'", group.name)
            return ogc_servers

        # recurse on children
        if isinstance(group, main.LayerGroup) and group.children:
            for tree_item in group.children:
                ogc_servers.update(self._get_ogc_servers(tree_item, depth + 1))

        if isinstance(group, main.LayerWMS):
            ogc_servers.add(group.ogc_server.name)

        if isinstance(group, main.LayerWMTS):
            ogc_servers.add(False)

        return ogc_servers

    def _group(
        self,
        path,
        group,
        layers,
        depth=1,
        min_levels=1,
        mixed=True,
        time_=None,
        dim=None,
        wms_layers=None,
        layers_name=None,
        **kwargs,
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
            errors.add("Too many recursions with group '{}'".format(group.name))
            return None, errors

        ogc_servers = None
        org_depth = depth
        if depth == 1:
            ogc_servers = list(self._get_ogc_servers(group, 1))
            # check if mixed content
            mixed = len(ogc_servers) != 1 or ogc_servers[0] is False
            if not mixed:
                time_ = TimeInformation()
            dim = DimensionInformation()

        for tree_item in group.children:
            if isinstance(tree_item, main.LayerGroup):
                group_theme, gp_errors = self._group(
                    "{}/{}".format(path, tree_item.name),
                    tree_item,
                    layers,
                    depth=depth + 1,
                    min_levels=min_levels,
                    mixed=mixed,
                    time_=time_,
                    dim=dim,
                    wms_layers=wms_layers,
                    layers_name=layers_name,
                    **kwargs,
                )
                errors |= gp_errors
                if group_theme is not None:
                    children.append(group_theme)
            elif self._layer_included(tree_item):
                if tree_item.name in layers:
                    layers_name.append(tree_item.name)
                    if isinstance(tree_item, main.LayerWMS):
                        wms_layers.extend(tree_item.layer.split(","))

                    layer_theme, l_errors = self._layer(tree_item, mixed=mixed, time_=time_, dim=dim)
                    errors |= l_errors
                    if layer_theme is not None:
                        if depth < min_levels:
                            errors.add(
                                "The Layer '{}' is under indented ({:d}/{:d}).".format(
                                    path + "/" + tree_item.name, depth, min_levels
                                )
                            )
                        else:
                            children.append(layer_theme)

        if children:
            group_theme = {
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

            group_theme["mixed"] = mixed
            if org_depth == 1:
                if not mixed:
                    group_theme["ogcServer"] = cast(List, ogc_servers)[0]
                    if time_.has_time() and time_.layer is None:
                        group_theme["time"] = time_.to_dict()

                    group_theme["dimensions"] = dim.get_dimensions()

            return group_theme, errors
        return None, errors

    def _layers(self, interface):
        query = self._create_layer_query(interface=interface)
        return [name for (name,) in query.all()]

    def _wms_layers(self, ogc_server):
        # retrieve layers metadata via GetCapabilities
        wms, wms_errors = asyncio.run(self._wms_getcap(ogc_server))
        if wms_errors:
            return None, wms_errors

        return wms, set()

    def _load_tree_items(self) -> None:
        # Populate sqlalchemy session.identity_map to reduce the number of database requests.
        self._ogcservers_cache = models.DBSession.query(main.OGCServer).all()
        self._treeitems_cache = models.DBSession.query(main.TreeItem).all()
        self._layerswms_cache = (
            models.DBSession.query(main.LayerWMS)
            .options(subqueryload(main.LayerWMS.dimensions), subqueryload(main.LayerWMS.metadatas))
            .all()
        )
        self._layerswmts_cache = (
            models.DBSession.query(main.LayerWMTS)
            .options(subqueryload(main.LayerWMTS.dimensions), subqueryload(main.LayerWMTS.metadatas))
            .all()
        )
        self._layergroup_cache = (
            models.DBSession.query(main.LayerGroup)
            .options(subqueryload(main.LayerGroup.metadatas), subqueryload(main.LayerGroup.children_relation))
            .all()
        )
        self._themes_cache = (
            models.DBSession.query(main.Theme)
            .options(
                subqueryload(main.Theme.functionalities),
                subqueryload(main.Theme.metadatas),
                subqueryload(main.Theme.children_relation),
            )
            .all()
        )

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
        auth_themes = models.DBSession.query(main.Theme)
        auth_themes = auth_themes.filter(main.Theme.public.is_(False))
        auth_themes = auth_themes.join(main.Theme.restricted_roles)
        auth_themes = auth_themes.filter(main.Role.id.in_(get_roles_id(self.request)))

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

            # Test if the theme is visible for the current user
            if children:
                icon = (
                    get_url2("The Theme '{}'".format(theme.name), theme.icon, self.request, errors)
                    if theme.icon is not None and theme.icon
                    else self.request.static_url("/etc/geomapfish/static/images/blank.png")
                )

                theme_theme = {
                    "id": theme.id,
                    "name": theme.name,
                    "icon": icon,
                    "children": children,
                    "functionalities": self._get_functionalities(theme),
                    "metadata": self._get_metadatas(theme, errors),
                }
                export_themes.append(theme_theme)

        return export_themes, errors

    @staticmethod
    def _get_functionalities(theme):
        result: Dict[str, List[str]] = {}
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
        return {"success": True}

    def _get_children(self, theme, layers, min_levels):
        children = []
        errors: Set[str] = set()
        for item in theme.children:
            if isinstance(item, main.LayerGroup):
                group_theme, gp_errors = self._group(
                    "{}/{}".format(theme.name, item.name), item, layers, min_levels=min_levels
                )
                errors |= gp_errors
                if group_theme is not None:
                    children.append(group_theme)
            elif self._layer_included(item):
                if min_levels > 0:
                    errors.add(
                        "The Layer '{}' cannot be directly in the theme '{}' (0/{:d}).".format(
                            item.name, theme.name, min_levels
                        )
                    )
                elif item.name in layers:
                    layer_theme, l_errors = self._layer(item, dim=DimensionInformation())
                    errors |= l_errors
                    if layer_theme is not None:
                        children.append(layer_theme)
        return children, errors

    @CACHE_REGION.cache_on_arguments()
    def _get_layers_enum(self):
        layers_enum = {}
        if "enum" in self.settings.get("layers", {}):
            for layer_name, layer in list(self.settings["layers"]["enum"].items()):
                layer_enum: Dict[str, str] = {}
                layers_enum[layer_name] = layer_enum
                for attribute in list(layer["attributes"].keys()):
                    layer_enum[attribute] = self.request.route_url(
                        "layers_enumerate_attribute_values",
                        layer_name=layer_name,
                        field_name=attribute,
                        path="",
                    )
        return layers_enum

    def _get_role_ids(self):
        return None if self.request.user is None else {role.id for role in self.request.user.roles}

    async def _wms_get_features_type(self, wfs_url, preload=False):
        errors = set()

        params = {
            "SERVICE": "WFS",
            "VERSION": "1.0.0",
            "REQUEST": "DescribeFeatureType",
            "ROLE_ID": "0",
            "USER_ID": "0",
        }
        wfs_url = add_url_params(wfs_url, params)

        LOG.debug("WFS DescribeFeatureType for base url: %s", wfs_url)

        # forward request to target (without Host Header)
        headers = dict(self.request.headers)
        if urllib.parse.urlsplit(wfs_url).hostname != "localhost" and "Host" in headers:
            headers.pop("Host")  # pragma nocover

        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, get_http_cached, self.http_options, wfs_url, headers
            )
        except Exception:  # pragma: no cover
            errors.add("Unable to get DescribeFeatureType from URL {}".format(wfs_url))
            return None, errors

        if not response.ok:  # pragma: no cover
            errors.add(
                "DescribeFeatureType from URL {} return the error: {:d} {}".format(
                    wfs_url, response.status_code, response.reason
                )
            )
            return None, errors

        if preload:
            return None, errors

        try:
            return lxml.XML(response.text.encode("utf-8")), errors
        except Exception as e:  # pragma: no cover
            errors.add(
                "Error '{}' on reading DescribeFeatureType from URL {}:\n{}".format(
                    str(e), wfs_url, response.text
                )
            )
            return None, errors

    def get_url_internal_wfs(self, ogc_server, errors):
        # required to do every time to validate the url.
        if ogc_server.auth != main.OGCSERVER_AUTH_NOAUTH:
            url = self.request.route_url("mapserverproxy", _query={"ogcserver": ogc_server.name})
            url_wfs = url
            url_internal_wfs = get_url2(
                "The OGC server (WFS) '{}'".format(ogc_server.name),
                ogc_server.url_wfs or ogc_server.url,
                self.request,
                errors=errors,
            )
        else:
            url = get_url2(
                "The OGC server '{}'".format(ogc_server.name), ogc_server.url, self.request, errors=errors
            )
            url_wfs = (
                get_url2(
                    "The OGC server (WFS) '{}'".format(ogc_server.name),
                    ogc_server.url_wfs,
                    self.request,
                    errors=errors,
                )
                if ogc_server.url_wfs is not None
                else url
            )
            url_internal_wfs = url_wfs
        return url_internal_wfs, url, url_wfs

    async def preload(self, errors):
        tasks = set()
        for ogc_server in models.DBSession.query(main.OGCServer).all():
            url_internal_wfs, _, _ = self.get_url_internal_wfs(ogc_server, errors)
            tasks.add(self._wms_get_features_type(url_internal_wfs, True))
            tasks.add(self._wms_getcap(ogc_server, True))

        await asyncio.gather(*tasks)

    @CACHE_REGION.cache_on_arguments()
    def _get_features_attributes(self, url_internal_wfs):
        all_errors: Set[str] = set()
        feature_type, errors = asyncio.run(self._wms_get_features_type(url_internal_wfs))
        LOG.debug("Run garbage collection: %s", ", ".join([str(gc.collect(n)) for n in range(3)]))
        if errors:
            all_errors |= errors
            return None, None, all_errors
        namespace = feature_type.attrib.get("targetNamespace")
        types = {}
        elements = {}
        for child in feature_type.getchildren():
            if child.tag == "{http://www.w3.org/2001/XMLSchema}element":
                name = child.attrib["name"]
                type_namespace, type_ = child.attrib["type"].split(":")
                if type_namespace not in child.nsmap:
                    LOG.info(
                        "The namespace '%s' of the type '%s' is not found in the available namespaces: %s",
                        type_namespace,
                        name,
                        ", ".join(child.nsmap.keys()),
                    )
                if child.nsmap[type_namespace] != namespace:
                    LOG.info(
                        "The namespace '%s' of the thye '%s' should be '%s'.",
                        child.nsmap[type_namespace],
                        name,
                        namespace,
                    )
                elements[name] = type_

            if child.tag == "{http://www.w3.org/2001/XMLSchema}complexType":
                sequence = child.find(".//{http://www.w3.org/2001/XMLSchema}sequence")
                attrib = {}
                for children in sequence.getchildren():
                    type_namespace = None
                    type_ = children.attrib["type"]
                    if len(type_.split(":")) == 2:
                        type_namespace, type_ = type_.split(":")
                    type_namespace = children.nsmap[type_namespace]
                    name = children.attrib["name"]
                    attrib[name] = {"namespace": type_namespace, "type": type_}
                    for key, value in children.attrib.items():
                        if key not in ("name", "type", "namespace"):
                            attrib[name][key] = value
                types[child.attrib["name"]] = attrib
        attributes = {}
        for name, type_ in elements.items():
            if type_ in types:
                attributes[name] = types[type_]
            elif (type_ == "Character") and (name + "Type") in types:
                LOG.debug(
                    "Due mapserver strange result the type 'ms:Character' is fallbacked to type '%sType'"
                    " for feature '%s', This is a stange comportement of mapserver when we use the "
                    'METADATA "gml_types" "auto"',
                    name,
                    name,
                )
                attributes[name] = types[name + "Type"]
            else:
                LOG.warning(
                    "The provided type '%s' does not exist, available types are %s.",
                    type_,
                    ", ".join(types.keys()),
                )

        return attributes, namespace, all_errors

    @view_config(route_name="themes", renderer="json")
    def themes(self):
        interface = self.request.params.get("interface", "desktop")
        sets = self.request.params.get("set", "all")
        min_levels = int(self.request.params.get("min_levels", 1))
        group = self.request.params.get("group")
        background_layers_group = self.request.params.get("background")

        set_common_headers(self.request, "themes", PRIVATE_CACHE)

        def get_theme():
            export_themes = sets in ("all", "themes")
            export_group = group is not None and sets in ("all", "group")
            export_background = background_layers_group is not None and sets in ("all", "background")

            result: Dict[str, Union[Dict[str, Dict[str, Any]], List[str]]] = {}
            all_errors: Set[str] = set()
            LOG.debug("Start preload")
            start_time = time.time()
            asyncio.run(self.preload(all_errors))
            LOG.debug("End preload")
            LOG.info("Do preload in %.3fs.", time.time() - start_time)
            result["ogcServers"] = {}
            for ogc_server in models.DBSession.query(main.OGCServer).all():
                url_internal_wfs, url, url_wfs = self.get_url_internal_wfs(ogc_server, all_errors)

                attributes = None
                namespace = None
                if ogc_server.wfs_support:
                    attributes, namespace, errors = self._get_features_attributes(url_internal_wfs)
                    all_errors |= errors

                    all_private_layers = get_private_layers([ogc_server.id]).values()
                    protected_layers_name = [
                        l.name for l in get_protected_layers(self.request, [ogc_server.id]).values()
                    ]
                    private_layers_name: List[str] = []
                    for layers in [
                        v.layer for v in all_private_layers if v.name not in protected_layers_name
                    ]:
                        private_layers_name.extend(layers.split(","))

                    if attributes is not None:
                        for name in private_layers_name:
                            if name in attributes:
                                del attributes[name]

                result["ogcServers"][ogc_server.name] = {
                    "url": url,
                    "urlWfs": url_wfs,
                    "type": ogc_server.type,
                    "credential": ogc_server.auth != main.OGCSERVER_AUTH_NOAUTH,
                    "imageType": ogc_server.image_type,
                    "wfsSupport": ogc_server.wfs_support,
                    "isSingleTile": ogc_server.is_single_tile,
                    "namespace": namespace,
                    "attributes": attributes,
                }
            if export_themes:
                themes, errors = self._themes(interface, True, min_levels)

                result["themes"] = themes
                all_errors |= errors

            if export_group:
                exported_group, errors = self._get_group(group, interface)
                if exported_group is not None:
                    result["group"] = exported_group
                all_errors |= errors

            if export_background:
                exported_group, errors = self._get_group(background_layers_group, interface)
                result["background_layers"] = exported_group["children"] if exported_group is not None else []
                all_errors |= errors

            result["errors"] = list(all_errors)
            if all_errors:
                LOG.info("Theme errors:\n%s", "\n".join(all_errors))
            return result

        @CACHE_REGION.cache_on_arguments()
        def get_theme_anonymous(intranet, interface, sets, min_levels, group, background_layers_group, host):
            # Only for cache key
            del intranet, interface, sets, min_levels, group, background_layers_group, host
            return get_theme()

        if self.request.user is None:
            return get_theme_anonymous(
                is_intranet(self.request),
                interface,
                sets,
                min_levels,
                group,
                background_layers_group,
                self.request.headers.get("Host"),
            )
        return get_theme()

    def _get_group(self, group, interface):
        layers = self._layers(interface)
        try:
            group_db = models.DBSession.query(main.LayerGroup).filter(main.LayerGroup.name == group).one()
            return self._group(group_db.name, group_db, layers, depth=2, dim=DimensionInformation())
        except NoResultFound:  # pragma: no cover
            return (
                None,
                set(
                    [
                        "Unable to find the Group named: {}, Available Groups: {}".format(
                            group,
                            ", ".join([i[0] for i in models.DBSession.query(main.LayerGroup.name).all()]),
                        )
                    ]
                ),
            )
