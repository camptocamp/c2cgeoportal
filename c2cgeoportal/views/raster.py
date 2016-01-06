# -*- coding: utf-8 -*-

# Copyright (c) 2012-2016, Camptocamp SA
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
from decimal import Decimal

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPInternalServerError, HTTPNotFound

from c2cgeoportal.lib.raster.georaster import GeoRaster
from c2cgeoportal.lib.caching import set_common_headers, NO_CACHE

log = logging.getLogger(__name__)


class Raster(object):

    # cache of GeoRaster instances in function of the layer name
    _rasters = {}

    def __init__(self, request):
        self.request = request
        self.rasters = self.request.registry.settings["raster"]

    @view_config(route_name="raster", renderer="decimaljson")
    def raster(self):
        lon = float(self.request.params["lon"])
        lat = float(self.request.params["lat"])
        if "layers" in self.request.params:
            rasters = {}
            layers = self.request.params["layers"].split(",")
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

        set_common_headers(
            self.request, "raster", NO_CACHE
        )
        return result

    def _get_raster_value(self, layer, ref, lon, lat):
        if ref in self._rasters:
            raster = self._rasters[ref]
        elif "type" not in layer or layer["type"] == "shp_index":
            raster = GeoRaster(layer["file"])
            self._rasters[ref] = raster
        else:
            raise HTTPInternalServerError(
                'Bad raster type "%s" for raster layer "%s"'
                % (layer["type"], ref))  # pragma: no cover

        result = raster.get_value(lon, lat)
        if "round" in layer:
            result = self._round(result, layer["round"])
        elif result is not None:
            result = Decimal(str(result))

        return result

    def _round(self, value, round_to):
        if value is not None:
            return Decimal(str(value)).quantize(Decimal(str(round_to)))
        else:
            return None
