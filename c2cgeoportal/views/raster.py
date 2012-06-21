# -*- coding: utf-8 -*-

import logging
from math import floor

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPInternalServerError

from c2cgeoportal.lib.raster.georaster import GeoRaster
from c2cgeoportal.lib.config import cleanup_json

log = logging.getLogger(__name__)


class Raster(object):

    # cache of GeoRaster instances in function of the layer name
    _rasters = {}

    def __init__(self, request):
        self.request = request
        self.rasters = cleanup_json(self.request.registry.settings['raster'])

    @view_config(route_name='raster', renderer='json')
    def raster(self):
        lon = float(self.request.params['lon'])
        lat = float(self.request.params['lat'])
        if 'layers' in self.request.params:
            rasters = {}
            layers = self.request.params['layers'].split(',')
            for layer in layers:
                rasters[layer] = self.rasters[layer]
        else:
            rasters = self.rasters

        result = {}
        for ref in rasters.keys():
            result[ref] = self._get_raster_value(
                    rasters[ref], ref, lon, lat)

        return result

    def _get_raster_value(self, layer, ref, lon, lat):
        if ref in self._rasters:
            raster = self._rasters[ref]
        elif layer['type'] == 'shp_index':
            raster = GeoRaster(layer['file'])
        else:
            raise HTTPInternalServerError("Bad raster type '%s' for raster layer '%s'" \
                    % (layer['type'], ref))

        result = raster.get_value(lon, lat)
        if 'round' in layer:
            result = self._round(result, layer['round'])
        elif result:
            result = str(result)

        return result

    def _round(self, value, round_to):
        if value != None:
            value = round(value / round_to) * round_to
            if (round_to == floor(round_to)):
                return str(int(value))
            else:
                return str(value)
        else:
            return None
