# -*- coding: utf-8 -*-

import urllib
import logging

from pyramid.view import view_config
from pyramid.i18n import get_locale_name
from pyramid.compat import json
from pyramid.httpexceptions import HTTPFound, HTTPBadRequest, HTTPUnauthorized
from pyramid.security import remember, forget, authenticated_userid
from pyramid.response import Response
from sqlalchemy.sql.expression import and_
from geoalchemy.functions import functions
from owslib.wms import WebMapService

from c2cgeoportal.lib.functionality import get_functionality, get_functionalities
from c2cgeoportal.models import DBSession, Layer, LayerGroup, Theme, \
        RestrictionArea, Role, layer_ra, role_ra, User

log = logging.getLogger(__name__)


class Entry(object):

    _user = False

    def __init__(self, request):
        self.request = request
        self.settings = request.registry.settings
        self.debug = "debug" in request.params
        self.lang = get_locale_name(request)
        self.username = authenticated_userid(request)

    @property
    def user(self):
        if self.username is None:
            return None
        if self._user == False:
            self._user = DBSession.query(User).filter_by(
                    username=self.username).one()
        return self._user


    @view_config(route_name='testi18n', renderer='testi18n.html')
    def testi18n(self):
        _ = self.request.translate
        return { 'title': _('title i18n') }
    
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
            resolutionHintMin = float(layer.scaleHint['min'])
            resolutionHintMax = float(layer.scaleHint['max'])
        for childLayer in layer.layers:
            resolution = self._getLayerResolutionHint(childLayer)
            resolutionHintMin = min(resolutionHintMin, resolution[0])
            resolutionHintMax = max(resolutionHintMax, resolution[1])

        return (resolutionHintMin, resolutionHintMax)

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
            'name': layer.name,
            'type': layer.layerType,
            'imageType': layer.imageType,
            'no2D': layer.no2D,
            'legend': layer.legend,
            'isVisible': layer.isVisible
        }
        if layer.disclaimer:
            l['disclaimer'] = layer.disclaimer
        if layer.icon:
            l['icon'] = self._getIconPath(layer.icon)
        if layer.kml:
            l['kml'] = layer.kml

        if layer.layerType == "internal WMS":
            metadataUrls = layer.metadataURL or ""
            # this is a leaf, ie. a Mapserver layer
            # => add the metadata URL if any
            if len(metadataUrls) == 0 and layer.name in wms_layers:
                metadataUrls = self._getLayerMetadataUrls(wms[layer.name])
            if layer.minResolution and layer.maxResolution:
                l['minResolutionHint'] = layer.minResolution
                l['maxResolutionHint'] = layer.maxResolution
            else:
                if layer.name in wms_layers:
                    resolutions = self._getLayerResolutionHint(wms[layer.name])
                    if resolutions[0] <= resolutions[1]:
                        l['minResolutionHint'] = float('%0.2f'%resolutions[0])
                        l['maxResolutionHint'] = float('%0.2f'%resolutions[1])
            if len(metadataUrls) > 0:
                l['metadataUrls'] = metadataUrls
            if layer.legendRule:
                l['legendRule'] = layer.legendRule

        else:
            if layer.legendImage:
                l['legendImage'] = layer.legendImage
            if layer.minResolution and layer.maxResolution:
                l['minResolutionHint'] = layer.minResolution
                l['maxResolutionHint'] = layer.maxResolution
            if layer.metadataURL:
                l['metadataURL'] = layer.metadataURL

            if layer.layerType == "external WMS":
                l['url'] == layer.url
                l['isSingleTile'] = layer.isSingleTile

            if layer.layerType == "external WMTS":
                l['url'] == layer.url
                l['maxExtent'] == layer.maxExtent
                l['serverResolutions'] == layer.serverResolutions

        return l

    def _group(self, group, layers, wms_layers, wms):
        children = [] 
        error = ""
        for treeItem in sorted(group.children, key=lambda item: item.order):
            if type(treeItem) == LayerGroup:
                if (type(group) == Theme or
                    group.isInternalWMS == treeItem.isInternalWMS):
                    c, e = self._group(treeItem, layers, wms_layers, wms)
                    error += e
                    if c != None:
                        children.append(c)
                else:
                    error += "Group %s connot be in group %s " \
                             "(wrong isInternalWMS).\n" % \
                             (treeItem.name, group.name)
            elif type(treeItem) == Layer:
                if (treeItem in layers):
                    if (group.isInternalWMS ==
                        (treeItem.layerType == 'internal WMS')):
                        children.append(self._layer(treeItem, wms_layers, wms))
                    else:
                        error += "Layer %s of type %s cannot be " \
                                 "in the group %s.\n" % \
                                 (treeItem.name, treeItem.layerType, group.name)

        if len(children) > 0:
            group = {
                'name': group.name,
                'children': children,
                'isExpanded': group.isExpanded,
                'isInternalWMS' : group.isInternalWMS,
                'isBaseLayer' : group.isBaseLayer
            }
            return (group, error)
        else:
            return (None, error)

    def _themes(self, d):
        query = DBSession.query(Layer).filter(Layer.public == True)

        if 'role_id' in d and d['role_id'] is not None and d['role_id'] != '':
            role_id = d['role_id']
        elif self.user is not None:
            role_id = self.user.role.id
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

        layers = query.order_by(Layer.order.asc()).all()

        # retrieve layers metadata via GetCapabilities
        wms_url = self.request.route_url('mapserverproxy')
        log.info("GetCapabilities for base url: %s"%wms_url)
        wms = WebMapService(wms_url, version='1.1.1')
        wms_layers = list(wms.contents)

        themes = DBSession.query(Theme).order_by(Theme.order.asc()) 
        exportThemes = []

        error = "\n"

        #TODO: optimize following code to avoid parsing layers list many times?
        for theme in themes:
            if theme.display:
                children = []

                for item in sorted(theme.children, key=lambda item: item.order):
                    if type(item) == LayerGroup: 
                        (c, e) = self._group(item, layers, wms_layers, wms)
                        error += e
                        if c != None:
                            children.append(c)

                    elif type(item) == Layer:
                        if (item in layers):
                            children.append(self._layer(item, wms_layers, wms))

                if len(children) > 0:
                    icon = self._getIconPath(theme.icon) if theme.icon else \
                           self.request.static_url('c2cgeoportal:static' + \
                                                   '/images/blank.gif')
                    exportThemes.append({
                        'name': theme.name,
                        'icon': icon,
                        'children': children 
                    })

        return (exportThemes, error)

    def _getForLang(self, key):
        try:
            return json.loads(self.settings.get(key).strip("\"'"))[self.lang]
        except ValueError:
            return self.settings.get(key)

    def _getVars(self):
        d = {}
        (themes, errors) = self._themes(d)
        d['themes'] = json.dumps(themes)
        d['themesError'] = errors
        d['user'] = self.user
        
        if self.settings.get("external_themes_url") != '':
            ext_url = self.settings.get("external_themes_url")
            if self.user is not None and hasattr(self.user, 'parent_role'):
                ext_url += '?role_id=' + str(self.user.parent_role.id)

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
        d = self._getVars()

        d['lang'] = self.lang
        d['debug'] = self.debug

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
        user = DBSession.query(User).filter_by(username=login).first()
        if user and user.validate_password(password):
            headers = remember(self.request, login)

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
        if cameFrom:
            return HTTPFound(location=cameFrom, headers=headers)
        else:
            return HTTPFound(location = self.request.route_url('home'),
                    headers = headers)
