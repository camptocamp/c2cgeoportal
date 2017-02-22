# -*- coding: utf-8 -*-

# Copyright (c) 2012-2017, Camptocamp SA
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


import shputils
from os.path import dirname
from struct import unpack


class Tile:
    def __init__(self, min_x, min_y, max_x, max_y, filename):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
        self.filename = filename

    def contains(self, x, y):
        return self.min_x <= x < self.max_x and self.min_y <= y < self.max_y

    def __str__(self):
        return "{0:f}, {1:f}, {2:f}, {3:f}: {4!s}".format(
            self.min_x, self.min_y, self.max_x, self.max_y, self.filename
        )


class BTTile(Tile):
    def get_value(self, x, y):
        file = open(self.filename, "rb")
        if not hasattr(self, "cols"):
            file.seek(10)
            (self.cols, self.rows, self.dataSize, self.floatingPoint) = \
                unpack("<LLhh", file.read(12))
            self.resolution_x = (self.max_x - self.min_x) / self.cols
            self.resolution_y = (self.max_y - self.min_y) / self.rows

        pos_x = int((x - self.min_x) / self.resolution_x)
        pos_y = int((y - self.min_y) / self.resolution_y)
        file.seek(256 + (pos_y + pos_x * self.rows) * self.dataSize)

        if self.floatingPoint == 1:
            val = unpack("<f", file.read(self.dataSize))[0]
        else:
            if self.dataSize == 2:
                format_ = "<h"
            else:
                format_ = "<l"
            data = file.read(self.dataSize)
            val = unpack(format_, data)[0]

        file.close()
        return val


class GeoRaster:
    def __init__(self, shapefile_name):
        self.tiles = []
        shp_records = shputils.load_shapefile(shapefile_name)
        dir_ = dirname(shapefile_name)
        if dir_ == "":
            dir_ = "."
        for shape in shp_records:
            filename = shape["dbf_data"]["location"].rstrip()
            tile_class = None
            if filename.endswith(".bt"):
                tile_class = BTTile
            if not filename.startswith("/"):
                filename = dir_ + "/" + filename
            geo = shape["shp_data"]
            tile = tile_class(geo["xmin"], geo["ymin"], geo["xmax"], geo["ymax"], filename)
            self.tiles.append(tile)

    def get_value(self, x, y):
        tile = self._get_tile(x, y)
        if tile:
            return tile.get_value(x, y)
        else:
            return None

    def _get_tile(self, x, y):
        for cur in self.tiles:
            if cur.contains(x, y):
                return cur
        return None
