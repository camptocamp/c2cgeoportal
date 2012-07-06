# -*- coding: utf-8 -*-

import logging
from decimal import Decimal

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPInternalServerError, HTTPNotFound

from c2cgeoportal.lib.raster.georaster import GeoRaster
from c2cgeoportal.lib.config import cleanup_json

log = logging.getLogger(__name__)


class Raster(object):

    # cache of GeoRaster instances in function of the layer name
    _rasters = {}

    def __init__(self, request):
        self.request = request
        self.rasters = cleanup_json(self.request.registry.settings['raster'])

    @view_config(route_name='raster', renderer='decimaljson')
    def raster(self):
        lon = float(self.request.params['lon'])
        lat = float(self.request.params['lat'])
        if 'layers' in self.request.params:
            rasters = {}
            layers = self.request.params['layers'].split(',')
            for layer in layers:
                if layer in self.rasters:
                    rasters[layer] = self.rasters[layer]
                else:
                    raise HTTPNotFound("Layer %s not found" % layer)
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
        elif 'type' not in layer or layer['type'] == 'shp_index':
            raster = GeoRaster(layer['file'])
            self._rasters[ref] = raster
        else:
            raise HTTPInternalServerError(
                    "Bad raster type '%s' for raster layer '%s'" \
                    % (layer['type'], ref))  # pragma: no cover

        result = raster.get_value(lon, lat)
        if 'round' in layer:
            result = self._round(result, layer['round'])
        elif result != None:
            result = Decimal(str(result))

        return result

    def _round(self, value, round_to):
        if value != None:
            return Decimal(str(value)).quantize(Decimal(str(round_to)))
        else:
            return None
