# Copyright (c) 2011-2025, Camptocamp SA
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
import gc
import logging
import os
import re
import sys
import time
from collections import Counter
from math import sqrt
from typing import Any, Optional, Union, cast

import dogpile.cache.api
import pyramid.httpexceptions
import pyramid.request
import requests
import sqlalchemy
import sqlalchemy.orm.query
from c2cwsgiutils.auth import auth_view
from defusedxml import lxml
from lxml import etree  # nosec
from owslib.wms import WebMapService
from pyramid.view import view_config
from sqlalchemy.orm import subqueryload
from sqlalchemy.orm.exc import NoResultFound  # type: ignore[attr-defined]

from c2cgeoportal_commons import models
from c2cgeoportal_commons.lib.url import Url, get_url2
from c2cgeoportal_commons.models import cache_invalidate_cb, main
from c2cgeoportal_geoportal import is_allowed_host, is_allowed_url
from c2cgeoportal_geoportal.lib import get_roles_id, get_typed, get_types_map, is_intranet
from c2cgeoportal_geoportal.lib.caching import get_region
from c2cgeoportal_geoportal.lib.common_headers import Cache, set_common_headers
from c2cgeoportal_geoportal.lib.functionality import get_mapserver_substitution_params
from c2cgeoportal_geoportal.lib.layers import (
    get_private_layers,
    get_protected_layers,
    get_protected_layers_query,
)
from c2cgeoportal_geoportal.lib.wmstparsing import TimeInformation, parse_extent
from c2cgeoportal_geoportal.views.layers import get_layer_metadata

_LOG = logging.getLogger(__name__)
_CACHE_REGION = get_region("std")
_CACHE_OGC_SERVER_REGION = get_region("ogc-server")
_TIMEOUT = int(os.environ.get("C2CGEOPORTAL_THEME_TIMEOUT", "300"))

Metadata = Union[str, int, float, bool, list[Any], dict[str, Any]]


async def get_http_cached(
    http_options: dict[str, Any], url: str, headers: dict[str, str], cache: bool = True
) -> tuple[bytes, str]:
    """Get the content of the URL with a cache (dogpile)."""

    @_CACHE_OGC_SERVER_REGION.cache_on_arguments()
    def do_get_http_cached(url: str) -> tuple[bytes, str]:
        # This function is just used to create a cache entry
        raise NotImplementedError()

    # Use the cache
    if cache:
        result = cast(tuple[bytes, str], do_get_http_cached.get(url))  # type: ignore[attr-defined]
        if result != dogpile.cache.api.NO_VALUE:  # type: ignore[comparison-overlap]
            return result

    response = await asyncio.to_thread(
        requests.get, url.strip(), headers=headers, timeout=_TIMEOUT, **http_options
    )
    response.raise_for_status()
    _LOG.info("Get url '%s' in %.1fs.", url, response.elapsed.total_seconds())
    result = (response.content, response.headers.get("Content-Type", ""))
    # Set the result in the cache
    do_get_http_cached.set(result, url)  # type: ignore[attr-defined]
    return result


class DimensionInformation:
    """Used to collect the dimensions information."""

    URL_PART_RE = re.compile(r"[a-zA-Z0-9_\-\+~\.]*$")

    def __init__(self) -> None:
        self._dimensions: dict[str, str] = {}

    def merge(self, layer: main.Layer, layer_node: dict[str, Any], mixed: bool) -> set[str]:
        errors = set()

        dimensions: dict[str, str] = {}
        dimensions_filters = {}
        for dimension in layer.dimensions:
            if (
                not isinstance(layer, main.LayerWMS)
                and dimension.value is not None
                and not self.URL_PART_RE.match(dimension.value)
            ):
                errors.add(
                    f"The layer '{layer.name}' has an unsupported dimension value "
                    f"'{dimension.value}' ('{dimension.name}')."
                )
            elif dimension.name in dimensions:  # pragma: nocover
                errors.add(f"The layer '{layer.name}' has a duplicated dimension name '{dimension.name}'.")
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
                        f"The layer '{layer.name}' has a wrong dimension value '{value}' for '{name}', "
                        f"expected '{self._dimensions[name]}' or empty."
                    )
        return errors

    def get_dimensions(self) -> dict[str, str]:
        return self._dimensions


class Theme:
    """All the views concerning the themes."""

    def __init__(self, request: pyramid.request.Request):
        self.request = request
        self.settings = request.registry.settings
        self.http_options = self.settings.get("http_options", {})
        self.metadata_type = get_types_map(
            self.settings.get("admin_interface", {}).get("available_metadata", [])
        )

        self._ogcservers_cache: list[main.OGCServer] | None = None
        self._treeitems_cache: list[main.TreeItem] | None = None
        self._layerswms_cache: list[main.LayerWMS] | None = None
        self._layerswmts_cache: list[main.LayerWMTS] | None = None
        self._layergroup_cache: list[main.LayerGroup] | None = None
        self._themes_cache: list[main.Theme] | None = None

    def _get_metadata(
        self, item: main.TreeItem, metadata: str, errors: set[str]
    ) -> None | str | int | float | bool | list[Any] | dict[str, Any]:
        metadatas = item.get_metadata(metadata)
        return (
            None
            if not metadatas
            else get_typed(
                metadata, metadatas[0].value, self.metadata_type, self.request, errors, layer_name=item.name
            )
        )

    def _get_metadata_list(self, item: main.TreeItem, errors: set[str]) -> dict[str, Metadata]:
        metadatas: dict[str, Metadata] = {}
        metadata: main.Metadata
        for metadata in item.metadatas:
            value = get_typed(metadata.name, metadata.value, self.metadata_type, self.request, errors)
            if value is not None:
                metadatas[metadata.name] = value

        return metadatas

    async def _wms_getcap(
        self, ogc_server: main.OGCServer, preload: bool = False, cache: bool = True
    ) -> tuple[dict[str, dict[str, Any]] | None, set[str]]:
        _LOG.debug("Get the WMS Capabilities of %s, preload: %s, cache: %s", ogc_server.name, preload, cache)

        @_CACHE_OGC_SERVER_REGION.cache_on_arguments()
        def build_web_map_service(ogc_server_id: int) -> tuple[dict[str, dict[str, Any]] | None, set[str]]:
            del ogc_server_id  # Just for cache

            if url is None:
                raise RuntimeError("URL is None")

            version = url.query.get("VERSION", "1.1.1")
            layers = {}
            try:
                wms = WebMapService(None, xml=content, version=version)
            except Exception as e:  # pylint: disable=broad-exception-caught
                error = (
                    f"WARNING! an error '{e!s}' occurred while trying to read the mapfile and "
                    "recover the themes."
                    f"\nURL: {url}\n{content.decode() if content else None}"
                )
                _LOG.error(error, exc_info=True)
                return None, {error}
            wms_layers_name = list(wms.contents)
            for layer_name in wms_layers_name:
                wms_layer = wms[layer_name]
                resolution = self._get_layer_resolution_hint(wms_layer)
                info = {
                    "name": wms_layer.name,
                    "minResolutionHint": float(f"{resolution[0]:0.2f}"),
                    "maxResolutionHint": float(f"{resolution[1]:0.2f}"),
                }
                if hasattr(wms_layer, "queryable"):
                    info["queryable"] = wms_layer.queryable == 1

                layers[layer_name] = {
                    "info": info,
                    "timepositions": wms_layer.timepositions,
                    "defaulttimeposition": wms_layer.defaulttimeposition,
                    "children": [layer.name for layer in wms_layer.layers],
                }

            del wms

            return {"layers": layers}, set()

        if cache:
            result = build_web_map_service.get(ogc_server.id)  # type: ignore[attr-defined]
            if result != dogpile.cache.api.NO_VALUE:
                return result  # type: ignore[no-any-return]

        try:
            url, content, errors = await self._wms_getcap_cached(ogc_server, cache=cache)
        except requests.exceptions.RequestException as exception:
            if exception.response is None:
                error = (
                    f"Unable to get the WMS Capabilities for OGC server '{ogc_server.name}', "
                    f"return the error: {exception}"
                )
            else:
                error = (
                    f"Unable to get the WMS Capabilities for OGC server '{ogc_server.name}', "
                    f"return the error: {exception.response.status_code} {exception.response.reason}"
                )
            _LOG.exception(error)
            return None, {error}
        if errors or preload:
            return None, errors

        return build_web_map_service.refresh(ogc_server.id)  # type: ignore

    async def _wms_getcap_cached(
        self, ogc_server: main.OGCServer, cache: bool = True
    ) -> tuple[Url | None, bytes | None, set[str]]:
        errors: set[str] = set()
        url = get_url2(f"The OGC server '{ogc_server.name}'", ogc_server.url, self.request, errors)
        if errors or url is None:
            return url, None, errors

        # Add functionality params
        if (
            ogc_server.auth == main.OGCSERVER_AUTH_STANDARD
            and ogc_server.type == main.OGCSERVER_TYPE_MAPSERVER
        ):
            url.add_query(get_mapserver_substitution_params(self.request))

        url.add_query(
            {
                "SERVICE": "WMS",
                "VERSION": "1.1.1",
                "REQUEST": "GetCapabilities",
                "ROLE_IDS": "0",
                "USER_ID": "0",
            },
        )

        _LOG.debug("Get WMS GetCapabilities for URL: %s", url)

        headers = {}

        # Add headers for Geoserver
        if ogc_server.auth == main.OGCSERVER_AUTH_GEOSERVER:
            headers["sec-username"] = "root"
            headers["sec-roles"] = "root"

        try:
            content, content_type = await get_http_cached(self.http_options, url.url(), headers, cache=cache)
        except Exception:  # pylint: disable=broad-exception-caught
            error = f"Unable to GetCapabilities from URL {url}"
            errors.add(error)
            _LOG.error(error, exc_info=True)
            return url, None, errors

        # With wms 1.3 it returns text/xml also in case of error :-(
        if content_type.split(";")[0].strip() not in [
            "application/vnd.ogc.wms_xml",
            "text/xml",
        ]:
            error = (
                f"GetCapabilities from URL '{url}' returns a wrong Content-Type: {content_type}\n"
                f"{content.decode()}"
            )
            errors.add(error)
            _LOG.error(error)
            return url, None, errors

        return url, content, errors

    def _create_layer_query(self, interface: str) -> sqlalchemy.orm.query.RowReturningQuery[tuple[str]]:
        """Create an SQLAlchemy query for Layer and for the role identified to by ``role_id``."""

        assert models.DBSession is not None

        query: sqlalchemy.orm.query.RowReturningQuery[tuple[str]] = models.DBSession.query(
            main.Layer.name
        ).filter(main.Layer.public.is_(True))

        if interface is not None:
            query = query.join(main.Layer.interfaces)
            query = query.filter(main.Interface.name == interface)

        query2 = get_protected_layers_query(self.request, None, what=main.LayerWMS.name)  # type: ignore[arg-type]
        if interface is not None:
            query2 = query2.join(main.Layer.interfaces)
            query2 = query2.filter(main.Interface.name == interface)
        query = query.union(query2)
        query3 = get_protected_layers_query(self.request, None, what=main.LayerWMTS.name)  # type: ignore[arg-type]
        if interface is not None:
            query3 = query3.join(main.Layer.interfaces)
            query3 = query3.filter(main.Interface.name == interface)
        query = query.union(query3)

        return query

    def _get_layer_metadata_urls(self, layer: main.Layer) -> list[str]:
        metadata_urls: list[str] = []
        if layer.metadataUrls:
            metadata_urls = layer.metadataUrls
        for child_layer in layer.layers:
            metadata_urls.extend(self._get_layer_metadata_urls(child_layer))
        return metadata_urls

    def _get_layer_resolution_hint_raw(self, layer: main.Layer) -> tuple[float | None, float | None]:
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

    def _get_layer_resolution_hint(self, layer: main.Layer) -> tuple[float, float]:
        resolution_hint_min, resolution_hint_max = self._get_layer_resolution_hint_raw(layer)
        return (
            0.0 if resolution_hint_min is None else resolution_hint_min,
            999999999 if resolution_hint_max is None else resolution_hint_max,
        )

    async def _layer(
        self,
        layer: main.Layer,
        time_: TimeInformation | None = None,
        dim: DimensionInformation | None = None,
        mixed: bool = True,
    ) -> tuple[dict[str, Any] | None, set[str]]:
        errors: set[str] = set()
        layer_info = {"id": layer.id, "name": layer.name, "metadata": self._get_metadata_list(layer, errors)}
        if re.search("[/?#]", layer.name):
            errors.add(f"The layer has an unsupported name '{layer.name}'.")
        if layer.geo_table:
            errors |= self._fill_editable(layer_info, layer)
        if mixed:
            assert time_ is None
            time_ = TimeInformation()
        assert time_ is not None
        assert dim is not None

        if not isinstance(layer, main.LayerCOG):
            errors |= dim.merge(layer, layer_info, mixed)

        if isinstance(layer, main.LayerWMS):
            wms, wms_errors = await self._wms_layers(layer.ogc_server)
            errors |= wms_errors
            if wms is None:
                return None if errors else layer_info, errors
            if layer.layer is None or layer.layer == "":
                errors.add(f"The layer '{layer.name}' do not have any layers")
                return None, errors
            layer_info["type"] = "WMS"
            layer_info["layers"] = layer.layer
            await self._fill_wms(layer_info, layer, errors, mixed=mixed)
            errors |= self._merge_time(time_, layer_info, layer, wms)

        elif isinstance(layer, main.LayerWMTS):
            layer_info["type"] = "WMTS"
            self._fill_wmts(layer_info, layer, errors)

        elif isinstance(layer, main.LayerVectorTiles):
            layer_info["type"] = "VectorTiles"
            self._vectortiles_layers(layer_info, layer, errors)

        elif isinstance(layer, main.LayerCOG):
            layer_info["type"] = "COG"
            self._cog_layers(layer_info, layer, errors)

        return None if errors else layer_info, errors

    @staticmethod
    def _merge_time(
        time_: TimeInformation, layer_theme: dict[str, Any], layer: main.Layer, wms: dict[str, dict[str, Any]]
    ) -> set[str]:
        errors = set()
        wmslayer = layer.layer

        def merge_time(wms_layer_obj: dict[str, Any]) -> None:
            extent = parse_extent(wms_layer_obj["timepositions"], wms_layer_obj["defaulttimeposition"])
            time_.merge(layer_theme, extent, layer.time_mode, layer.time_widget)

        try:
            if wmslayer in wms["layers"]:
                wms_layer_obj = wms["layers"][wmslayer]

                if layer.time_mode != "disabled":
                    has_time = False
                    if wms_layer_obj["timepositions"]:
                        merge_time(wms_layer_obj)
                        has_time = True

                    else:
                        # For wms layer group, get time from the chldren.
                        for child_layer_name in wms_layer_obj["children"]:
                            child_layer = wms["layers"][child_layer_name]
                            if child_layer["timepositions"]:
                                merge_time(child_layer)  # The time mode comes from the wms layer group
                                has_time = True

                    if not has_time:
                        errors.add(
                            f"Error: time layer '{layer.name}' has no time information in capabilities"
                        )

        except ValueError:  # pragma no cover
            errors.add(f"Error while handling time for layer '{layer.name}': {sys.exc_info()[1]}")

        return errors

    def _fill_editable(self, layer_theme: dict[str, Any], layer: main.Layer) -> set[str]:
        assert models.DBSession is not None

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
                    layer_theme["edit_columns"] = get_layer_metadata(layer)
                    layer_theme["editable"] = True
        except Exception as exception:  # pylint: disable=broad-exception-caught
            _LOG.exception(str(exception))
            errors.add(str(exception))
        return errors

    def _fill_child_layer(
        self,
        layer_theme: dict[str, Any],
        layer_name: str,
        wms: dict[str, dict[str, Any]],
    ) -> None:
        wms_layer_obj = wms["layers"][layer_name]
        if not wms_layer_obj["children"]:
            layer_theme["childLayers"].append(wms["layers"][layer_name]["info"])
        else:
            for child_layer in wms_layer_obj["children"]:
                self._fill_child_layer(layer_theme, child_layer, wms)

    async def _fill_wms(
        self, layer_theme: dict[str, Any], layer: main.Layer, errors: set[str], mixed: bool
    ) -> None:
        wms, wms_errors = await self._wms_layers(layer.ogc_server)
        errors |= wms_errors
        if wms is None:
            return

        layer_theme["imageType"] = layer.ogc_server.image_type
        if layer.style:
            layer_theme["style"] = layer.style

        # now look at what is in the WMS capabilities doc
        layer_theme["childLayers"] = []
        for layer_name in layer.layer.split(","):
            if layer_name in wms["layers"]:
                self._fill_child_layer(layer_theme, layer_name, wms)
            else:
                errors.add(
                    f"The layer '{layer_name}' ({layer.name}) is not defined in WMS capabilities "
                    f"from '{layer.ogc_server.name}'"
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

    def _fill_wmts(self, layer_theme: dict[str, Any], layer: main.Layer, errors: set[str]) -> None:
        url = get_url2(f"The WMTS layer '{layer.name}'", layer.url, self.request, errors=errors)
        layer_theme["url"] = url.url() if url is not None else None

        if layer.style:
            layer_theme["style"] = layer.style
        if layer.matrix_set:
            layer_theme["matrixSet"] = layer.matrix_set

        layer_theme["layer"] = layer.layer
        layer_theme["imageType"] = layer.image_type

    def _vectortiles_layers(
        self, layer_theme: dict[str, Any], layer: main.LayerVectorTiles, errors: set[str]
    ) -> None:
        style = get_url2(f"The VectorTiles layer '{layer.name}'", layer.style, self.request, errors=errors)
        layer_theme["style"] = style.url() if style is not None else None
        if layer.xyz:
            layer_theme["xyz"] = layer.xyz

    def _cog_layers(self, layer_theme: dict[str, Any], layer: main.LayerCOG, errors: set[str]) -> None:
        url = get_url2(f"The COG layer '{layer.name}'", layer.url, self.request, errors=errors)
        layer_theme["url"] = url.url() if url is not None else None

    @staticmethod
    def _layer_included(tree_item: main.TreeItem) -> bool:
        return isinstance(tree_item, main.Layer)

    def _get_ogc_servers(self, group: main.LayerGroup, depth: int) -> set[str | bool]:
        """Get unique identifier for each child by recursing on all the children."""

        ogc_servers: set[str | bool] = set()

        # escape loop
        if depth > 30:
            _LOG.error("Error: too many recursions with group '%s'", group.name)
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

    @staticmethod
    def is_mixed(ogc_servers: list[str | bool]) -> bool:
        return len(ogc_servers) != 1 or ogc_servers[0] is False

    async def _group(
        self,
        path: str,
        group: main.LayerGroup,
        layers: list[str],
        depth: int = 1,
        min_levels: int = 1,
        mixed: bool = True,
        time_: TimeInformation | None = None,
        dim: DimensionInformation | None = None,
        wms_layers: list[str] | None = None,
        layers_name: list[str] | None = None,
        **kwargs: Any,
    ) -> tuple[dict[str, Any] | None, set[str]]:
        if wms_layers is None:
            wms_layers = []
        if layers_name is None:
            layers_name = []
        children = []
        errors = set()

        if re.search("[/?#]", group.name):
            errors.add(f"The group has an unsupported name '{group.name}'.")

        # escape loop
        if depth > 30:
            errors.add(f"Too many recursions with group '{group.name}'")
            return None, errors

        ogc_servers = None
        org_depth = depth
        if depth == 1:
            ogc_servers = list(self._get_ogc_servers(group, 1))
            # check if mixed content
            mixed = self.is_mixed(ogc_servers)
            if not mixed:
                time_ = TimeInformation()
            dim = DimensionInformation()

        for tree_item in group.children:
            if isinstance(tree_item, main.LayerGroup):
                group_theme, gp_errors = await self._group(
                    f"{path}/{tree_item.name}",
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

                    layer_theme, l_errors = await self._layer(tree_item, mixed=mixed, time_=time_, dim=dim)
                    errors |= l_errors
                    if layer_theme is not None:
                        if depth < min_levels:
                            errors.add(
                                f"The Layer '{path + '/' + tree_item.name}' is under indented "
                                f"({depth:d}/{min_levels:d})."
                            )
                        else:
                            children.append(layer_theme)

        if children:
            group_theme = {
                "id": group.id,
                "name": group.name,
                "children": children,
                "metadata": self._get_metadata_list(group, errors),
                "mixed": False,
            }
            if not mixed:
                name: str
                for name, nb in Counter(layers_name).items():
                    if nb > 1:
                        errors.add(
                            f"The GeoMapFish layer name '{name}', cannot be two times "
                            "in the same block (first level group)."
                        )

            group_theme["mixed"] = mixed
            if org_depth == 1:
                if not mixed:
                    assert time_ is not None
                    assert dim is not None
                    group_theme["ogcServer"] = cast(list[Any], ogc_servers)[0]
                    if time_.has_time() and time_.layer is None:
                        group_theme["time"] = time_.to_dict()

                    group_theme["dimensions"] = dim.get_dimensions()

            return group_theme, errors
        return None, errors

    def _layers(self, interface: str) -> list[str]:
        query = self._create_layer_query(interface=interface)
        return [name for (name,) in query.all()]

    async def _wms_layers(
        self, ogc_server: main.OGCServer
    ) -> tuple[dict[str, dict[str, Any]] | None, set[str]]:
        # retrieve layers metadata via GetCapabilities
        wms, wms_errors = await self._wms_getcap(ogc_server)
        if wms_errors:
            return None, wms_errors

        return wms, set()

    def _load_tree_items(self) -> None:
        assert models.DBSession is not None

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

    async def _themes(
        self, interface: str = "desktop", filter_themes: bool = True, min_levels: int = 1
    ) -> tuple[list[dict[str, Any]], set[str]]:
        """Return theme information for the role identified by ``role_id``."""

        assert models.DBSession is not None

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
                errors.add(f"The theme has an unsupported name '{theme.name}'.")
                continue

            children, children_errors = await self._get_children(theme, layers, min_levels)
            errors |= children_errors

            # Test if the theme is visible for the current user
            if children:
                url = (
                    get_url2(f"The Theme '{theme.name}'", theme.icon, self.request, errors)
                    if theme.icon is not None and theme.icon
                    else None
                )
                icon = (
                    url.url()
                    if url is not None
                    else self.request.static_url("/etc/geomapfish/static/images/blank.png")
                )

                theme_theme = {
                    "id": theme.id,
                    "name": theme.name,
                    "icon": icon,
                    "children": children,
                    "functionalities": self._get_functionalities(theme),
                    "metadata": self._get_metadata_list(theme, errors),
                }
                export_themes.append(theme_theme)

        return export_themes, errors

    @staticmethod
    def _get_functionalities(theme: main.Theme) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        for functionality in theme.functionalities:
            if functionality.name in result:
                result[functionality.name].append(functionality.value)
            else:
                result[functionality.name] = [functionality.value]
        return result

    @view_config(route_name="invalidate", renderer="json")  # type: ignore[misc]
    def invalidate_cache(self) -> dict[str, bool]:
        auth_view(self.request)
        models.cache_invalidate_cb()
        return {"success": True}

    async def _get_children(
        self, theme: main.Theme, layers: list[str], min_levels: int
    ) -> tuple[list[dict[str, Any]], set[str]]:
        children = []
        errors: set[str] = set()
        for item in theme.children:
            if isinstance(item, main.LayerGroup):
                group_theme, gp_errors = await self._group(
                    f"{theme.name}/{item.name}", item, layers, min_levels=min_levels
                )
                errors |= gp_errors
                if group_theme is not None:
                    children.append(group_theme)
            elif self._layer_included(item):
                if min_levels > 0:
                    errors.add(
                        f"The Layer '{item.name}' cannot be directly in the theme '{theme.name}' "
                        f"(0/{min_levels:d})."
                    )
                elif item.name in layers:
                    layer_theme, l_errors = await self._layer(item, dim=DimensionInformation())
                    errors |= l_errors
                    if layer_theme is not None:
                        children.append(layer_theme)
        return children, errors

    @_CACHE_REGION.cache_on_arguments()
    def _get_layers_enum(self) -> dict[str, dict[str, str]]:
        layers_enum = {}
        if "enum" in self.settings.get("layers", {}):
            for layer_name, layer in list(self.settings["layers"]["enum"].items()):
                layer_enum: dict[str, str] = {}
                layers_enum[layer_name] = layer_enum
                for attribute in list(layer["attributes"].keys()):
                    layer_enum[attribute] = self.request.route_url(
                        "layers_enumerate_attribute_values",
                        layer_name=layer_name,
                        field_name=attribute,
                        path="",
                    )
        return layers_enum

    def _get_role_ids(self) -> set[int] | None:
        return None if self.request.user is None else {role.id for role in self.request.user.roles}

    async def _wfs_get_features_type(
        self, wfs_url: Url, ogc_server: main.OGCServer, preload: bool = False, cache: bool = True
    ) -> tuple[Optional[etree.Element], set[str]]:  # pylint: disable=c-extension-no-member
        errors = set()

        wfs_url = wfs_url.clone()
        wfs_url.add_query(
            {
                "SERVICE": "WFS",
                "VERSION": "1.0.0",
                "REQUEST": "DescribeFeatureType",
                "ROLE_IDS": "0",
                "USER_ID": "0",
            }
        )

        _LOG.debug("WFS DescribeFeatureType for the URL: %s", wfs_url.url())

        headers = {}

        # Add headers for Geoserver
        if ogc_server.auth == main.OGCSERVER_AUTH_GEOSERVER:
            headers["sec-username"] = "root"
            headers["sec-roles"] = "root"

        try:
            content, _ = await get_http_cached(self.http_options, wfs_url.url(), headers, cache)
        except requests.exceptions.RequestException as exception:
            error = (
                f"Unable to get WFS DescribeFeatureType from the URL '{wfs_url.url()}' for "
                f"OGC server {ogc_server.name}, "
                + (
                    f"return the error: {exception.response.status_code} {exception.response.reason}"
                    if exception.response is not None
                    else f"{exception}"
                )
            )
            errors.add(error)
            _LOG.exception(error)
            return None, errors
        except Exception:  # pylint: disable=broad-exception-caught
            error = (
                f"Unable to get WFS DescribeFeatureType from the URL {wfs_url} for "
                f"OGC server {ogc_server.name}"
            )
            errors.add(error)
            _LOG.exception(error)
            return None, errors

        if preload:
            return None, errors

        try:
            return lxml.XML(content), errors
        except Exception as e:  # pylint: disable=broad-except
            errors.add(
                f"Error '{e!s}' on reading DescribeFeatureType from URL {wfs_url}:\n{content.decode()}"
            )
            return None, errors

    def get_url_internal_wfs(
        self, ogc_server: main.OGCServer, errors: set[str]
    ) -> tuple[Url | None, Url | None, Url | None]:
        # required to do every time to validate the url.
        if ogc_server.auth != main.OGCSERVER_AUTH_NOAUTH:
            url: Url | None = Url(
                self.request.route_url("mapserverproxy", _query={"ogcserver": ogc_server.name})
            )
            url_wfs: Url | None = url
            url_internal_wfs = get_url2(
                f"The OGC server (WFS) '{ogc_server.name}'",
                ogc_server.url_wfs or ogc_server.url,
                self.request,
                errors=errors,
            )
        else:
            url = get_url2(f"The OGC server '{ogc_server.name}'", ogc_server.url, self.request, errors=errors)
            url_wfs = (
                get_url2(
                    f"The OGC server (WFS) '{ogc_server.name}'",
                    ogc_server.url_wfs,
                    self.request,
                    errors=errors,
                )
                if ogc_server.url_wfs is not None
                else url
            )
            url_internal_wfs = url_wfs
        return url_internal_wfs, url, url_wfs

    async def _preload(self, errors: set[str]) -> None:
        assert models.DBSession is not None
        tasks = set()

        for ogc_server, nb_layers in (
            models.DBSession.query(
                main.OGCServer, sqlalchemy.func.count(main.LayerWMS.id)  # pylint: disable=not-callable
            )
            .filter(main.LayerWMS.ogc_server_id == main.OGCServer.id)
            .group_by(main.OGCServer.id)
            .all()
        ):
            # Don't load unused OGC servers, required for landing page, because the related OGC server
            # will be on error in those functions.
            _LOG.debug("%i layers for OGC server '%s'", nb_layers, ogc_server.name)
            if nb_layers > 0:
                _LOG.debug("Preload OGC server '%s'", ogc_server.name)
                url_internal_wfs, _, _ = self.get_url_internal_wfs(ogc_server, errors)
                if url_internal_wfs is not None:
                    tasks.add(self.preload_ogc_server(ogc_server, url_internal_wfs))

        await asyncio.gather(*tasks)

    async def preload_ogc_server(
        self, ogc_server: main.OGCServer, url_internal_wfs: Url, cache: bool = True
    ) -> None:
        if ogc_server.wfs_support:
            await self._get_features_attributes(url_internal_wfs, ogc_server, cache=cache)
        await self._wms_getcap(ogc_server, False, cache=cache)

    async def _get_features_attributes(
        self, url_internal_wfs: Url, ogc_server: main.OGCServer, cache: bool = True
    ) -> tuple[dict[str, dict[Any, dict[str, Any]]] | None, str | None, set[str]]:
        @_CACHE_OGC_SERVER_REGION.cache_on_arguments()
        def _get_features_attributes_cache(
            url_internal_wfs: Url, ogc_server_name: str
        ) -> tuple[dict[str, dict[Any, dict[str, Any]]] | None, str | None, set[str]]:
            del url_internal_wfs  # Just for cache
            all_errors: set[str] = set()
            if errors:
                all_errors |= errors
                return None, None, all_errors
            assert feature_type is not None
            namespace: str = feature_type.attrib.get("targetNamespace")
            types: dict[Any, dict[str, Any]] = {}
            elements = {}
            for child in feature_type.getchildren():
                if child.tag == "{http://www.w3.org/2001/XMLSchema}element":
                    name = child.attrib["name"]
                    type_namespace, type_ = child.attrib["type"].split(":")
                    if type_namespace not in child.nsmap:
                        _LOG.info(
                            "The namespace '%s' of the type '%s' is not found in the "
                            "available namespaces: %s (OGC server: %s)",
                            type_namespace,
                            name,
                            ", ".join([str(k) for k in child.nsmap.keys()]),
                            ogc_server_name,
                        )
                    elif child.nsmap[type_namespace] != namespace:
                        _LOG.info(
                            "The namespace '%s' of the type '%s' should be '%s' (OGC server: %s).",
                            child.nsmap[type_namespace],
                            name,
                            namespace,
                            ogc_server_name,
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
                        name = children.attrib["name"]
                        attrib[name] = {"type": type_}
                        if type_namespace in children.nsmap:
                            type_namespace = children.nsmap[type_namespace]
                            attrib[name]["namespace"] = type_namespace
                        else:
                            _LOG.info(
                                "The namespace '%s' of the type '%s' is not found in the "
                                "available namespaces: %s (OGC server: %s)",
                                type_namespace,
                                name,
                                ", ".join([str(k) for k in child.nsmap.keys()]),
                                ogc_server_name,
                            )
                        for key, value in children.attrib.items():
                            if key not in ("name", "type", "namespace"):
                                attrib[name][key] = value
                    types[child.attrib["name"]] = attrib
            attributes: dict[str, dict[Any, dict[str, Any]]] = {}
            for name, type_ in elements.items():
                if type_ in types:
                    attributes[name] = types[type_]
                elif (type_ == "Character") and (name + "Type") in types:
                    _LOG.debug(
                        'Due to MapServer weird behavior when using METADATA "gml_types" "auto"'
                        "the type 'ms:Character' is returned as type '%sType' for feature '%s'.",
                        name,
                        name,
                    )
                    attributes[name] = types[name + "Type"]
                else:
                    _LOG.warning(
                        "The provided type '%s' does not exist, available types are %s.",
                        type_,
                        ", ".join(types.keys()),
                    )

            return attributes, namespace, all_errors

        if cache:
            result = _get_features_attributes_cache.get(  # type: ignore[attr-defined]
                url_internal_wfs,
                ogc_server.name,
            )
            if result != dogpile.cache.api.NO_VALUE:
                return result  # type: ignore[no-any-return]

        feature_type, errors = await self._wfs_get_features_type(url_internal_wfs, ogc_server, False, cache)

        return _get_features_attributes_cache.refresh(  # type: ignore[attr-defined,no-any-return]
            url_internal_wfs,
            ogc_server.name,
        )

    @view_config(route_name="themes", renderer="json")  # type: ignore[misc]
    def themes(self) -> dict[str, dict[str, dict[str, Any]] | list[str]]:

        is_allowed_host(self.request)

        interface = self.request.params.get("interface", "desktop")
        sets = self.request.params.get("set", "all")
        min_levels = int(self.request.params.get("min_levels", 1))
        group = self.request.params.get("group")
        background_layers_group = self.request.params.get("background")

        set_common_headers(self.request, "themes", Cache.PRIVATE)

        async def get_theme() -> dict[str, dict[str, Any] | list[str]]:
            assert models.DBSession is not None

            export_themes = sets in ("all", "themes")
            export_group = group is not None and sets in ("all", "group")
            export_background = background_layers_group is not None and sets in ("all", "background")

            result: dict[str, dict[str, Any] | list[Any]] = {}
            all_errors: set[str] = set()
            _LOG.debug("Start preload")
            start_time = time.time()
            await self._preload(all_errors)
            _LOG.debug("End preload")
            # Don't log if it looks to be already preloaded.
            if (time.time() - start_time) > 1:
                _LOG.info("Do preload in %.3fs.", time.time() - start_time)
            _LOG.debug("Run garbage collection: %s", ", ".join([str(gc.collect(n)) for n in range(3)]))
            result["ogcServers"] = {}
            for ogc_server, nb_layers in (
                models.DBSession.query(
                    main.OGCServer, sqlalchemy.func.count(main.LayerWMS.id)  # pylint: disable=not-callable
                )
                .filter(main.LayerWMS.ogc_server_id == main.OGCServer.id)
                .group_by(main.OGCServer.id)
                .all()
            ):
                if nb_layers == 0:
                    # QGIS Server landing page requires an OGC server that can't be used here.
                    continue

                _LOG.debug("Process OGC server '%s'", ogc_server.name)

                url_internal_wfs, url, url_wfs = self.get_url_internal_wfs(ogc_server, all_errors)

                attributes = None
                namespace = None
                if ogc_server.wfs_support and not url_internal_wfs:
                    all_errors.add(
                        f"The OGC server '{ogc_server.name}' is configured to support WFS "
                        "but no internal WFS URL is found."
                    )
                if ogc_server.wfs_support and url_internal_wfs:
                    attributes, namespace, errors = await self._get_features_attributes(
                        url_internal_wfs, ogc_server
                    )
                    # Create a local copy (don't modify the cache)
                    if attributes is not None:
                        attributes = dict(attributes)
                    all_errors |= errors

                    all_private_layers = get_private_layers([ogc_server.id]).values()
                    protected_layers_name = [
                        layer.name for layer in get_protected_layers(self.request, [ogc_server.id]).values()
                    ]
                    private_layers_name: list[str] = []
                    for layers in [
                        v.layer for v in all_private_layers if v.name not in protected_layers_name
                    ]:
                        private_layers_name.extend(layers.split(","))

                    if attributes is not None:
                        for name in private_layers_name:
                            if name in attributes:
                                del attributes[name]

                result["ogcServers"][ogc_server.name] = {
                    "url": url.url() if url else None,
                    "urlWfs": url_wfs.url() if url_wfs else None,
                    "type": ogc_server.type,
                    "credential": ogc_server.auth != main.OGCSERVER_AUTH_NOAUTH,
                    "imageType": ogc_server.image_type,
                    "wfsSupport": ogc_server.wfs_support,
                    "isSingleTile": ogc_server.is_single_tile,
                    "namespace": namespace,
                    "attributes": attributes,
                }
            if export_themes:
                themes, errors = await self._themes(interface, True, min_levels)

                result["themes"] = themes
                all_errors |= errors

            if export_group:
                exported_group, errors = await self._get_group(group, interface)
                if exported_group is not None:
                    result["group"] = exported_group
                all_errors |= errors

            if export_background:
                exported_group, errors = await self._get_group(background_layers_group, interface)
                result["background_layers"] = exported_group["children"] if exported_group is not None else []
                all_errors |= errors

            result["errors"] = list(all_errors)
            if all_errors:
                _LOG.info("Theme errors:\n%s", "\n".join(all_errors))
            return result

        @_CACHE_REGION.cache_on_arguments()
        def get_theme_anonymous(
            intranet: bool,
            interface: str,
            sets: str,
            min_levels: str,
            group: str,
            background_layers_group: str,
            host: str,
        ) -> dict[str, dict[str, dict[str, Any]] | list[str]]:
            # Only for cache key
            del intranet, interface, sets, min_levels, group, background_layers_group, host
            return asyncio.run(get_theme())

        if self.request.user is None:
            return cast(
                dict[str, Union[dict[str, dict[str, Any]], list[str]]],
                get_theme_anonymous(
                    is_intranet(self.request),
                    interface,
                    sets,
                    min_levels,
                    group,
                    background_layers_group,
                    self.request.headers.get("Host"),
                ),
            )
        return asyncio.run(get_theme())

    async def _get_group(
        self, group: main.LayerGroup, interface: main.Interface
    ) -> tuple[dict[str, Any] | None, set[str]]:
        assert models.DBSession is not None

        layers = self._layers(interface)
        try:
            group_db = models.DBSession.query(main.LayerGroup).filter(main.LayerGroup.name == group).one()  # type: ignore[arg-type]
            assert isinstance(group_db, main.LayerGroup)
            return await self._group(group_db.name, group_db, layers, depth=2, dim=DimensionInformation())
        except NoResultFound:
            return (
                None,
                {
                    f"Unable to find the Group named: {group}, Available Groups: "
                    f"{', '.join([i[0] for i in models.DBSession.query(main.LayerGroup.name).all()])}"
                },
            )

    @view_config(route_name="ogc_server_clear_cache", renderer="json")  # type: ignore[misc]
    def ogc_server_clear_cache_view(self) -> dict[str, Any]:
        assert models.DBSession is not None

        if not self.request.user:
            raise pyramid.httpexceptions.HTTPForbidden()

        admin_roles = [r for r in self.request.user.roles if r.name == ("role_admin")]
        if not admin_roles:
            raise pyramid.httpexceptions.HTTPForbidden()

        self._ogc_server_clear_cache(
            models.DBSession.query(main.OGCServer).filter_by(id=self.request.matchdict.get("id")).one()
        )
        came_from = self.request.params.get("came_from")
        allowed_hosts = self.request.registry.settings.get("admin_interface", {}).get("allowed_hosts", [])
        came_from_hostname, ok = is_allowed_url(self.request, came_from, allowed_hosts)
        if not ok:
            message = (
                f"Invalid hostname '{came_from_hostname}' in 'came_from' parameter, "
                f"is not the current host '{self.request.host}' "
                f"or part of allowed hosts: {', '.join(allowed_hosts)}"
            )
            _LOG.debug(message)
            raise pyramid.httpexceptions.HTTPBadRequest(message)
        if came_from:
            raise pyramid.httpexceptions.HTTPFound(location=came_from)
        return {"success": True}

    def _ogc_server_clear_cache(self, ogc_server: main.OGCServer) -> None:
        errors: set[str] = set()
        url_internal_wfs, _, _ = self.get_url_internal_wfs(ogc_server, errors)
        if errors:
            _LOG.error(
                "Error while getting the URL of the OGC Server %s:\n%s", ogc_server.id, "\n".join(errors)
            )
            return
        if url_internal_wfs is None:
            return

        asyncio.run(self._async_cache_invalidate_ogc_server_cb(ogc_server, url_internal_wfs))

    async def _async_cache_invalidate_ogc_server_cb(
        self, ogc_server: main.OGCServer, url_internal_wfs: Url
    ) -> None:
        # Fill the cache
        await self.preload_ogc_server(ogc_server, url_internal_wfs, False)

        cache_invalidate_cb()
