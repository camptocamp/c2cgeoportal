# -*- coding: utf-8 -*-

# Copyright (c) 2012-2019, Camptocamp SA
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


from decimal import Decimal
import logging
import math
import os
from typing import Any, Dict  # noqa, pylint: disable=unused-import

from pyramid.httpexceptions import HTTPBadRequest, HTTPNotFound
from pyramid.view import view_config
import zope.event.classhandler

from c2cgeoportal_commons.models import InvalidateCacheEvent
from c2cgeoportal_geoportal.lib.caching import NO_CACHE, set_common_headers

LOG = logging.getLogger(__name__)


class Raster:
    data: Dict[str, Any] = {}

    def __init__(self, request):
        self.request = request
        self.rasters = self.request.registry.settings["raster"]

        @zope.event.classhandler.handler(InvalidateCacheEvent)
        def handle(event: InvalidateCacheEvent):  # pylint: disable=unused-variable
            del event
            for _, v in Raster.data.items():
                v.close()
            Raster.data = {}

    def _get_required_finite_float_param(self, name: str) -> float:
        if name not in self.request.params:
            raise HTTPBadRequest("'{}' should be in the query string parameters".format(name))
        try:
            result = float(self.request.params[name])
        except ValueError:
            raise HTTPBadRequest(
                "'{}' ({}) parameters should be a number".format(name, self.request.params[name])
            )
        if not math.isfinite(result):
            raise HTTPBadRequest(
                "'{}' ({}) parameters should be a finite number".format(name, self.request.params[name])
            )
        return result

    @view_config(route_name="raster", renderer="fast_json")
    def raster(self):
        lon = self._get_required_finite_float_param("lon")
        lat = self._get_required_finite_float_param("lat")

        if "layers" in self.request.params:
            rasters = {}
            layers = self.request.params["layers"].split(",")
            for layer in layers:
                if layer in self.rasters:
                    rasters[layer] = self.rasters[layer]
                else:
                    raise HTTPNotFound("Layer {} not found".format(layer))
        else:
            rasters = self.rasters

        result = {}
        for ref in list(rasters.keys()):
            result[ref] = self._get_raster_value(rasters[ref], ref, lon, lat)

        set_common_headers(self.request, "raster", NO_CACHE)
        return result

    def _get_data(self, layer, name):
        if name not in self.data:
            path = layer["file"]
            if layer.get("type", "shp_index") == "shp_index":
                # Avoid loading if not needed
                from fiona.collection import Collection  # pylint: disable=import-outside-toplevel

                self.data[name] = Collection(path)
            elif layer.get("type") == "gdal":
                # Avoid loading if not needed
                import rasterio  # pylint: disable=import-outside-toplevel

                self.data[name] = rasterio.open(path)

        return self.data[name]

    def _get_raster_value(self, layer, name, lon, lat):
        data = self._get_data(layer, name)
        type_ = layer.get("type", "shp_index")
        if type_ == "shp_index":
            tiles = list(data.filter(mask={"type": "Point", "coordinates": [lon, lat]}))

            if not tiles:
                return None

            path = os.path.join(os.path.dirname(layer["file"]), tiles[0]["properties"]["location"])

            # Avoid loading if not needed
            import rasterio  # pylint: disable=import-outside-toplevel

            with rasterio.open(path) as dataset:
                result = self._get_value(layer, name, dataset, lon, lat)
        elif type_ == "gdal":
            result = self._get_value(layer, name, data, lon, lat)
        else:
            raise ValueError("Unsupported type " + type_)

        if "round" in layer:
            result = self._round(result, layer["round"])
        elif result is not None:
            result = Decimal(str(result))

        return result

    @staticmethod
    def _get_value(layer, name, dataset, lon, lat):
        index = dataset.index(lon, lat)

        shape = dataset.shape
        if 0 <= index[0] < shape[0] and 0 <= index[1] < shape[1]:

            def get_index(index_):
                return index_, index_ + 1

            result = dataset.read(1, window=(get_index(index[0]), get_index(index[1])))[0][0]
            result = None if result == layer.get("nodata", dataset.nodata) else result
        else:
            LOG.debug(
                "Out of index for layer: %s (%s), " "lon/lat: %dx%d, index: %dx%d, shape: %dx%d.",
                name,
                layer["file"],
                lon,
                lat,
                index[0],
                index[1],
                dataset.shape[0],
                dataset.shape[1],
            )
            result = None

        return result

    @staticmethod
    def _round(value, round_to):
        if value is not None:
            return Decimal(str(value)).quantize(Decimal(str(round_to)))
        return None
