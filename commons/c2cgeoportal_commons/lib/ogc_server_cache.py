# Copyright (c) 2022, Camptocamp SA
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
from math import sqrt
from typing import Any, Dict, Optional, Set, Tuple

import dogpile.cache.api
import pyramid.httpexceptions
import pyramid.request
import requests
from defusedxml import lxml
from lxml import etree  # nosec
from owslib.wms import WebMapService

from c2cgeoportal_commons.lib.caching import get_region
from c2cgeoportal_commons.lib.functionality import get_mapserver_substitution_params
from c2cgeoportal_commons.lib.url import Url, get_url2
from c2cgeoportal_commons.models import cache_invalidate_cb, main

_LOG = logging.getLogger(__name__)
_CACHE_OGC_SERVER_REGION = get_region("ogc-server")
_TIMEOUT = int(os.environ.get("C2CGEOPORTAL_THEME_TIMEOUT", "300"))


def _get_http_cached(
    http_options: Dict[str, Any], url: str, headers: Dict[str, str], cache: bool = True
) -> Tuple[bytes, str]:
    """Get the content of the URL with a cash (dogpile)."""

    @_CACHE_OGC_SERVER_REGION.cache_on_arguments()  # type: ignore
    def do_get_http_cached(url: str) -> Tuple[bytes, str]:
        response = requests.get(url, headers=headers, timeout=_TIMEOUT, **http_options)
        response.raise_for_status()
        _LOG.info("Get url '%s' in %.1fs.", url, response.elapsed.total_seconds())
        return response.content, response.headers.get("Content-Type", "")

    if cache:
        return do_get_http_cached(url)  # type: ignore
    return do_get_http_cached.refresh(url)  # type: ignore


def _get_layer_resolution_hint_raw(layer: main.Layer) -> Tuple[Optional[float], Optional[float]]:
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
        resolution = _get_layer_resolution_hint_raw(child_layer)
        resolution_hint_min = (
            resolution[0]
            if resolution_hint_min is None
            else (resolution_hint_min if resolution[0] is None else min(resolution_hint_min, resolution[0]))
        )
        resolution_hint_max = (
            resolution[1]
            if resolution_hint_max is None
            else (resolution_hint_max if resolution[1] is None else max(resolution_hint_max, resolution[1]))
        )

    return (resolution_hint_min, resolution_hint_max)


def _get_layer_resolution_hint(layer: main.Layer) -> Tuple[float, float]:
    resolution_hint_min, resolution_hint_max = _get_layer_resolution_hint_raw(layer)
    return (
        0.0 if resolution_hint_min is None else resolution_hint_min,
        999999999 if resolution_hint_max is None else resolution_hint_max,
    )


async def wms_getcap(
    request: pyramid.request.Request,
    http_options: Dict[str, Any],
    ogc_server: main.OGCServer,
    preload: bool = False,
    cache: bool = True,
) -> Tuple[Optional[Dict[str, Dict[str, Any]]], Set[str]]:
    """
    Get the WMS capabilities.

    Returns

        layers: dict of layers
        errors: set of errors
    """

    @_CACHE_OGC_SERVER_REGION.cache_on_arguments()  # type: ignore
    def build_web_map_service(ogc_server_id: int) -> Tuple[Optional[Dict[str, Dict[str, Any]]], Set[str]]:
        del ogc_server_id  # Just for cache

        if url is None:
            raise RuntimeError("URL is None")

        version = url.query.get("VERSION", "1.1.1")
        layers = {}
        try:
            wms = WebMapService(None, xml=content, version=version)
        except Exception as e:
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
            resolution = _get_layer_resolution_hint(wms_layer)
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
        _LOG.debug("Run garbage collection: %s", ", ".join([str(gc.collect(n)) for n in range(3)]))

        return {"layers": layers}, set()

    if cache:
        result = build_web_map_service.get(ogc_server.id)
        if result != dogpile.cache.api.NO_VALUE:
            return result  # type: ignore

    try:
        url, content, errors = await _wms_getcap_cached(request, http_options, ogc_server, cache=cache)
    except requests.exceptions.RequestException as exception:
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
    request: pyramid.request.Request,
    http_options: Dict[str, Any],
    ogc_server: main.OGCServer,
    cache: bool = True,
) -> Tuple[Optional[Url], Optional[bytes], Set[str]]:
    errors: Set[str] = set()
    url = get_url2(f"The OGC server '{ogc_server.name}'", ogc_server.url, request, errors)
    if errors or url is None:
        return url, None, errors

    # Add functionality params
    if ogc_server.auth == main.OGCSERVER_AUTH_STANDARD and ogc_server.type == main.OGCSERVER_TYPE_MAPSERVER:
        url.add_query(get_mapserver_substitution_params(request))

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
        content, content_type = _get_http_cached(http_options, url.url(), headers, cache=cache)
    except Exception:
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


async def preload_ogc_server(
    request: pyramid.request.Request,
    http_options: Dict[str, Any],
    ogc_server: main.OGCServer,
    url_internal_wfs: Url,
    cache: bool = True,
) -> None:
    """
    Preload the OGC servers.
    """
    if ogc_server.wfs_support:
        await get_features_attributes(http_options, url_internal_wfs, ogc_server, cache=cache)
    await wms_getcap(request, http_options, ogc_server, True, cache=cache)


async def get_features_attributes(
    http_options: Dict[str, Any], url_internal_wfs: Url, ogc_server: main.OGCServer, cache: bool = True
) -> Tuple[Optional[Dict[str, Dict[Any, Dict[str, Any]]]], Optional[str], Set[str]]:
    """
    Get the features attributes.

    Returns

      attributes: The attributes
      namespace: The server namespace
      all_errors
    """

    @_CACHE_OGC_SERVER_REGION.cache_on_arguments()  # type: ignore
    def _get_features_attributes_cache(
        url_internal_wfs: Url, ogc_server_name: str
    ) -> Tuple[Optional[Dict[str, Dict[Any, Dict[str, Any]]]], Optional[str], Set[str]]:
        del url_internal_wfs, ogc_server_name  # Just for cache
        all_errors: Set[str] = set()
        _LOG.debug("Run garbage collection: %s", ", ".join([str(gc.collect(n)) for n in range(3)]))
        if errors:
            all_errors |= errors
            return None, None, all_errors
        assert feature_type is not None
        namespace: str = feature_type.attrib.get("targetNamespace")
        types: Dict[Any, Dict[str, Any]] = {}
        elements = {}
        for child in feature_type.getchildren():
            if child.tag == "{http://www.w3.org/2001/XMLSchema}element":
                name = child.attrib["name"]
                type_namespace, type_ = child.attrib["type"].split(":")
                if type_namespace not in child.nsmap:
                    _LOG.info(
                        "The namespace '%s' of the type '%s' is not found in the available namespaces: %s",
                        type_namespace,
                        name,
                        ", ".join(child.nsmap.keys()),
                    )
                if child.nsmap[type_namespace] != namespace:
                    _LOG.info(
                        "The namespace '%s' of the type '%s' should be '%s'.",
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
        attributes: Dict[str, Dict[Any, Dict[str, Any]]] = {}
        for name, type_ in elements.items():
            if type_ in types:
                attributes[name] = types[type_]
            elif (type_ == "Character") and (name + "Type") in types:
                _LOG.debug(
                    "Due MapServer strange result the type 'ms:Character' is fall backed to type '%sType'"
                    " for feature '%s', This is a wired behavior of MapServer when we use the "
                    'METADATA "gml_types" "auto"',
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
        result = _get_features_attributes_cache.get(url_internal_wfs, ogc_server.name)
        if result != dogpile.cache.api.NO_VALUE:
            return result  # type: ignore

    feature_type, errors = await _wfs_get_features_type(http_options, url_internal_wfs, ogc_server)
    return _get_features_attributes_cache.refresh(url_internal_wfs, ogc_server.name)  # type: ignore


async def _wfs_get_features_type(
    http_options: Dict[str, Any],
    wfs_url: Url,
    ogc_server: main.OGCServer,
    preload: bool = False,
    cache: bool = True,
) -> Tuple[Optional[etree.Element], Set[str]]:
    errors = set()

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
        content, _ = _get_http_cached(http_options, wfs_url.url(), headers, cache)
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
    except Exception:
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
    except Exception as e:
        errors.add(f"Error '{e!s}' on reading DescribeFeatureType from URL {wfs_url}:\n{content.decode()}")
        return None, errors


def get_url_internal_wfs(
    request: pyramid.request.Request, ogc_server: main.OGCServer, errors: Set[str]
) -> Tuple[Optional[Url], Optional[Url], Optional[Url]]:
    """
    Get the internal WFS URL for the OGC server.

    Returns

      url_internal_wfs: The internal WFS URL.
      url: The public WMS URL.
      url_wfs: The public WFS URL.
    """
    # required to do every time to validate the url.
    if ogc_server.auth != main.OGCSERVER_AUTH_NOAUTH:
        url: Optional[Url] = Url(request.route_url("mapserverproxy", _query={"ogcserver": ogc_server.name}))
        url_wfs: Optional[Url] = url
        url_internal_wfs = get_url2(
            f"The OGC server (WFS) '{ogc_server.name}'",
            ogc_server.url_wfs or ogc_server.url,
            request,
            errors=errors,
        )
    else:
        url = get_url2(f"The OGC server '{ogc_server.name}'", ogc_server.url, request, errors=errors)
        url_wfs = (
            get_url2(
                f"The OGC server (WFS) '{ogc_server.name}'",
                ogc_server.url_wfs,
                request,
                errors=errors,
            )
            if ogc_server.url_wfs is not None
            else url
        )
        url_internal_wfs = url_wfs
    return url_internal_wfs, url, url_wfs


def ogcserver_clear_cache(
    request: pyramid.request.Request, http_options: Dict[str, Any], ogc_server: main.OGCServer
) -> None:
    """
    Regenerate the cache for the given OGC server.
    """
    errors: Set[str] = set()
    url_internal_wfs, _, _ = get_url_internal_wfs(request, ogc_server, errors)
    if errors:
        _LOG.error("Error while getting the URL of the OGC Server %s:\n%s", ogc_server.id, "\n".join(errors))
        return
    if url_internal_wfs is None:
        return

    asyncio.run(_async_cache_invalidate_ogc_server_cb(request, http_options, ogc_server, url_internal_wfs))


async def _async_cache_invalidate_ogc_server_cb(
    request: pyramid.request.Request,
    http_options: Dict[str, Any],
    ogc_server: main.OGCServer,
    url_internal_wfs: Url,
) -> None:

    # Fill the cache
    await preload_ogc_server(request, http_options, ogc_server, url_internal_wfs, False)

    cache_invalidate_cb()
