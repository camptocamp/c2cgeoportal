# -*- coding: utf-8 -*-

import urllib
import logging
import json
import sys

from pyramid.view import view_config
from pyramid.i18n import get_locale_name, TranslationStringFactory
from pyramid.httpexceptions import HTTPFound, HTTPNotFound, \
        HTTPBadRequest, HTTPUnauthorized, HTTPForbidden
from pyramid.security import remember, forget, authenticated_userid
from pyramid.response import Response
from sqlalchemy.sql.expression import and_
from geoalchemy.functions import functions
from owslib.wms import WebMapService
from xml.dom.minidom import parseString
from math import sqrt

from c2cgeoportal.lib import get_setting
from c2cgeoportal.lib.functionality import get_functionality, get_functionalities
from c2cgeoportal.models import DBSession, Layer, LayerGroup, Theme, \
        RestrictionArea, Role, layer_ra, role_ra


_ = TranslationStringFactory('c2cgeoportal')
log = logging.getLogger(__name__)


class Entry(object):

    def __init__(self, request):
        self.request = request
        self.settings = request.registry.settings
        self.debug = "debug" in request.params
        self.lang = get_locale_name(request)
        self.serverError = []

        # detect if HTTPS scheme must be set
        https_flag = self.settings.get('https_flag_header')
        if https_flag:
            https_flag = https_flag.upper()
            if https_flag in self.request.headers and \
               self.request.headers[https_flag] == self.settings.get('https_flag_value'):
                self.request.scheme = 'https'

    @view_config(route_name='testi18n', renderer='testi18n.html')
    def testi18n(self):
        _ = self.request.translate  # pragma: no cover
        return {'title': _('title i18n')}  # pragma: no cover

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
            return None  # pragma: no cover
        icon = str(icon)
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
        l = {
            'id': layer.id,
            'name': layer.name,
            'type': layer.layerType,
            'legend': layer.legend,
            'isChecked': layer.isChecked,
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

    def _fill_internal_WMS(self, l, layer, wms_layers, wms):
        self._fill_WMS(l, layer)
        self._fill_legend_rule_query_string(l, layer,
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
        else:
            log.warning('layer %s not defined in WMS caps doc', layer.name)

    def _fill_external_WMS(self, l, layer):
        self._fill_WMS(l, layer)
        self._fill_legend_rule_query_string(l, layer, layer.url)

        l['url'] = layer.url
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
        elif layer.wmsLayers:
            l['wmsUrl'] = self.request.route_url('mapserverproxy')
            l['wmsLayers'] = layer.wmsLayers
        elif layer.wmsUrl:
            l['wmsUrl'] = layer.wmsUrl
            l['wmsLayers'] = layer.name

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

        exportThemes = []
        errors = "\n"

        # retrieve layers metadata via GetCapabilities
        wms_url = self.request.registry.settings['mapserv_url'] + \
            (('?role_id=' + str(role_id)) if role_id else '')
        log.info("WMS GetCapabilities for base url: %s" % wms_url)
        try:
            wms = WebMapService(wms_url, version='1.1.1')
        except AttributeError:
            errors = _("WARNING! an error occured while trying to read the mapfile and recover the themes")
            self.serverError.append(errors)
            log.exception(errors)

            return (exportThemes, errors)
        wms_layers = list(wms.contents)

        themes = DBSession.query(Theme).order_by(Theme.order.asc())

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

    def _WFSTypes(self, external=False):
        # retrieve layers metadata via GetCapabilities
        role_id = None
        if self.request.user:
            role_id = self.request.user.parent_role.id if external \
                      else self.request.user.role.id
        params = (
            ('role_id', str(role_id) if role_id else ''),
            ('SERVICE', 'WFS'),
            ('VERSION', '1.0.0'),
            ('REQUEST', 'GetCapabilities'),
        )
        wfs_url = self.request.registry.settings['external_mapserv_url'] if external \
                    else self.request.registry.settings['mapserv_url']
        if wfs_url.find('?') < 0:
            wfs_url += '?'
        wfsgc_url = wfs_url + '&'.join(['='.join(p) for p in params])
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
        d['serverError'] = json.dumps(self.serverError)

        if 'external_mapserv_url' in self.settings \
                and self.settings['external_mapserv_url']:
            d['externalWFSTypes'] = json.dumps(self._WFSTypes(True))
        else:
            d['externalWFSTypes'] = '[]'

        if 'external_themes_url' in self.settings \
                and self.settings['external_themes_url']:
            ext_url = self.settings['external_themes_url']
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
        for func in get_setting(self.settings,
                ('functionalities', 'webclient_string'), []):
            functionality[func] = get_functionality(func, self.settings,
                    self.request)
        d['functionality'] = json.dumps(functionality)

        functionalities = dict()
        for func in get_setting(self.settings,
                ('functionalities', 'webclient_array'), []):
            functionalities[func] = get_functionalities(func, self.settings,
                    self.request)
        d['functionalities'] = json.dumps(functionalities)

        # handle permalink_themes
        permalink_themes = self.request.params.get('permalink_themes', None)
        if permalink_themes:
            d['permalink_themes'] = json.dumps(permalink_themes.split(','))

        return d

    @view_config(route_name='home', renderer='index.html')
    def home(self, templates_params=None):
        d = {
            'lang': self.lang,
            'debug': self.debug,
            'extra_params': '?'
        }
        # general templates_params handling
        if templates_params is not None:
            d = dict(d.items() + templates_params.items())
        # specific permalink_themes handling
        if 'permalink_themes' in d:
            d['extra_params'] = d['extra_params'] + d['permalink_themes']
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
        }

    @view_config(route_name='edit.js', renderer='edit.js')
    def editjs(self):
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
        return {
            'lang': self.lang,
            'debug': self.debug,
        }

    @view_config(route_name='themes', renderer='json')
    def themes(self):
        d = {}
        d['role_id'] = self.request.params.get("role_id", None)
        return self._themes(d)[0]

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
            return HTTPFound(location=self.request.route_url('home'),
                    headers=headers)

    @view_config(route_name='permalinktheme', renderer='index.html')
    def permalinktheme(self):
        # recover themes from url route
        themes = self.request.matchdict['themes']
        d = {}
        d['permalink_themes'] = 'permalink_themes=' + ','.join(themes)
        # call home with extra params
        return self.home(d)
