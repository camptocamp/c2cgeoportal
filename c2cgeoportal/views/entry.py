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
import urllib
import logging
import json
import sys

from random import Random
from math import sqrt
from xml.dom.minidom import parseString
from urlparse import urlsplit

from pyramid.view import view_config
from pyramid.i18n import get_locale_name, TranslationStringFactory
from pyramid.httpexceptions import HTTPFound, HTTPNotFound, \
    HTTPBadRequest, HTTPUnauthorized, HTTPForbidden, HTTPBadGateway
from pyramid.security import remember, forget
from pyramid.response import Response
from sqlalchemy.orm.exc import NoResultFound
from owslib.wms import WebMapService

from c2cgeoportal.lib import get_setting, get_protected_layers_query, get_url, add_url_params
from c2cgeoportal.lib.cacheversion import get_cache_version
from c2cgeoportal.lib.caching import get_region, invalidate_region,  \
    set_common_headers, NO_CACHE, PUBLIC_CACHE, PRIVATE_CACHE
from c2cgeoportal.lib.functionality import get_functionality, \
    get_mapserver_substitution_params
from c2cgeoportal.lib.wmstparsing import parse_extent, TimeInformation
from c2cgeoportal.lib.email_ import send_email
from c2cgeoportal.models import DBSession, User, Role, \
    Theme, LayerGroup, RestrictionArea, Interface, \
    Layer, LayerV1, LayerInternalWMS, LayerExternalWMS, LayerWMTS


_ = TranslationStringFactory("c2cgeoportal")
log = logging.getLogger(__name__)
cache_region = get_region()


class Entry(object):

    WFS_NS = "http://www.opengis.net/wfs"

    def __init__(self, request):
        self.request = request
        self.settings = request.registry.settings
        self.mapserver_settings = self.settings.get("mapserverproxy", {})
        self.debug = "debug" in request.params
        self.lang = get_locale_name(request)

    @view_config(route_name="testi18n", renderer="testi18n.html")
    def testi18n(self):  # pragma: no cover
        _ = self.request.translate
        return {"title": _("title i18n")}

    def _wms_getcap(self, url):
        if url.find("?") < 0:
            url += "?"

        # add functionalities params
        sparams = get_mapserver_substitution_params(self.request)
        if sparams:  # pragma: no cover
            url += urllib.urlencode(sparams) + "&"

        return self._wms_getcap_cached(
            url, self._get_role_id() if self.mapserver_settings["geoserver"] else None
        )

    @cache_region.cache_on_arguments()
    def _wms_getcap_cached(self, url, role_id):
        """ role_id is just for cache """

        errors = set()
        wms = None

        url = add_url_params(url, {
            "SERVICE": "WMS",
            "VERSION": "1.1.1",
            "REQUEST": "GetCapabilities",
        })

        log.info("Get WMS GetCapabilities for url: %s" % url)

        # forward request to target (without Host Header)
        http = httplib2.Http()
        headers = dict(self.request.headers)

        role = None if self.request.user is None else self.request.user.role

        # Add headers for Geoserver
        if self.mapserver_settings["geoserver"] and self.request.user is not None:
            headers["sec-username"] = self.request.user.username
            headers["sec-roles"] = role.name

        if urlsplit(url).hostname != "localhost":  # pragma: no cover
            headers.pop("Host")
        try:
            resp, content = http.request(url, method="GET", headers=headers)
        except:  # pragma: no cover
            errors.add("Unable to GetCapabilities from url %s" % url)
            return None, errors

        if resp.status < 200 or resp.status >= 300:  # pragma: no cover
            errors.add(
                "GetCapabilities from url %s return the error: %i %s" %
                (url, resp.status, resp.reason)
            )
            return None, errors

        try:
            wms = WebMapService(None, xml=content)
        except AttributeError:
            error = _(
                "WARNING! an error occured while trying to "
                "read the mapfile and recover the themes."
            )
            error = "%s\nurl: %s\nxml:\n%s" % (error, url, content)
            errors.add(error)
            log.exception(error)
        return wms, errors

    def _create_layer_query(self, role_id, version):
        """ Create an SQLAlchemy query for Layer and for the role
            identified to by ``role_id``.
        """

        if version == 1:
            q = DBSession.query(LayerV1)
        else:
            q = DBSession.query(Layer).with_polymorphic(
                [LayerInternalWMS, LayerExternalWMS, LayerWMTS]
            )

        q = q.filter(Layer.public.is_(True))
        if role_id is not None:
            q = q.union(get_protected_layers_query(role_id, version=version))

        return q

    def _get_layer_metadata_urls(self, layer):
        metadata_urls = []
        if len(layer.metadataUrls) > 0:
            metadata_urls = layer.metadataUrls
        for childLayer in layer.layers:
            metadata_urls.extend(self._get_layer_metadata_urls(childLayer))
        return metadata_urls

    def _get_layer_resolution_hint(self, layer):
        resolution_hint_min = float("inf")
        resolution_hint_max = 0
        if layer.scaleHint:
            # scaleHint is based upon a pixel diagonal length whereas we use
            # resolutions based upon a pixel edge length. There is a sqrt(2)
            # ratio between edge and diagonal of a square.
            resolution_hint_min = float(layer.scaleHint["min"]) / sqrt(2)
            resolution_hint_max = float(layer.scaleHint["max"]) / sqrt(2)
        for childLayer in layer.layers:
            resolution = self._get_layer_resolution_hint(childLayer)
            resolution_hint_min = min(resolution_hint_min, resolution[0])
            resolution_hint_max = max(resolution_hint_max, resolution[1])

        return (resolution_hint_min, resolution_hint_max)

    def _get_child_layers_info(self, layer):
        """ Return information about sub layers of a layer.

            Arguments:

            * ``layer`` The layer object in the WMS capabilities.
        """
        child_layers_info = []
        for child_layer in layer.layers:
            child_layer_info = dict(name=child_layer.name)
            resolution = self._get_layer_resolution_hint(child_layer)
            if resolution[0] <= resolution[1]:
                child_layer_info.update({
                    "minResolutionHint": float("%0.2f" % resolution[0]),
                    "maxResolutionHint": float("%0.2f" % resolution[1])
                })
            if hasattr(child_layer, "queryable"):
                child_layer_info["queryable"] = child_layer.queryable
            child_layers_info.append(child_layer_info)
        return child_layers_info

    def _layer(self, layer, wms, wms_layers, time):
        errors = set()
        l = {
            "id": layer.id,
            "name": layer.name,
            "metadata": {}
        }
        for metadata in layer.ui_metadata:
            l["metadata"][metadata.name] = get_url(metadata.value, self.request, errors=errors)
        if layer.geo_table:
            self._fill_editable(l, layer)

        if isinstance(layer, LayerV1):
            l.update({
                "type": layer.layer_type,
                "public": layer.public,
                "legend": layer.legend,
                "isChecked": layer.is_checked,
                "isLegendExpanded": layer.is_legend_expanded,
            })
            if layer.identifier_attribute_field:
                l["identifierAttribute"] = layer.identifier_attribute_field
            if layer.disclaimer:
                l["disclaimer"] = layer.disclaimer
            if layer.icon:
                l["icon"] = get_url(layer.icon, self.request, errors=errors)
            if layer.kml:
                l["kml"] = get_url(layer.kml, self.request, errors=errors)
            if layer.metadata_url:
                l["metadataURL"] = layer.metadata_url
            if layer.legend_image:
                l["legendImage"] = get_url(layer.legend_image, self.request, errors=errors)

            if layer.layer_type == "internal WMS":
                if not self._fill_internal_wms(l, layer, wms, wms_layers, errors):
                    return None, set()
                errors |= self._merge_time(time, l, layer, wms, wms_layers)
            elif layer.layer_type == "external WMS":
                self._fill_external_wms(l, layer, errors)
            elif layer.layer_type == "WMTS":
                self._fill_wmts(l, layer, wms, wms_layers, errors)
        elif isinstance(layer, LayerInternalWMS):
            l["type"] = "internal WMS"
            l["layers"] = layer.layer
            if not self._fill_internal_wms(l, layer, wms, wms_layers, errors, version=2):
                return None, set()
            errors |= self._merge_time(time, l, layer, wms, wms_layers)
        elif isinstance(layer, LayerExternalWMS):
            l["type"] = "external WMS"
            l["layers"] = layer.layer
            self._fill_external_wms(l, layer, errors, version=2)
        elif isinstance(layer, LayerWMTS):
            l["type"] = "WMTS"
            self._fill_wmts(l, layer, wms, wms_layers, errors, version=2)

        return l, errors

    def _merge_time(self, time, l, layer, wms, wms_layers):
        errors = set()
        wmslayer = layer.name if isinstance(layer, LayerV1) else layer.layer
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
                "Error while handling time for layer '%s': %s"
                % (layer.name, sys.exc_info()[1])
            )

        return errors

    def _fill_editable(self, l, layer):
        if self.request.user:
            c = DBSession.query(RestrictionArea) \
                .filter(RestrictionArea.roles.any(
                    Role.id == self.request.user.role.id)) \
                .filter(RestrictionArea.layers.any(Layer.id == layer.id)) \
                .filter(RestrictionArea.readwrite.is_(True)) \
                .count()
            if c > 0:
                l["editable"] = True

    def _fill_wms(self, l, layer, version=1):
        l["imageType"] = layer.image_type
        if version == 1 and layer.legend_rule:
            l["icon"] = add_url_params(self.request.route_url("mapserverproxy"), {
                "SERVICE": "WMS",
                "VERSION": "1.1.1",
                "REQUEST": "GetLegendGraphic",
                "LAYER": layer.name,
                "FORMAT": "image/png",
                "TRANSPARENT": "TRUE",
                "RULE": layer.legend_rule,
            })
        if layer.style:
            l["style"] = layer.style

    def _fill_legend_rule_query_string(self, l, layer, url):
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

    def _fill_internal_wms(self, l, layer, wms, wms_layers, errors, version=1):
        self._fill_wms(l, layer, version=version)

        if version == 1:
            self._fill_legend_rule_query_string(
                l, layer,
                self.request.route_url("mapserverproxy")
            )

            # this is a leaf, ie. a Mapserver layer
            if layer.min_resolution is not None:
                l["minResolutionHint"] = layer.min_resolution
            if layer.max_resolution is not None:
                l["maxResolutionHint"] = layer.max_resolution

        wmslayer = layer.name if version == 1 else layer.layer
        # now look at what's in the WMS capabilities doc
        if wmslayer in wms_layers:
            wms_layer_obj = wms[wmslayer]
            metadata_urls = self._get_layer_metadata_urls(wms_layer_obj)
            if len(metadata_urls) > 0:
                l["metadataUrls"] = metadata_urls
            resolutions = self._get_layer_resolution_hint(wms_layer_obj)
            if resolutions[0] <= resolutions[1]:
                if "minResolutionHint" not in l:
                    l["minResolutionHint"] = float("%0.2f" % resolutions[0])
                if "maxResolutionHint" not in l:
                    l["maxResolutionHint"] = float("%0.2f" % resolutions[1])
            l["childLayers"] = self._get_child_layers_info(wms_layer_obj)
            if hasattr(wms_layer_obj, "queryable"):
                l["queryable"] = wms_layer_obj.queryable
        else:
            if self.mapserver_settings["geoserver"]:
                return False
            else:
                errors.add(
                    "The layer '%s' is not defined in WMS capabilities" % wmslayer
                )
        return True

    def _fill_external_wms(self, l, layer, errors, version=1):
        self._fill_wms(l, layer, version=version)
        if version == 1:
            self._fill_legend_rule_query_string(l, layer, layer.url)

            if layer.min_resolution is not None:
                l["minResolutionHint"] = layer.min_resolution
            if layer.max_resolution is not None:
                l["maxResolutionHint"] = layer.max_resolution

        l["url"] = get_url(layer.url, self.request, errors=errors)
        l["isSingleTile"] = layer.is_single_tile

    def _fill_wmts(self, l, layer, wms, wms_layers, errors, version=1):
        l["url"] = get_url(layer.url, self.request, errors=errors)

        if layer.style:
            l["style"] = layer.style
        if layer.matrix_set:
            l["matrixSet"] = layer.matrix_set

        if version == 1:
            self._fill_wmts_v1(l, layer, wms, wms_layers, errors)
        else:
            self._fill_wmts_v2(l, layer)

    def _fill_wmts_v2(self, l, layer):
        l["imageType"] = layer.image_type
        l["dimensions"] = {}
        for dimension in layer.dimensions:
            l["dimensions"][dimension.name] = dimension.value

    def _fill_wmts_v1(self, l, layer, wms, wms_layers, errors):
        if layer.dimensions:
            try:
                l["dimensions"] = json.loads(layer.dimensions)
            except:  # pragma: no cover
                errors.add(
                    u"Unexpected error: '%s' while reading '%s' in layer '%s'" %
                    (sys.exc_info()[0], layer.dimensions, layer.name))

        mapserverproxy_url = self.request.route_url("mapserverproxy")

        if layer.wms_url:
            l["wmsUrl"] = layer.wms_url
        elif layer.wms_layers or layer.query_layers:
            l["wmsUrl"] = mapserverproxy_url
        if layer.wms_layers:
            l["wmsLayers"] = layer.wms_layers
        elif layer.wms_url:
            l["wmsLayers"] = layer.name
        # needed for external WMTS
        if layer.query_layers == "[]":  # pragma: no cover
            l["queryLayers"] = []

        if layer.min_resolution is not None:
            l["minResolutionHint"] = layer.min_resolution
        if layer.max_resolution is not None:
            l["maxResolutionHint"] = layer.max_resolution

        # if we have associated local WMS layers then look at what's in the
        # WMS capabilities, and add a queryLayers array with the "resolution
        # hint" information.
        if "wmsUrl" in l and l["wmsUrl"] == mapserverproxy_url:

            query_layers = layer.query_layers.strip("[]") \
                if layer.query_layers else l["wmsLayers"]
            l["queryLayers"] = []

            for query_layer in query_layers.split(","):
                if query_layer not in wms_layers:
                    continue
                query_layer_obj = wms[query_layer]

                ql = {"name": query_layer}
                resolutions = self._get_layer_resolution_hint(query_layer_obj)

                if resolutions[0] != float("Inf"):
                    ql["minResolutionHint"] = float(
                        "%0.2f" % resolutions[0])
                if resolutions[1] != 0:
                    ql["maxResolutionHint"] = float(
                        "%0.2f" % resolutions[1])

                l["queryLayers"].append(ql)

                # FIXME we do not support WMTS layers associated to
                # MapServer layer groups for now.

    def _layer_included(self, tree_item, version):
        if version == 1 and type(tree_item) == LayerV1:
            return True
        if version == 2 and isinstance(tree_item, Layer):
            return type(tree_item) != LayerV1
        return False

    def _is_internal_wms(self, layer):
        return \
            isinstance(layer, LayerInternalWMS) or \
            isinstance(layer, LayerV1) and layer.layer_type == "internal WMS"

    def _group(
        self, path, group, layers, depth=1, min_levels=1,
        catalogue=True, version=1, **kwargs
    ):
        children = []
        errors = set()

        # escape loop
        if depth > 30:
            errors.add(
                "Too many recursions with group '%s'" % group.name
            )
            return None, errors

        for tree_item in group.children:
            if type(tree_item) == LayerGroup:
                depth += 1
                if type(group) == Theme or catalogue or \
                        group.is_internal_wms == tree_item.is_internal_wms:
                    gp, gp_errors = self._group(
                        "%s/%s" % (path, tree_item.name),
                        tree_item, layers, depth=depth, min_levels=min_levels,
                        catalogue=catalogue, version=version, **kwargs
                    )
                    errors |= gp_errors
                    if gp is not None:
                        children.append(gp)
                else:
                    errors.add(
                        "Group '%s' cannot be in group '%s' (internal/external mix)." %
                        (tree_item.name, group.name)
                    )
            elif self._layer_included(tree_item, version):
                if (tree_item.name in layers):
                    if (catalogue or group.is_internal_wms ==
                            self._is_internal_wms(tree_item)):
                        l, l_errors = self._layer(tree_item, **kwargs)
                        errors |= l_errors
                        if l is not None:
                            if depth < min_levels:
                                errors.add("The Layer '%s' is under indented (%i/%i)." % (
                                    path + "/" + tree_item.name, depth, min_levels
                                ))
                            else:
                                children.append(l)
                    else:
                        errors.add(
                            "Layer '%s' cannot be in the group '%s' (internal/external mix)." %
                            (tree_item.name, group.name)
                        )

        if len(children) > 0:
            g = {
                "id": group.id,
                "name": group.name,
                "children": children,
                "metadata": {},
            }
            if version == 1:
                g.update({
                    "isExpanded": group.is_expanded,
                    "isInternalWMS": group.is_internal_wms,
                    "isBaseLayer": group.is_base_layer,
                })
            for metadata in group.ui_metadata:
                g["metadata"][metadata.name] = get_url(metadata.value, self.request, errors=errors)
            if version == 1 and group.metadata_url:
                g["metadataURL"] = group.metadata_url

            return g, errors
        else:
            return None, errors

    @cache_region.cache_on_arguments()
    def _layers(self, role_id, version, interface):
        query = self._create_layer_query(role_id, version)
        if interface is not None:
            query = query.join(Layer.interfaces)
            query = query.filter(Interface.name == interface)
        return [l.name for l in query.all()]

    @cache_region.cache_on_arguments()
    def _wms_layers(self, role_id):
        """ role_id is just for cache """

        # retrieve layers metadata via GetCapabilities
        wms, wms_errors = self._wms_getcap(
            self.mapserver_settings["mapserv_url"]
        )
        if len(wms_errors) > 0:
            return [], wms_errors

        return wms, list(wms.contents)

    @cache_region.cache_on_arguments()
    def _themes(
        self, role_id, interface="main", filter_themes=True, version=1,
        catalogue=False, min_levels=1
    ):
        """
        This function returns theme information for the role identified
        by ``role_id``.
        ``mobile`` tells whether to retrieve mobile or desktop layers
        """
        errors = set()
        layers = self._layers(role_id, version, interface)
        wms, wms_layers = self._wms_layers(
            role_id if self.mapserver_settings["geoserver"] else None
        )

        themes = DBSession.query(Theme)
        themes = themes.filter(Theme.public.is_(True))
        if role_id is not None:
            auth_themes = DBSession.query(Theme)
            auth_themes = auth_themes.filter(Theme.public.is_(False))
            auth_themes = auth_themes.join(Theme.restricted_roles)
            auth_themes = auth_themes.filter(Role.id == role_id)

            themes = themes.union(auth_themes)

        themes = themes.order_by(Theme.ordering.asc())

        if filter_themes and interface is not None:
            themes = themes.join(Theme.interfaces)
            themes = themes.filter(Interface.name == interface)

        export_themes = []
        for theme in themes.all():
            children, children_errors = self._get_children(
                theme, layers, wms, wms_layers, version, catalogue, min_levels
            )
            errors |= children_errors

            # test if the theme is visible for the current user
            if len(children) > 0:
                icon = get_url(
                    theme.icon, self.request,
                    self.request.static_url(
                        "c2cgeoportal:static/images/blank.gif"
                    ),
                    errors=errors
                )

                t = {
                    "id": theme.id,
                    "name": theme.name,
                    "icon": icon,
                    "children": children,
                    "functionalities": self._get_functionalities(theme),
                    "metadata": {},
                }
                if version == 1:
                    t.update({
                        "in_mobile_viewer": theme.is_in_interface("mobile"),
                    })
                for metadata in theme.ui_metadata:
                    t["metadata"][metadata.name] = get_url(
                        metadata.value, self.request, errors=errors
                    )
                export_themes.append(t)

        return export_themes, errors

    def _get_functionalities(self, theme):
        result = {}
        for functionality in theme.functionalities:
            if functionality.name in result:
                result[functionality.name].append(functionality.value)
            else:
                result[functionality.name] = [functionality.value]
        return result

    @view_config(route_name="invalidate", renderer="json")
    def invalidate_cache(self):  # pragma: no cover
        invalidate_region()
        return {
            "success": True
        }

    def _get_children(self, theme, layers, wms, wms_layers, version, catalogue, min_levels):
        children = []
        errors = set()
        for item in theme.children:
            if type(item) == LayerGroup:
                time = TimeInformation()
                gp, gp_errors = self._group(
                    "%s/%s" % (theme.name, item.name),
                    item, layers, time=time, wms=wms, wms_layers=wms_layers,
                    version=version, catalogue=catalogue, min_levels=min_levels
                )
                errors |= gp_errors

                if gp is not None:
                    if time.has_time() and time.layer is None:
                        gp["time"] = time.to_dict()
                    children.append(gp)
            elif self._layer_included(item, version):
                if min_levels > 0:
                    errors.add("The Layer '%s' cannot be directly in the theme '%s' (0/%i)." % (
                        item.name, theme.name, min_levels
                    ))
                elif item.name in layers:
                    time = TimeInformation()
                    l, l_errors = self._layer(
                        item, time=time, wms=wms, wms_layers=wms_layers
                    )
                    errors |= l_errors
                    if l is not None:
                        children.append(l)
        return children, errors

    def _get_wfs_url(self):
        if "mapserv_wfs_url" in self.mapserver_settings and \
                self.mapserver_settings["mapserv_wfs_url"]:
            return self.mapserver_settings["mapserv_wfs_url"]
        return self.mapserver_settings["mapserv_url"]

    def _internal_wfs_types(self, role_id):
        return self._wfs_types(self._get_wfs_url(), role_id)

    def _get_external_wfs_url(self):
        if "external_mapserv_wfs_url" in self.mapserver_settings and \
                self.mapserver_settings["external_mapserv_wfs_url"]:
            return self.mapserver_settings["external_mapserv_wfs_url"]
        if "external_mapserv_url" in self.mapserver_settings and \
                self.mapserver_settings["external_mapserv_url"]:
            return self.mapserver_settings["external_mapserv_url"]
        return None

    def _external_wfs_types(self, role_id):
        url = self._get_external_wfs_url()
        if not url:
            return [], set()
        return self._wfs_types(url, role_id)

    def _wfs_types(self, wfs_url, role_id):
        if wfs_url.find("?") < 0:
            wfs_url += "?"

        # add functionalities query_string
        sparams = get_mapserver_substitution_params(self.request)
        if sparams:  # pragma: no cover
            wfs_url += urllib.urlencode(sparams) + "&"

        if role_id is not None:
            wfs_url += "role_id=%s&" % role_id

        return self._wfs_types_cached(wfs_url)

    @cache_region.cache_on_arguments()
    def _wfs_types_cached(self, wfs_url):
        errors = set()

        # retrieve layers metadata via GetCapabilities
        params = (
            ("SERVICE", "WFS"),
            ("VERSION", "1.0.0"),
            ("REQUEST", "GetCapabilities"),
        )
        wfsgc_url = wfs_url + "&".join(["=".join(p) for p in params])

        log.info("WFS GetCapabilities for base url: %s" % wfsgc_url)

        # forward request to target (without Host Header)
        http = httplib2.Http()
        h = dict(self.request.headers)
        if urlsplit(wfsgc_url).hostname != "localhost":  # pragma: no cover
            h.pop("Host")
        try:
            resp, get_capabilities_xml = http.request(wfsgc_url, method="GET", headers=h)
        except:  # pragma: no cover
            errors.add("Unable to GetCapabilities from url %s" % wfsgc_url)
            return None, errors

        if resp.status < 200 or resp.status >= 300:  # pragma: no cover
            errors.add(
                "GetCapabilities from url %s return the error: %i %s" %
                (wfsgc_url, resp.status, resp.reason)
            )
            return None, errors

        try:
            get_capabilities_dom = parseString(get_capabilities_xml)
            featuretypes = []
            for featureType in get_capabilities_dom.getElementsByTagNameNS(
                    self.WFS_NS, "FeatureType"):
                # don't includes FeatureType without name
                name = featureType.getElementsByTagNameNS(self.WFS_NS, "Name").item(0)
                if name:
                    name_value = name.childNodes[0].data
                    # ignore namespace when not using geoserver
                    if name_value.find(":") >= 0 and \
                            not self.mapserver_settings["geoserver"]:  # pragma nocover
                        name_value = name_value.split(":")[1]
                    featuretypes.append(name_value)
                else:  # pragma nocover
                    log.warn("Feature type without name: %s" % featureType.toxml())
            return featuretypes, errors
        except:  # pragma: no cover
            return get_capabilities_xml, errors

    def _external_themes(self, interface):  # pragma nocover
        if not (
            "external_themes_url" in self.settings and
            self.settings["external_themes_url"]
        ):
            return None, set()

        role_id = None
        if self.request.user is not None and \
                hasattr(self.request.user, "parent_role") and \
                self.request.user.parent_role is not None:
            role_id = str(self.request.user.parent_role.id)

        return self._external_themes_role(interface, role_id)

    @cache_region.cache_on_arguments()
    def _external_themes_role(self, interface, role_id):  # pragma nocover
        errors = set()

        ext_url = self.settings["external_themes_url"]
        url_params = {
            "interface": interface
        }

        if ext_url[-1] not in ("?", "&"):
            ext_url += "?"
        ext_url += "&".join([
            "=".join(p) for p in url_params.items()
        ])

        # forward request to target (without Host Header)
        http = httplib2.Http()
        h = dict(self.request.headers)
        if urlsplit(ext_url).hostname != "localhost":
            h.pop("Host")
        try:
            resp, content = http.request(ext_url, method="GET", headers=h)
        except:
            errors.add(
                "Unable to get external themes from url %s" % ext_url
            )
            return None, errors

        if resp.status < 200 or resp.status >= 300:
            errors.add(
                "Get external themes from url %s return the error: %i %s" %
                (ext_url, resp.status, resp.reason)
            )
            return None, errors

        return content, errors

    def _functionality(self):
        return self._functionality_cached(
            self.request.user.role.name if self.request.user is not None else None
        )

    @cache_region.cache_on_arguments()
    def _functionality_cached(self, role):
        functionality = {}
        for func in get_setting(
                self.settings,
                ("functionalities", "available_in_templates"), []
        ):
            functionality[func] = get_functionality(
                func, self.settings, self.request
            )
        return functionality

    @cache_region.cache_on_arguments()
    def _get_layers_enum(self):
        layers_enum = {}
        if "enum" in self.settings.get("layers", {}):
            for layer_name, layer in \
                    self.settings["layers"]["enum"].items():
                layer_enum = {}
                layers_enum[layer_name] = layer_enum
                for attribute in layer["attributes"].keys():
                    layer_enum[attribute] = self.request.route_url(
                        "layers_enumerate_attribute_values",
                        layer_name=layer_name,
                        field_name=attribute,
                        path=""
                    )
        return layers_enum

    def get_cgxp_index_vars(self, templates_params={}):
        extra_params = {}

        if self.lang:
            extra_params["lang"] = self.lang

        # specific permalink_themes handling
        if "permalink_themes" in templates_params:
            extra_params["permalink_themes"] = templates_params["permalink_themes"]

        d = {
            "lang": self.lang,
            "debug": self.debug,
            "no_redirect": self.request.params.get("no_redirect") is not None,
            "extra_params": extra_params,
        }

        # general templates_params handling
        d.update(templates_params)

        # check if route to mobile app exists
        try:
            d["mobile_url"] = self.request.route_url("mobile_index_prod")
        except:  # pragma: no cover
            d["mobile_url"] = None

        set_common_headers(self.request, "cgxp_index", NO_CACHE)

        return d

    def get_cgxp_permalinktheme_vars(self):
        # call home with extra params
        return self.get_cgxp_index_vars({
            # recover themes from url route
            "permalink_themes": self.request.matchdict["themes"]
        })

    def _get_role_id(self):
        return None if self.request.user is None or self.request.user.role is None else \
            self.request.user.role.id

    def get_cgxp_viewer_vars(self):
        role_id = self._get_role_id()
        interface = self.request.interface_name

        themes, errors = self._themes(role_id, interface)
        wfs_types, add_errors = self._internal_wfs_types(role_id)
        errors |= add_errors
        external_wfs_types, add_errors = self._external_wfs_types(role_id)
        errors |= add_errors
        external_themes, add_errors = self._external_themes(interface)
        errors |= add_errors

        version_params = {
            "cache_version": get_cache_version()
        }
        version_role_params = {
            "cache_version": get_cache_version()
        }
        if role_id is not None:
            version_role_params["user"] = role_id

        d = {
            "lang": self.lang,
            "debug": self.debug,
            "themes": json.dumps(themes),
            "user": self.request.user,
            "WFSTypes": json.dumps(wfs_types),
            "externalWFSTypes": json.dumps(external_wfs_types),
            "external_themes": external_themes,
            "tiles_url": json.dumps(self.settings.get("tiles_url")),
            "functionality": self._functionality(),
            "queryer_attribute_urls": json.dumps(self._get_layers_enum()),
            "serverError": json.dumps(list(errors)),
            "version_params": version_params,
            "version_role_params": version_role_params,
        }

        # handle permalink_themes
        permalink_themes = self.request.params.get("permalink_themes")
        if permalink_themes:
            d["permalink_themes"] = json.dumps(permalink_themes.split(","))

        set_common_headers(
            self.request, "cgxp_viewer", PRIVATE_CACHE,
            vary=True, content_type="application/javascript",
        )

        return d

    def get_ngeo_index_vars(self, vars={}):
        set_common_headers(self.request, "ngeo_index", NO_CACHE)

        vars.update({
            "debug": self.debug,
            "functionality": self._functionality(),
            "queryer_attribute_urls": self._get_layers_enum(),
        })
        return vars

    def get_ngeo_permalinktheme_vars(self):
        # recover themes from url route
        themes = self.request.matchdict["themes"]
        d = {}
        d["permalink_themes"] = themes
        # call home with extra params
        return self.get_ngeo_index_vars(d)

    def mobile(self):
        """
        View callable for the mobile application's index.html file.
        """
        set_common_headers(self.request, "sencha_index", NO_CACHE)

        extra_params = dict(self.request.params)
        came_from = self.request.current_route_url(_query=extra_params)
        cache_version = get_cache_version()
        url_params = {
            "cache_version": cache_version
        }
        extra_params["cache_version"] = cache_version
        if self.request.user is not None:
            extra_params["role"] = self.request.user.role.name

        def enc(vals):
            return (vals[0], vals[1].encode("utf8"))
        return {
            "lang": self.lang,
            "came_from": came_from,
            "url_params": urllib.urlencode(dict(map(enc, url_params.items()))),
            "extra_params": urllib.urlencode(dict(map(enc, extra_params.items()))),
        }

    def flatten_layers(self, theme):
        """
        Flatten the children property into allLayers for mobile application
        """

        layer_info = []

        def process(node, layer_info):
            if "children" in node:
                for child_node in node["children"]:
                    process(child_node, layer_info)
            else:
                layer_info.append(node)

        process(theme, layer_info)

        # we only support WMS layers right now
        layer_info = filter(lambda li: li["type"] == "internal WMS", layer_info)

        # list of dicts representing the layers of the selected theme
        layers = []
        for li in layer_info:

            def process_layers(l, layers):
                layer = {"name": l["name"]}
                if "minResolutionHint" in l:
                    layer["minResolutionHint"] = l["minResolutionHint"]
                if "maxResolutionHint" in l:
                    layer["maxResolutionHint"] = l["maxResolutionHint"]
                if "childLayers" in l and len(l["childLayers"]) > 0:
                    layer["childLayers"] = []
                    for child in l["childLayers"]:
                        process_layers(child, layer["childLayers"])
                return layers.append(layer)

            process_layers(li, layers)

        # reverse
        theme["allLayers"] = layers[::-1]

        # comma-separated string including the names of layers that
        # should visible by default in the map
        visible_layers = filter(lambda li: li["isChecked"] is True, layer_info)
        theme["layers"] = [li["name"] for li in visible_layers][::-1]

    def mobileconfig(self):
        """
        View callable for the mobile application's config.js file.
        """
        errors = set()
        interface = self.request.interface_name

        mobile_default_themes = get_functionality(
            "mobile_default_theme",
            self.settings,
            self.request
        )
        theme_name = self.request.params.get(
            "theme",
            mobile_default_themes[0] if len(mobile_default_themes) > 0 else None
        )
        user = self.request.user

        role_id = None if user is None else user.role.id
        # get the list of themes available for mobile
        themes, errors = self._themes(role_id, interface, False, 1, False, 0)
        if len(errors) > 0:  # pragma: no cover
            log.error("Error in mobile theme:\n%s" % "\n".join(errors))

        for t in themes:
            self.flatten_layers(t)

        # comma-separated string including the feature types supported
        # by WFS service
        wfs_types, errors = self._internal_wfs_types(role_id)
        if len(errors) > 0:  # pragma: no cover
            raise HTTPBadGateway("\n".join(errors))

        # info includes various information that is not used by config.js,
        # but by other - private to the integrator - parts of the mobile
        # application.
        info = {
            "username": user.username if user else ""
        }

        themes_ = []
        for theme in themes:
            # mobile theme or hidden theme explicitely loaded
            if theme["in_mobile_viewer"] or theme["name"] == theme_name:
                themes_.append({
                    "name": theme["name"],
                    "icon": theme["icon"],
                    "allLayers": theme["allLayers"],
                    "layers": theme["layers"],
                })

        set_common_headers(
            self.request, "sencha_config", PRIVATE_CACHE,
            vary=True, content_type="application/javascript",
        )

        return {
            "lang": self.lang,
            "themes": themes_,
            "theme": theme_name if theme_name is not None else "",
            "wfs_types": wfs_types,
            "server_error": errors,
            "info": info,
        }

    @view_config(route_name="apijs", renderer="api/api.js")
    def apijs(self):
        wms, wms_errors = self._wms_getcap(
            self.mapserver_settings["mapserv_url"])
        if len(wms_errors) > 0:  # pragma: no cover
            raise HTTPBadGateway("\n".join(wms_errors))
        queryable_layers = [
            name for name in list(wms.contents)
            if wms[name].queryable == 1]
        cache_version = self.settings.get("cache_version", None)

        set_common_headers(
            self.request, "apijs", NO_CACHE,
            content_type="application/javascript",
        )

        return {
            "lang": self.lang,
            "debug": self.debug,
            "queryable_layers": json.dumps(queryable_layers),
            "url_params": {"cache_version": cache_version} if cache_version else {},
            "tiles_url": json.dumps(self.settings.get("tiles_url")),
        }

    @view_config(route_name="xapijs", renderer="api/xapi.js")
    def xapijs(self):
        wms, wms_errors = self._wms_getcap(
            self.mapserver_settings["mapserv_url"])
        queryable_layers = [
            name for name in list(wms.contents)
            if wms[name].queryable == 1]
        cache_version = self.settings.get("cache_version", None)

        set_common_headers(
            self.request, "xapijs", NO_CACHE,
            content_type="application/javascript",
        )

        return {
            "lang": self.lang,
            "debug": self.debug,
            "queryable_layers": json.dumps(queryable_layers),
            "url_params": {"cache_version": cache_version} if cache_version else {},
            "tiles_url": json.dumps(self.settings.get("tiles_url")),
        }

    @view_config(route_name="apihelp", renderer="api/apihelp.html")
    def apihelp(self):
        set_common_headers(self.request, "apihelp", NO_CACHE)

        return {
            "lang": self.lang,
            "debug": self.debug,
        }

    @view_config(route_name="xapihelp", renderer="api/xapihelp.html")
    def xapihelp(self):
        set_common_headers(self.request, "xapihelp", NO_CACHE)

        return {
            "lang": self.lang,
            "debug": self.debug,
        }

    @view_config(route_name="themes", renderer="json")
    def themes(self):
        role_id = self.request.params.get("role_id", None)
        if role_id is None and self.request.user is not None:
            role_id = self.request.user.role.id
        elif self.request.client_addr != "127.0.0.1":
            role_id = None

        interface = self.request.params.get("interface", "main")
        sets = self.request.params.get("set", "all")
        version = int(self.request.params.get("version", 1))
        catalogue = self.request.params.get("catalogue", "false") == "true"
        min_levels = int(self.request.params.get("min_levels", 1))
        group = self.request.params.get("group", None)
        background_layers_group = self.request.params.get("background", None)

        export_themes = sets in ("all", "themes")
        export_group = group is not None and sets in ("all", "group")
        export_background = background_layers_group is not None and sets in ("all", "background")

        set_common_headers(self.request, "themes", PRIVATE_CACHE)

        result = {}
        all_errors = set()
        if export_themes:
            themes, errors = self._themes(
                role_id, interface, True, version, catalogue, min_levels
            )

            if version == 1:
                return themes

            result["themes"] = themes
            all_errors |= errors

        if export_group:
            group, errors = self._get_group(group, role_id, interface, version)
            result["group"] = group
            all_errors |= errors

        if export_background:
            group, errors = self._get_group(background_layers_group, role_id, interface, version)
            result["background_layers"] = group["children"]
            all_errors |= errors

        result["errors"] = list(all_errors)
        return result

    def _get_group(self, group, role_id, interface, version):
        time = TimeInformation()
        layers = self._layers(role_id, version, interface)
        wms, wms_layers = self._wms_layers(
            role_id if self.mapserver_settings["geoserver"] else None
        )
        lg = DBSession.query(LayerGroup).filter(LayerGroup.name == group).one()
        return self._group(
            lg.name, lg, layers, time=time, wms=wms, wms_layers=wms_layers, version=version
        )

    @view_config(context=HTTPForbidden, renderer="login.html")
    def loginform403(self):
        if self.request.authenticated_userid:
            return HTTPForbidden()  # pragma: no cover

        set_common_headers(self.request, "loginform403", NO_CACHE)

        return {
            "lang": self.lang,
            "came_from": self.request.path,
        }

    @view_config(route_name="loginform", renderer="login.html")
    def loginform(self):
        set_common_headers(self.request, "loginform", PUBLIC_CACHE, vary=True)

        return {
            "lang": self.lang,
            "came_from": self.request.params.get("came_from") or "/",
        }

    @view_config(route_name="login")
    def login(self):
        login = self.request.POST.get("login", None)
        password = self.request.POST.get("password", None)
        if not (login and password):
            return HTTPBadRequest(
                "'login' and 'password' should be "
                "available in request params"
            )  # pragma nocover
        user = self.request.registry.validate_user(self.request, login, password)
        if user is not None:
            headers = remember(self.request, user)
            log.info("User '%s' logged in." % login)

            came_from = self.request.params.get("came_from")
            if came_from:
                return HTTPFound(location=came_from, headers=headers)
            else:
                return set_common_headers(
                    self.request, "login", NO_CACHE,
                    response=Response("true", headers=headers),
                )
        else:
            return HTTPUnauthorized("bad credentials")

    @view_config(route_name="logout")
    def logout(self):
        headers = forget(self.request)

        # if there's no user to log out, we send a 404 Not Found (which
        # is the status code that applies best here)
        if not self.request.user:
            return HTTPNotFound()

        log.info("User '%s' (%i) logging out." % (
            self.request.user.username,
            self.request.user.id
        ))

        return set_common_headers(
            self.request, "logout", NO_CACHE,
            response=Response("true", headers=headers),
        )

    @view_config(route_name="loginchange", renderer="json")
    def loginchange(self):
        set_common_headers(self.request, "loginchange", NO_CACHE)

        new_password = self.request.POST.get("newPassword", None)
        new_password_confirm = self.request.POST.get("confirmNewPassword", None)
        if new_password is None or new_password_confirm is None:
            raise HTTPBadRequest(
                "'newPassword' and 'confirmNewPassword' should be "
                "available in request params"
            )

        # check if loggedin
        if not self.request.user:
            raise HTTPUnauthorized("bad credentials")
        if new_password != new_password_confirm:
            raise HTTPBadRequest(
                "The new password and the new password "
                "confirmation don't match"
            )

        u = self.request.user
        u._set_password(new_password)
        u.is_password_changed = True
        DBSession.flush()
        log.info("Password changed for user: %s" % self.request.user.username)

        return {
            "success": "true"
        }

    def generate_password(self):
        allchars = "123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        rand = Random()

        password = ""
        for i in range(8):
            password += rand.choice(allchars)

        return password

    def _loginresetpassword(self):
        username = self.request.POST["login"]
        try:
            user = DBSession.query(User).filter(User.username == username).one()
        except NoResultFound:  # pragma: no cover
            return {
                "success": False,
                "error": _("The user '%s' doesn't exist.") % username,
            }

        if user.email is None or user.email == "":  # pragma: no cover
            return {
                "success": False,
                "error": _("User '%s' has no registered email address.") % username,
            }

        password = self.generate_password()
        user.set_temp_password(password)

        return user, username, password

    @view_config(route_name="loginresetpassword", renderer="json")
    def loginresetpassword(self):  # pragma: no cover
        set_common_headers(self.request, "loginresetpassword", NO_CACHE)

        user, username, password = self._loginresetpassword()
        smtp_config = self.request.registry.settings.get("smtp", {})
        reset_password_config = self.request.registry.settings.get("reset_password", {})

        send_email(
            reset_password_config.get("email_from"),
            [user.email],
            reset_password_config.get("email_body").format(user=username,
                                                           password=password).encode("utf-8"),
            reset_password_config.get("email_subject"),
            smtp_config
        )

        return {
            "success": True
        }
