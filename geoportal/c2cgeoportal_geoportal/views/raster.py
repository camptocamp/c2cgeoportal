# -*- coding: utf-8 -*-

# Copyright (c) 2012-2018, Camptocamp SA
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


import logging
import os
from decimal import Decimal
from repoze.lru import LRUCache

from fiona.collection import Collection
import rasterio
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest
from pyramid.view import view_config

from c2cgeoportal_geoportal.lib.caching import set_common_headers, NO_CACHE

log = logging.getLogger(__name__)

_rasters = None


class Raster:

    def __init__(self, request):
        self.request = request
        self.rasters = self.request.registry.settings["raster"]
        global _rasters
        if _rasters is None:
            cache_size = self.rasters.get('cache_size', 10)
            log.debug('initialize LRUCache with size %d' % cache_size)
            _rasters = LRUCache(cache_size)

    @view_config(route_name="raster", renderer="decimaljson")
    def raster(self):
        if 'lon' not in self.request.params:
            raise HTTPBadRequest("'lon' should be in the query string parameters")
        if 'lat' not in self.request.params:
            raise HTTPBadRequest("'lat' should be in the query string parameters")
        try:
            lon = float(self.request.params["lon"])
        except ValueError:
            raise HTTPBadRequest("'lon' ({}) parameters should be a number".format(
                self.request.params["lon"]
            ))
        try:
            lat = float(self.request.params["lat"])
        except ValueError:
            raise HTTPBadRequest("'lat' ({}) parameters should be a number".format(
                self.request.params["lat"]
            ))
        if "layers" in self.request.params:
            rasters = {}
            layers = self.request.params["layers"].split(",")
            for layer in layers:
                if layer in self.rasters:
                    rasters[layer] = self.rasters[layer]
                else:
                    raise HTTPNotFound("Layer {0!s} not found".format(layer))
        else:
            rasters = self.rasters

        result = {}
        for ref in list(rasters.keys()):
            result[ref] = self._get_raster_value(rasters[ref], lon, lat)

        set_common_headers(self.request, "raster", NO_CACHE)
        return result

    def _get_raster_value(self, layer, lon, lat):
        path = layer["file"]
        if layer.get("type", "shp_index") == "shp_index":

            with Collection(path) as collection:
                tiles = [e for e in collection.filter(mask={
                    "type": "Point",
                    "coordinates": [lon, lat],
                })]

            if len(tiles) == 0:
                return None

            path = os.path.join(
                os.path.dirname(layer["file"]),
                tiles[0]["properties"]["location"],
            )

        dataset, band = self._get_raster(path)

        index = dataset.index(lon, lat)
        result = band[index[0] - 1][index[1] - 1]

        if "round" in layer:
            result = self._round(result, layer["round"])
        elif result is not None:
            result = Decimal(str(result))

        return result

    @staticmethod
    def _get_raster(path):
        if path not in _rasters.data:
            dataset = rasterio.open(path)
            band = dataset.read(1)  # pylint: disable=no-member
            _rasters.put(path, (dataset, band))
            log.debug('raster cache miss for %s' % path)
        else:
            log.debug('raster cache hit for %s' % path)
        return _rasters.get(path)

    @staticmethod
    def _round(value, round_to):
        if value is not None:
            return Decimal(str(value)).quantize(Decimal(str(round_to)))
        else:
            return None
