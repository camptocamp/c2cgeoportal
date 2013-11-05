# -*- coding: utf-8 -*-

# Copyright (c) 2013, Camptocamp SA
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
import logging
import json
import sys

from urlparse import urlparse

from pyramid.view import view_config
from pyramid.i18n import get_locale_name, TranslationStringFactory
from pyramid.httpexceptions import HTTPFound, HTTPNotFound, \
    HTTPBadRequest, HTTPUnauthorized, HTTPForbidden, HTTPBadGateway
from pyramid.security import remember, forget, authenticated_userid
from pyramid.response import Response
from sqlalchemy.sql.expression import and_
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import engine_from_config
import sqlahelper
from geoalchemy.functions import functions
from owslib.wms import WebMapService
from xml.dom.minidom import parseString
from math import sqrt

from c2cgeoportal.lib import get_setting, caching
from c2cgeoportal.lib.functionality import get_functionality
from c2cgeoportal.models import DBSession, Layer, LayerGroup, \
    Theme, RestrictionArea, Role, layer_ra, role_ra, User

_ = TranslationStringFactory('c2cgeoportal')
log = logging.getLogger(__name__)
cache_region = caching.get_region()


class Entry(object):

    WFS_NS = "http://www.opengis.net/wfs"

    def __init__(self, request):
        self.request = request
        self.settings = request.registry.settings
        self.debug = "debug" in request.params
        self.lang = get_locale_name(request)

        # detect if HTTPS scheme must be set
        https_flag = self.settings.get('https_flag_header')
        if https_flag:  # pragma: no cover
            if https_flag in self.request.headers and \
                    self.request.headers[https_flag] == self.settings.get('https_flag_value'):
                self.request.scheme = 'https'

    @view_config(route_name='testi18n', renderer='testi18n.html')
    def testi18n(self):  # pragma: no cover
        _ = self.request.translate
        return {'title': _('title i18n')}

    @cache_region.cache_on_arguments()
    def _wms_getcap(self, url):
        errors = []
        wms = None

        params = (
            ('SERVICE', 'WMS'),
            ('VERSION', '1.1.1'),
            ('REQUEST', 'GetCapabilities'),
        )
        if url.find('?') < 0:
            url += '?'
        url = url + '&'.join(['='.join(p) for p in params])

        log.info("WMS GetCapabilities for base url: %s" % url)

        # forward request to target (without Host Header)
        http = httplib2.Http()
        h = dict(self.request.headers)
        if urlparse(url).hostname != 'localhost':  # pragma: no cover
            h.pop('Host')
        try:
            resp, content = http.request(url, method='GET', headers=h)
        except:  # pragma: no cover
            errors.append("Unable to GetCapabilities from url %s" % url)
            return None, errors

        if resp.status < 200 or resp.status >= 300:  # pragma: no cover
            errors.append(
                "GetCapabilities from url %s return the error: %i %s" %
                (url, resp.status, resp.reason)
            )
            return None, errors

        try:
            wms = WebMapService(None, xml=content)
        except AttributeError:
            error = _(
                "WARNING! an error occured while trying to "
                "read the mapfile and recover the themes"
            )
            errors.append("%s\nurl: %s\nxml:\n%s" % (error, url, content))
            log.exception(error)
        return wms, errors

    def _create_layer_query(self, role_id):
        """ Create an SQLAlchemy query for Layer and for the role
            identified to by ``role_id``.
        """
        q = DBSession.query(Layer).filter(Layer.public == True)
        if role_id:
            q2 = DBSession.query(Layer)
            q2 = q2.join(
                (layer_ra, Layer.id == layer_ra.c.layer_id),
                (RestrictionArea,
                    RestrictionArea.id == layer_ra.c.restrictionarea_id),
                (role_ra, role_ra.c.restrictionarea_id == RestrictionArea.id),
                (Role, Role.id == role_ra.c.role_id))
            q2 = q2.filter(Role.id == role_id)
            q2 = q2.filter(and_(
                Layer.public != True,
                functions.area(RestrictionArea.area) > 0))
            q = q.union(q2)
        return q

    def _getLayerMetadataUrls(self, layer):
        metadataUrls = []
        if len(layer.metadataUrls) > 0:
            metadataUrls = layer.metadataUrls
        for childLayer in layer.layers:
            metadataUrls.extend(self._getLayerMetadataUrls(childLayer))
        return metadataUrls

    def _getLayerResolutionHint(self, layer):
        resolutionHintMin = float('inf')
        resolutionHintMax = 0
        if layer.scaleHint:
            # scaleHint is based upon a pixel diagonal length whereas we use
            # resolutions based upon a pixel edge length. There is a sqrt(2)
            # ratio between edge and diagonal of a square.
            resolutionHintMin = float(layer.scaleHint['min']) / sqrt(2)
            resolutionHintMax = float(layer.scaleHint['max']) / sqrt(2)
        for childLayer in layer.layers:
            resolution = self._getLayerResolutionHint(childLayer)
            resolutionHintMin = min(resolutionHintMin, resolution[0])
            resolutionHintMax = max(resolutionHintMax, resolution[1])

        return (resolutionHintMin, resolutionHintMax)

    def _get_child_layers_info(self, layer):
        """ Return information about sub layers of a layer.

            Arguments:

            * ``layer`` The layer object in the WMS capabilities.
        """
        child_layers_info = []
        for child_layer in layer.layers:
            child_layer_info = dict(name=child_layer.name)
            resolution = self._getLayerResolutionHint(child_layer)
            if resolution[0] <= resolution[1]:
                child_layer_info.update({
                    'minResolutionHint': float('%0.2f' % resolution[0]),
                    'maxResolutionHint': float('%0.2f' % resolution[1])
                })
            if hasattr(child_layer, 'queryable'):
                child_layer_info['queryable'] = child_layer.queryable
            child_layers_info.append(child_layer_info)
        return child_layers_info

    def _getIconPath(self, icon):
        if not icon:
            return None  # pragma: no cover
        icon = unicode(icon)
        # test full URL
        if not icon[0:4] == 'http':
            try:
                # test full resource ref
                if icon.find(':') < 0:
                    if icon[0] is not '/':
                        icon = '/' + icon
                    icon = self.settings['project'] + ':static' + icon
                icon = self.request.static_url(icon)
            except ValueError:  # pragma: no cover
                log.exception('can\'t generate url for icon: %s' % icon)
                return None
        return icon

    def _layer(self, layer, wms_layers, wms):
        errors = []
        l = {
            'id': layer.id,
            'name': layer.name,
            'type': layer.layerType,
            'legend': layer.legend,
            'isChecked': layer.isChecked,
            'public': layer.public,
            'isLegendExpanded': layer.isLegendExpanded,
        }
        if layer.identifierAttributeField:
            l['identifierAttribute'] = layer.identifierAttributeField
        if layer.disclaimer:
            l['disclaimer'] = layer.disclaimer
        if layer.icon:
            l['icon'] = self._getIconPath(layer.icon)
        if layer.kml:
            l['kml'] = self._getIconPath(layer.kml)
        if layer.metadataURL:
            l['metadataURL'] = layer.metadataURL
        if layer.geoTable:
            self._fill_editable(l, layer)
        if layer.legendImage:
            l['legendImage'] = self._getIconPath(layer.legendImage)

        if layer.layerType == "internal WMS":
            self._fill_internal_WMS(l, layer, wms_layers, wms, errors)
        elif layer.layerType == "external WMS":
            self._fill_external_WMS(l, layer)
        elif layer.layerType == "WMTS":
            self._fill_WMTS(l, layer, wms_layers, wms, errors)

        return l, errors

    def _fill_editable(self, l, layer):
        if layer.public:
            l['editable'] = True
        elif self.request.user:
            c = DBSession.query(RestrictionArea) \
                .filter(RestrictionArea.roles.any(
                    Role.id == self.request.user.role.id)) \
                .filter(RestrictionArea.layers.any(Layer.id == layer.id)) \
                .filter(RestrictionArea.readwrite == True) \
                .count()
            if c > 0:
                l['editable'] = True

    def _fill_WMS(self, l, layer):
        l['imageType'] = layer.imageType
        if layer.legendRule:
            query = (
                ('SERVICE', 'WMS'),
                ('VERSION', '1.1.1'),
                ('REQUEST', 'GetLegendGraphic'),
                ('LAYER', layer.name),
                ('FORMAT', 'image/png'),
                ('TRANSPARENT', 'TRUE'),
                ('RULE', layer.legendRule),
            )
            l['icon'] = self.request.route_url('mapserverproxy') + \
                '?' + '&'.join('='.join(p) for p in query)
        if layer.style:
            l['style'] = layer.style

    def _fill_legend_rule_query_string(self, l, layer, url):
        if layer.legendRule and url:
            query = (
                ('SERVICE', 'WMS'),
                ('VERSION', '1.1.1'),
                ('REQUEST', 'GetLegendGraphic'),
                ('LAYER', layer.name),
                ('FORMAT', 'image/png'),
                ('TRANSPARENT', 'TRUE'),
                ('RULE', layer.legendRule),
            )
            l['icon'] = url + '?' + '&'.join('='.join(p) for p in query)

    def _fill_internal_WMS(self, l, layer, wms_layers, wms, errors):
        self._fill_WMS(l, layer)
        self._fill_legend_rule_query_string(
            l, layer,
            self.request.route_url('mapserverproxy'))

        # this is a leaf, ie. a Mapserver layer
        if layer.minResolution:
            l['minResolutionHint'] = layer.minResolution
        if layer.maxResolution:
            l['maxResolutionHint'] = layer.maxResolution
        # now look at what's in the WMS capabilities doc
        if layer.name in wms_layers:
            wms_layer_obj = wms[layer.name]
            metadataUrls = self._getLayerMetadataUrls(wms_layer_obj)
            if len(metadataUrls) > 0:
                l['metadataUrls'] = metadataUrls
            resolutions = self._getLayerResolutionHint(wms_layer_obj)
            if resolutions[0] <= resolutions[1]:
                if 'minResolutionHint' not in l:
                    l['minResolutionHint'] = float('%0.2f' % resolutions[0])
                if 'maxResolutionHint' not in l:
                    l['maxResolutionHint'] = float('%0.2f' % resolutions[1])
            l['childLayers'] = self._get_child_layers_info(wms_layer_obj)
            if hasattr(wms_layer_obj, 'queryable'):
                l['queryable'] = wms_layer_obj.queryable
        else:
            errors.append(
                'The layer %s is not defined in WMS capabilities' % layer.name
            )

    def _fill_external_WMS(self, l, layer):
        self._fill_WMS(l, layer)
        self._fill_legend_rule_query_string(l, layer, layer.url)

        l['url'] = layer.url
        l['isSingleTile'] = layer.isSingleTile

        if layer.minResolution:
            l['minResolutionHint'] = layer.minResolution
        if layer.minResolution:
            l['maxResolutionHint'] = layer.maxResolution

    def _fill_WMTS(self, l, layer, wms_layers, wms, errors):
        l['url'] = layer.url

        if layer.dimensions:
            try:
                l['dimensions'] = json.loads(layer.dimensions)
            except:  # pragma: no cover
                errors.append(
                    u"Unexpected error: '%s' while reading '%s' in layer '%s'" %
                    (sys.exc_info()[0], layer.dimensions, layer.name))

        mapserverproxy_url = self.request.route_url('mapserverproxy')

        if layer.style:
            l['style'] = layer.style
        if layer.matrixSet:
            l['matrixSet'] = layer.matrixSet

        if layer.wmsUrl:
            l['wmsUrl'] = layer.wmsUrl
        elif layer.wmsLayers or layer.queryLayers:
            l['wmsUrl'] = mapserverproxy_url
        if layer.wmsLayers:
            l['wmsLayers'] = layer.wmsLayers
        elif layer.wmsUrl:
            l['wmsLayers'] = layer.name
        # needed for external WMTS
        if layer.queryLayers == '[]':  # pragma: no cover
            l['queryLayers'] = []

        if layer.minResolution:
            l['minResolutionHint'] = layer.minResolution
        if layer.minResolution:
            l['maxResolutionHint'] = layer.maxResolution

        # if we have associated local WMS layers then look at what's in the
        # WMS capabilities, and add a queryLayers array with the "resolution
        # hint" information.
        if 'wmsUrl' in l and l['wmsUrl'] == mapserverproxy_url:

            query_layers = layer.queryLayers.strip('[]') \
                if layer.queryLayers else l['wmsLayers']
            l['queryLayers'] = []

            for query_layer in query_layers.split(','):
                if query_layer not in wms_layers:
                    continue
                query_layer_obj = wms[query_layer]

                ql = {'name': query_layer}
                resolutions = self._getLayerResolutionHint(query_layer_obj)

                if resolutions[0] <= resolutions[1]:
                    ql['minResolutionHint'] = float(
                        '%0.2f' % resolutions[0])
                    ql['maxResolutionHint'] = float(
                        '%0.2f' % resolutions[1])

                if 'minResolutionHint' in ql or \
                   'maxResolutionHint' in ql:
                    l['queryLayers'].append(ql)

                # FIXME we do not support WMTS layers associated to
                # MapServer layer groups for now.

    def _group(self, group, layers, wms_layers, wms, depth=1):
        children = []
        errors = []

        # escape loop
        if depth > 10:
            return None, errors, True
        depth += 1

        for treeItem in sorted(group.children, key=lambda item: item.order):
            if type(treeItem) == LayerGroup:
                if (type(group) == Theme or
                        group.isInternalWMS == treeItem.isInternalWMS):
                    gp, gp_errors, stop = self._group(treeItem, layers,
                                                      wms_layers, wms, depth)
                    errors += gp_errors
                    if stop:
                        errors.append("Too many recursions with group \"%s\""
                                      % group.name)
                        return None, errors, True
                    if gp is not None:
                        children.append(gp)
                else:
                    errors.append(
                        "Group %s connot be in group %s (wrong isInternalWMS)." %
                        (treeItem.name, group.name))
            elif type(treeItem) == Layer:
                if (treeItem in layers):
                    if (group.isInternalWMS ==
                            (treeItem.layerType == 'internal WMS')):
                        l, l_errors = self._layer(treeItem, wms_layers, wms)
                        errors += l_errors
                        children.append(l)
                    else:
                        errors.append(
                            "Layer %s of type %s cannot be in the group %s." %
                            (treeItem.name, treeItem.layerType, group.name))

        if len(children) > 0:
            g = {
                'name': group.name,
                'children': children,
                'isExpanded': group.isExpanded,
                'isInternalWMS': group.isInternalWMS,
                'isBaseLayer': group.isBaseLayer
            }
            if group.metadataURL:
                g['metadataURL'] = group.metadataURL
            return g, errors, False
        else:
            return None, errors, False

    @cache_region.cache_on_arguments()
    def _themes(self, role_id, mobile=False):
        """
        This function returns theme information for the role identified
        to by ``role_id``.
        ``mobile`` tells whether to retrieve mobile or desktop layers
        """
        errors = []
        query = self._create_layer_query(role_id)
        filter = Layer.inDesktopViewer == True if not mobile else \
            Layer.inMobileViewer == True
        query = query.filter(filter)
        query = query.order_by(Layer.order.asc())
        layers = query.all()

        # retrieve layers metadata via GetCapabilities
        wms, wms_errors = self._wms_getcap(
            self.request.registry.settings['mapserv_url'])
        if len(wms_errors) > 0:
            return [], wms_errors

        wms_layers = list(wms.contents)

        themes = DBSession.query(Theme).order_by(Theme.order.asc())

        exportThemes = []
        for theme in themes:
            children, children_errors, stop = self._getChildren(
                theme, layers, wms_layers, wms)
            errors += children_errors
            if stop:
                break
            # test if the theme is visible for the current user
            if len(children) > 0:
                icon = self._getIconPath(theme.icon) \
                    if theme.icon \
                    else self.request.static_url(
                        'c2cgeoportal:static/images/blank.gif')

                exportThemes.append({
                    'inDesktopViewer': theme.inDesktopViewer,
                    'inMobileViewer': theme.inMobileViewer,
                    'name': theme.name,
                    'icon': icon,
                    'children': children
                })

        return exportThemes, errors

    def _getChildren(self, theme, layers, wms_layers, wms):
        children = []
        errors = []
        for item in sorted(theme.children, key=lambda item: item.order):
            if type(item) == LayerGroup:
                gp, gp_errors, stop = self._group(item, layers, wms_layers, wms)
                errors += gp_errors
                if stop:
                    errors.append("Themes listing interrupted because of an error"
                                  " with theme \"%s\"" % theme.name)
                    return children, errors, True
                if gp is not None:
                    children.append(gp)
            elif type(item) == Layer:
                if item in layers:
                    l, l_errors = self._layer(item, wms_layers, wms)
                    errors += l_errors
                    children.append(l)
        return children, errors, False

    def _get_wfs_url(self):
        if 'mapserv_wfs_url' in self.request.registry.settings and \
                self.request.registry.settings['mapserv_wfs_url']:
            return self.request.registry.settings['mapserv_wfs_url']
        return self.request.registry.settings['mapserv_url']

    def _internal_wfs_types(self):
        return self._wfs_types(self._get_wfs_url())

    def _get_external_wfs_url(self):
        if 'external_mapserv_wfs_url' in self.request.registry.settings and \
                self.request.registry.settings['external_mapserv_wfs_url']:
            return self.request.registry.settings['external_mapserv_wfs_url']
        if 'external_mapserv_url' in self.request.registry.settings and \
                self.request.registry.settings['external_mapserv_url']:
            return self.request.registry.settings['external_mapserv_url']
        return None

    def _external_wfs_types(self):
        url = self._get_external_wfs_url()
        if not url:
            return [], []
        return self._wfs_types(url)

    @cache_region.cache_on_arguments()
    def _wfs_types(self, wfs_url):
        errors = []

        # retrieve layers metadata via GetCapabilities
        params = (
            ('SERVICE', 'WFS'),
            ('VERSION', '1.0.0'),
            ('REQUEST', 'GetCapabilities'),
        )
        if wfs_url.find('?') < 0:
            wfs_url += '?'
        wfsgc_url = wfs_url + '&'.join(['='.join(p) for p in params])
        log.info("WFS GetCapabilities for base url: %s" % wfsgc_url)

        # forward request to target (without Host Header)
        http = httplib2.Http()
        h = dict(self.request.headers)
        if urlparse(wfsgc_url).hostname != 'localhost':  # pragma: no cover
            h.pop('Host')
        try:
            resp, getCapabilities_xml = http.request(wfsgc_url, method='GET', headers=h)
        except:  # pragma: no cover
            errors.append("Unable to GetCapabilities from url %s" % wfsgc_url)
            return None, errors

        if resp.status < 200 or resp.status >= 300:  # pragma: no cover
            errors.append(
                "GetCapabilities from url %s return the error: %i %s" %
                (wfsgc_url, resp.status, resp.reason)
            )
            return None, errors

        try:
            getCapabilities_dom = parseString(getCapabilities_xml)
            featuretypes = []
            for featureType in getCapabilities_dom.getElementsByTagNameNS(self.WFS_NS,
                                                                          "FeatureType"):
                # don't includes FeatureType without name
                name = featureType.getElementsByTagNameNS(self.WFS_NS, "Name").item(0)
                if name:
                    nameValue = name.childNodes[0].data
                    # ignore namespace
                    if nameValue.find(':') >= 0:
                        nameValue = nameValue.split(':')[1] # pragma nocover
                    featuretypes.append(nameValue)
                else:  # pragma nocover
                    log.warn("Feature type without name: %s" % featureType.toxml())
            return featuretypes, errors
        except:  # pragma: no cover
            return getCapabilities_xml, errors

    @cache_region.cache_on_arguments()
    def _external_themes(self):  # pragma nocover
        errors = []

        if not ('external_themes_url' in self.settings
                and self.settings['external_themes_url']):
            return None, errors
        ext_url = self.settings['external_themes_url']
        if self.request.user is not None and \
                hasattr(self.request.user, 'parent_role') and \
                self.request.user.parent_role is not None:
            ext_url += '?role_id=' + str(self.request.user.parent_role.id)

        # forward request to target (without Host Header)
        http = httplib2.Http()
        h = dict(self.request.headers)
        if urlparse(ext_url).hostname != 'localhost':
            h.pop('Host')
        try:
            resp, content = http.request(ext_url, method='GET', headers=h)
        except:
            errors.append(
                "Unable to get external themes from url %s" % ext_url
            )
            return None, errors

        if resp.status < 200 or resp.status >= 300:
            errors.append(
                "Get external themes from url %s return the error: %i %s" %
                (ext_url, resp.status, resp.reason)
            )
            return None, errors

        return content, errors

    def _functionality(self):
        functionality = {}
        for func in get_setting(
                self.settings,
                ('functionalities', 'available_in_templates'), []):
            functionality[func] = get_functionality(
                func, self.settings, self.request)
        return functionality

    def _getVars(self):
        role_id = None if self.request.user is None else \
            self.request.user.role.id

        themes, errors = self._themes(role_id)
        themes = filter(lambda theme: theme['inDesktopViewer'], themes)
        wfs_types, add_errors = self._internal_wfs_types()
        errors.extend(add_errors)
        external_wfs_types, add_errors = self._external_wfs_types()
        errors.extend(add_errors)
        external_themes, add_errors = self._external_themes()
        errors.extend(add_errors)

        layers_enum = {}
        if 'layers_enum' in self.request.registry.settings:
            for layer_name, layer in \
                    self.request.registry.settings['layers_enum'].items():
                layer_enum = {}
                layers_enum[layer_name] = layer_enum
                for attribute in layer['attributes'].keys():
                    layer_enum[attribute] = self.request.route_url(
                        'layers_enumerate_attribute_values',
                        layer_name=layer_name,
                        field_name=attribute,
                        path=''
                    )

        d = {
            'themes': json.dumps(themes),
            'user': self.request.user,
            'WFSTypes': json.dumps(wfs_types),
            'externalWFSTypes': json.dumps(external_wfs_types),
            'external_themes': external_themes,
            # for backward compatibility
            'tilecache_url': json.dumps(self.settings.get("tilecache_url")),
            'tiles_url': json.dumps(self.settings.get("tiles_url")),
            'functionality': self._functionality(),
            'queryer_attribute_urls': json.dumps(layers_enum),
            'serverError': json.dumps(errors),
        }

        # handle permalink_themes
        permalink_themes = self.request.params.get('permalink_themes')
        if permalink_themes:
            d['permalink_themes'] = json.dumps(permalink_themes.split(','))

        return d

    @view_config(route_name='home', renderer='index.html')
    def home(self, templates_params=None):
        d = {
            'lang': self.lang,
            'debug': self.debug,
            'extra_params': '?lang=%s&' % self.lang if self.lang else '?'
        }

        # general templates_params handling
        if templates_params is not None:
            d = dict(d.items() + templates_params.items())
        # specific permalink_themes handling
        if 'permalink_themes' in d:
            d['extra_params'] = d['extra_params'] + d['permalink_themes']

        # check if route to mobile app exists
        try:
            d['mobile_url'] = self.request.route_url('mobile_index_prod')
        except:
            d['mobile_url'] = None

        d['no_redirect'] = self.request.params.get('no_redirect') is not None

        return d

    @view_config(route_name='viewer', renderer='viewer.js')
    def viewer(self):
        d = self._getVars()
        d['lang'] = self.lang
        d['debug'] = self.debug

        self.request.response.content_type = 'application/javascript'
        return d

    @view_config(route_name='edit', renderer='edit.html')
    def edit(self):
        return {
            'lang': self.lang,
            'debug': self.debug,
            'extra_params': '?lang=%s&' % self.lang if self.lang else '?'
        }

    @view_config(route_name='edit.js', renderer='edit.js')
    def editjs(self):
        d = self._getVars()
        d['lang'] = self.lang
        d['debug'] = self.debug

        self.request.response.content_type = 'application/javascript'
        return d

    @view_config(route_name='routing', renderer='routing.html')
    def routing(self):
        return {
            'lang': self.lang,
            'debug': self.debug,
            'extra_params': '?lang=%s&' % self.lang if self.lang else '?'
        }

    @view_config(route_name='routing.js', renderer='routing.js')
    def routingjs(self):
        d = self._getVars()
        d['lang'] = self.lang
        d['debug'] = self.debug

        self.request.response.content_type = 'application/javascript'
        return d

    def mobile(self):
        """
        View callable for the mobile application's index.html file.
        """
        return {'lang': self.lang}

    def mobileconfig(self):
        """
        View callable for the mobile application's config.js file.
        """
        errors = []
        layer_info = []
        public_only = True

        mobile_default_themes = get_functionality(
            'mobile_default_theme',
            self.settings,
            self.request
        )
        theme_name = self.request.params.get(
            'theme',
            mobile_default_themes[0] if len(mobile_default_themes) > 0 else None
        )
        user = self.request.user

        role_id = None if user is None else user.role.id
        themes, errors = self._themes(role_id, True)
        if theme_name:

            themes = filter(lambda theme: theme['name'] == theme_name, themes)
            theme = themes[0] if len(themes) > 0 else None

            def process(node, layer_info, public_only=True):
                if 'children' in node:
                    for child_node in node['children']:
                        public_only = process(
                            child_node, layer_info, public_only)
                else:
                    layer_info.append(node)
                    public_only = public_only and node['public'] is True
                return public_only

            if theme is not None:
                public_only = process(theme, layer_info)

        # we only support WMS layers right now
        layer_info = filter(lambda li: li['type'] == 'internal WMS', layer_info)

        # comma-separated string including the names of layers of the
        # requested theme
        layers = ','.join(reversed([li['name'] for li in layer_info]))

        # comma-separated string including the names of layers that
        # should visible by default in the map
        visible_layers = filter(lambda li: li['isChecked'] is True, layer_info)
        visible_layers = ','.join(reversed([li['name'] for li in visible_layers]))

        # comma-separated string including the feature types supported
        # by WFS service
        wfs_types, errors = self._internal_wfs_types()
        if len(errors) > 0:  # pragma: no cover
            raise HTTPBadGateway('\n'.join(errors))
        wfs_types = ','.join(wfs_types)

        # info includes various information that is not used by config.js,
        # but by other - private to the integrator - parts of the mobile
        # application.
        info = {
            'username': user.username if user else '',
            'publicLayersOnly': public_only
        }

        # get the list of themes available for mobile
        themes_ = []
        themes, errors = self._themes(role_id, True)
        for theme in themes:
            if theme['inMobileViewer']:
                themes_.append({
                    'name': theme['name'],
                    'icon': theme['icon']
                })

        self.request.response.content_type = 'application/javascript'
        return {
            'lang': self.lang,
            'themes': json.dumps(themes_),
            'layers': layers,
            'visible_layers': visible_layers,
            'wfs_types': wfs_types,
            'server_error': json.dumps(errors),
            'info': json.dumps(info)
        }

    @view_config(route_name='apijs', renderer='api/api.js')
    def apijs(self):
        wms, wms_errors = self._wms_getcap(
            self.request.registry.settings['mapserv_url'])
        if len(wms_errors) > 0:  # pragma: no cover
            raise HTTPBadGateway('\n'.join(wms_errors))
        queryable_layers = [
            name for name in list(wms.contents)
            if wms[name].queryable == 1]
        d = {
            'lang': self.lang,
            'debug': self.debug,
            'queryable_layers': json.dumps(queryable_layers)
        }
        self.request.response.content_type = 'application/javascript'
        return d

    @view_config(route_name='xapijs', renderer='api/xapi.js')
    def xapijs(self):
        wms, wms_errors = self._wms_getcap(
            self.request.registry.settings['mapserv_url'])
        queryable_layers = [
            name for name in list(wms.contents)
            if wms[name].queryable == 1]
        d = {
            'lang': self.lang,
            'debug': self.debug,
            'queryable_layers': json.dumps(queryable_layers)
        }
        self.request.response.content_type = 'application/javascript'
        return d

    @view_config(route_name='apihelp', renderer='api/apihelp.html')
    def apihelp(self):
        return {
            'lang': self.lang,
            'debug': self.debug,
        }

    @view_config(route_name='xapihelp', renderer='api/xapihelp.html')
    def xapihelp(self):
        return {
            'lang': self.lang,
            'debug': self.debug,
        }

    @view_config(route_name='themes', renderer='json')
    def themes(self):
        role_id = self.request.params.get("role_id") or None
        if role_id is None and self.request.user is not None:
            role_id = self.request.user.role.id
        themes = self._themes(role_id)[0]
        return filter(lambda theme: theme['inDesktopViewer'], themes)

    @view_config(context=HTTPForbidden, renderer='login.html')
    def loginform403(self):
        if authenticated_userid(self.request):
            return HTTPForbidden()  # pragma: no cover
        return {
            'lang': self.lang,
            'came_from': self.request.path,
        }

    @view_config(route_name='loginform', renderer='login.html')
    def loginform(self):
        return {
            'lang': self.lang,
            'came_from': self.request.params.get("came_from") or "/",
        }

    @view_config(route_name='login')
    def login(self):
        login = self.request.params.get('login', None)
        password = self.request.params.get('password', None)
        if not (login and password):
            return HTTPBadRequest('"login" and "password" should be " \
                    "available in request params')  # pragma nocover
        if self.request.registry.validate_user(self.request, login, password):
            headers = remember(self.request, login)
            log.info("User '%s' logged in." % login)

            cameFrom = self.request.params.get("came_from")
            if cameFrom:
                return HTTPFound(location=cameFrom, headers=headers)
            else:
                return Response('true', headers=headers)
        else:
            return HTTPUnauthorized('bad credentials')

    @view_config(route_name='logout')
    def logout(self):
        headers = forget(self.request)
        cameFrom = self.request.params.get("came_from")

        # if there's no user to log out, we send a 404 Not Found (which
        # is the status code that applies best here)
        if not self.request.user:
            return HTTPNotFound()

        log.info("User '%s' (%i) logging out." % (self.request.user.username,
                                                  self.request.user.id))

        if cameFrom:
            return HTTPFound(location=cameFrom, headers=headers)
        else:
            return HTTPFound(
                location=self.request.route_url('home'),
                headers=headers)

    @view_config(route_name='loginchange')
    def loginchange(self):
        new_password = self.request.params.get('newPassword', None)
        new_password_confirm = self.request.params.get('confirmNewPassword', None)
        if new_password is None or new_password_confirm is None:
            raise HTTPBadRequest('"newPassword" and "confirmNewPassword" should be \
                   available in request params')

        # check if loggedin
        if not self.request.user:
            raise HTTPUnauthorized('bad credentials')
        if new_password != new_password_confirm:
            raise HTTPBadRequest("the new password and the new password \
                   confirmation don't match")

        u = self.request.user
        u._set_password(new_password)
        u.is_password_changed = True
        DBSession.flush()
        log.info("password changed for user: %s" % self.request.user.username)

        # handle replication
        if 'auth_replication_enabled' in self.request.registry.settings and \
                self.request.registry.settings['auth_replication_enabled'] == \
                'true':  # pragma: no cover
            try:
                log.debug("trying to find if engine set for replication exists")
                engine = sqlahelper.get_engine('replication')
            except RuntimeError:
                log.debug("engine for replication doesn't exist yet, trying \
                          to create")
                engine = engine_from_config(
                    self.request.registry.settings,
                    'sqlalchemy_replication.')
                sqlahelper.add_engine(engine, 'replication')

            DBSession2 = scoped_session(sessionmaker(bind=engine))

            dbuser_r = DBSession2.query(User).filter(User.id == self.request.user.id)
            result = dbuser_r.all()
            if len(result) == 0:
                msg = 'user not found in replication target database: %s' \
                    % self.request.user.username
                log.exception(msg)
                return HTTPBadRequest(msg)  # pragma nocover
            else:
                u_r = dbuser_r.all()[0]
                u_r._set_password(new_password)
                u_r.is_password_changed = True
                DBSession2.commit()
                log.info("password changed in replication target database \
                    for user: %s" % self.request.user.username)

        return Response('true')

    @view_config(route_name='permalinktheme', renderer='index.html')
    def permalinktheme(self):
        # recover themes from url route
        themes = self.request.matchdict['themes']
        d = {}
        d['permalink_themes'] = 'permalink_themes=' + ','.join(themes)
        # call home with extra params
        return self.home(d)
