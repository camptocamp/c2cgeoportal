# -*- coding: utf-8-*-

import shputils
from os.path import dirname
from struct import unpack


class Tile(object):
    def __init__(self, min_x, min_y, max_x, max_y, filename):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
        self.filename = filename

    def contains(self, x, y):
        return self.min_x <= x and self.max_x > x and self.min_y <= y and self.max_y > y

    def __str__(self):
        return "%f, %f, %f, %f: %s" % (
            self.min_x, self.min_y, self.max_x, self.max_y, self.filename
        )


class BTTile(Tile):
    def get_value(self, x, y):
        file = open(self.filename, 'rb')
        if not hasattr(self, 'cols'):
            file.seek(10)
            (self.cols, self.rows, self.dataSize, self.floatingPoint) = \
                unpack('<LLhh', file.read(12))
            self.resolution_x = (self.max_x - self.min_x) / self.cols
            self.resolution_y = (self.max_y - self.min_y) / self.rows

        pos_x = int((x - self.min_x) / self.resolution_x)
        pos_y = int((y - self.min_y) / self.resolution_y)
        file.seek(256 + (pos_y + pos_x * self.rows) * self.dataSize)

        if self.floatingPoint == 1:
            val = unpack("<f", file.read(self.dataSize))[0]
        else:
            if self.dataSize == 2:
                format = "<h"
            else:
                format = "<l"
            data = file.read(self.dataSize)
            val = unpack(format, data)[0]

        file.close()
        return val


class GeoRaster:
    def __init__(self, shapefile_name):
        self.tiles = []
        shp_records = shputils.load_shapefile(shapefile_name)
        dir = dirname(shapefile_name)
        if dir == "":
            dir = "."
        for shape in shp_records:
            filename = shape['dbf_data']['location'].rstrip()
            tile_class = None
            if filename.endswith(".bt"):
                tile_class = BTTile
            if not filename.startswith("/"):
                filename = dir + '/' + filename
            geo = shape['shp_data']
            tile = tile_class(geo['xmin'], geo['ymin'], geo['xmax'], geo['ymax'], filename)
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
