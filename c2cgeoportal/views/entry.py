# -*- coding: utf-8 -*-

import urllib
import logging
import json
import sys

from pyramid.view import view_config
from pyramid.i18n import get_locale_name
from pyramid.compat import json
from pyramid.httpexceptions import (HTTPFound, HTTPNotFound,
                                    HTTPBadRequest, HTTPUnauthorized)
from pyramid.security import remember, forget
from pyramid.response import Response
from sqlalchemy.sql.expression import and_
from geoalchemy.functions import functions
from owslib.wms import WebMapService
from xml.dom.minidom import parseString
from math import sqrt

from c2cgeoportal.lib.functionality import get_functionality, get_functionalities
from c2cgeoportal.models import DBSession, Layer, LayerGroup, Theme, \
        RestrictionArea, Role, layer_ra, role_ra

log = logging.getLogger(__name__)


class Entry(object):

    _user = False

    def __init__(self, request):
        self.request = request
        self.settings = request.registry.settings
        self.debug = "debug" in request.params
        self.lang = get_locale_name(request)

    @view_config(route_name='testi18n', renderer='testi18n.html')
    def testi18n(self):
        _ = self.request.translate
        return {'title': _('title i18n')}

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
            child_layers_info.append(child_layer_info)
        return child_layers_info

    def _getIconPath(self, icon):
        if not icon:
            return None
        icon = str(icon)
        # test full URL
        if not icon[0:4] == 'http':
            try:
                # test full resource ref
                if icon.find(':') < 0:
                    if icon[0] is not '/':
                        icon = '/' + icon
                    icon = self.request.static_url(self.settings['project'] + ':static' + icon)
                else:
                    icon = self.request.static_url(icon)
            except ValueError:
                log.exception('can\'t generate url for icon: %s' % icon)
                return None
        return icon

    def _layer(self, layer, wms_layers, wms):
        l = {
            'id': layer.id,
            'name': layer.name,
            'type': layer.layerType,
            'legend': layer.legend,
            'isVisible': layer.isVisible,
            'isChecked': layer.isChecked,
            'identifierAttribute': layer.identifierAttributeField
        }
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
            l['legendImage'] = layer.legendImage

        if layer.layerType == "internal WMS":
            self._fill_internal_WMS(l, layer, wms_layers, wms)
        elif layer.layerType == "external WMS":
            self._fill_external_WMS(l, layer)
        elif layer.layerType == "WMTS":
            self._fill_WMTS(l, layer)

        return l

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
        l['url'] = layer.url
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
            l['icon'] = self.request.route_url('mapserverproxy') \
                    + '?' + '&'.join('='.join(p) for p in query)
        if layer.style:
            l['style'] = layer.style

    def _fill_internal_WMS(self, l, layer, wms_layers, wms):
        self._fill_WMS(l, layer)

        # this is a leaf, ie. a Mapserver layer
        if layer.minResolution:
            l['minResolutionHint'] = layer.minResolution
        if layer.maxResolution:
            l['maxResolutionHint'] = layer.maxResolution
        if layer.legendRule:
            l['legendRule'] = layer.legendRule
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
        else:
            log.warning('layer %s not defined in WMS caps doc', layer.name)

    def _fill_external_WMS(self, l, layer):
        self._fill_WMS(l, layer)

        l['isSingleTile'] = layer.isSingleTile

        if layer.minResolution:
            l['minResolutionHint'] = layer.minResolution
        if layer.minResolution:
            l['maxResolutionHint'] = layer.maxResolution

    def _fill_WMTS(self, l, layer):
        l['url'] = layer.url

        if layer.dimensions:
            try:
                l['dimensions'] = json.loads(layer.dimensions)
            except:  # pragma: no cover
                self.errors += (u"Unexpected error: '%s' " + \
                        "while reading '%s' in layer '%s'\n") % (
                        sys.exc_info()[0], layer.dimensions,
                        layer.name)

        if layer.style:
            l['style'] = layer.style
        if layer.matrixSet:
            l['matrixSet'] = layer.matrixSet
        if layer.wmsUrl and layer.wmsLayers:
            l['wmsUrl'] = layer.wmsUrl
            l['wmsLayers'] = layer.wmsLayers
        if layer.wmsLayers:
            l['wmsLayers'] = layer.wmsLayers

        if layer.minResolution:
            l['minResolutionHint'] = layer.minResolution
        if layer.minResolution:
            l['maxResolutionHint'] = layer.maxResolution


    def _group(self, group, layers, wms_layers, wms):
        children = []
        for treeItem in sorted(group.children, key=lambda item: item.order):
            if type(treeItem) == LayerGroup:
                if (type(group) == Theme or
                    group.isInternalWMS == treeItem.isInternalWMS):
                    c = self._group(treeItem, layers, wms_layers, wms)
                    if c != None:
                        children.append(c)
                else:
                    self.errors += "Group %s connot be in group %s " \
                             "(wrong isInternalWMS).\n" % \
                             (treeItem.name, group.name)
            elif type(treeItem) == Layer:
                if (treeItem in layers):
                    if (group.isInternalWMS ==
                        (treeItem.layerType == 'internal WMS')):
                        children.append(self._layer(treeItem, wms_layers, wms))
                    else:
                        self.errors += "Layer %s of type %s cannot be " \
                                 "in the group %s.\n" % \
                                 (treeItem.name, treeItem.layerType, group.name)

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
            return g
        else:
            return None

    def _themes(self, d):
        query = DBSession.query(Layer).filter(Layer.public == True)

        if 'role_id' in d and d['role_id'] is not None and d['role_id'] != '':
            role_id = d['role_id']
        elif self.request.user is not None:
            role_id = self.request.user.role.id
        else:
            role_id = None

        if role_id is not None:
            query2 = DBSession.query(Layer).join( \
                       (layer_ra, Layer.id == layer_ra.c.layer_id), \
                       (RestrictionArea, RestrictionArea.id ==
                                         layer_ra.c.restrictionarea_id), \
                       (role_ra, role_ra.c.restrictionarea_id ==
                                         RestrictionArea.id), \
                       (Role, Role.id == role_ra.c.role_id) \
                     ). \
                     filter(Role.id == role_id). \
                     filter(and_(Layer.public != True,
                                 functions.area(RestrictionArea.area) > 0))
            query = query.union(query2)

        layers = query.filter(Layer.isVisible == True).order_by(Layer.order.asc()).all()

        # retrieve layers metadata via GetCapabilities
        wms_url = self.request.route_url('mapserverproxy')
        log.info("WMS GetCapabilities for base url: %s" % wms_url)
        wms = WebMapService(wms_url, version='1.1.1')
        wms_layers = list(wms.contents)

        themes = DBSession.query(Theme).order_by(Theme.order.asc())
        exportThemes = []

        for theme in themes:
            if theme.display:
                children = list(self._getChildren(
                        theme, layers, wms_layers, wms))
                # test if the theme is visible for the current user
                if len(children) > 0:
                    icon = self._getIconPath(theme.icon) if theme.icon else \
                           self.request.static_url('c2cgeoportal:static' + \
                                                   '/images/blank.gif')
                    exportThemes.append({
                        'name': theme.name,
                        'icon': icon,
                        'children': children
                    })

        return exportThemes

    def _getChildren(self, theme, layers, wms_layers, wms):
        for item in sorted(theme.children, key=lambda item: item.order):
            if type(item) == LayerGroup:
                c = self._group(item, layers, wms_layers, wms)
                if c != None:
                    yield c

            elif type(item) == Layer:
                if (item in layers):
                    yield self._layer(item, wms_layers, wms)

    def _getForLang(self, key):
        try:
            return json.loads(self.settings.get(key).strip("\"'"))[self.lang]
        except ValueError:
            return self.settings.get(key)

    def _WFSTypes(self, external=False):
        # retrieve layers metadata via GetCapabilities
        wfs_url = self.request.route_url('mapserverproxy')
        wfsgc_url = wfs_url + "?service=WFS&version=1.0.0&request=GetCapabilities"
        if external:
            wfsgc_url += '&EXTERNAL=true'
        log.info("WFS GetCapabilities for base url: %s" % wfsgc_url)

        getCapabilities_xml = urllib.urlopen(wfsgc_url).read()
        try:
            getCapabilities_dom = parseString(getCapabilities_xml)
            featuretypes = []
            for featureType in getCapabilities_dom.getElementsByTagName("FeatureType"):
                featuretypes.append(featureType.getElementsByTagName("Name").item(0).childNodes[0].data)
            return featuretypes
        except:
            return getCapabilities_xml

    def _getVars(self):
        d = {}
        self.errors = "\n"
        d['themes'] = json.dumps(self._themes(d))
        d['themesError'] = self.errors
        self.errors = None
        d['user'] = self.request.user
        d['WFSTypes'] = json.dumps(self._WFSTypes())

        if hasattr(self.request.registry.settings, 'external_mapserv.url') \
           and self.settings.get('external_mapserv.url'):
            d['externalWFSTypes'] = json.dumps(self._WFSTypes(True))
        else:
            d['externalWFSTypes'] = '[]'

        if hasattr(self.request.registry.settings, 'external_themes_url') \
           and self.settings.get("external_themes_url"):
            ext_url = self.settings.get("external_themes_url")
            if self.request.user is not None and \
                    hasattr(self.request.user, 'parent_role'):
                ext_url += '?role_id=' + str(self.request.user.parent_role.id)
            result = json.load(urllib.urlopen(ext_url))
            # TODO: what if external server does not respond?
            d['external_themes'] = json.dumps(result)
        else:
            d['external_themes'] = None

        d['tilecache_url'] = self.settings.get("tilecache_url")

        functionality = dict()
        for func in self.settings.get("webclient_string_functionalities").split():
            functionality[func] = get_functionality(func, self.settings, self.request)
        d['functionality'] = json.dumps(functionality)
        functionalities = dict()
        for func in self.settings.get("webclient_array_functionalities").split():
            functionalities[func] = get_functionalities(func, self.settings, self.request)
        d['functionalities'] = json.dumps(functionalities)

        return d

    @view_config(route_name='home', renderer='index.html')
    def home(self):
        return {
            'lang': self.lang,
            'debug': self.debug,
        }

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
        }

    @view_config(route_name='edit.js', renderer='edit.js')
    def viewer(self):
        d = self._getVars()
        d['lang'] = self.lang
        d['debug'] = self.debug

        self.request.response.content_type = 'application/javascript'
        return d

    @view_config(route_name='apiloader', renderer='apiloader.js')
    def apiloader(self):
        d = self._getVars()
        d['lang'] = self.lang
        d['debug'] = self.debug

        self.request.response.content_type = 'application/javascript'
        return d

    @view_config(route_name='apihelp', renderer='apihelp.html')
    def apihelp(self):
        return {'lang': self.lang, 'debug': self.debug}

    @view_config(route_name='themes', renderer='json')
    def themes(self):
        d = {}
        d['role_id'] = self.request.params.get("role_id", None)
        return self._themes(d)[0]

    @view_config(route_name='login')
    def login(self):
        login = self.request.params.get('login', None)
        password = self.request.params.get('password', None)
        if not (login and password):
            return HTTPBadRequest('"login" and "password" should be " \
                    "available in request params')
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
            return HTTPFound(location=self.request.route_url('home'),
                    headers=headers)
