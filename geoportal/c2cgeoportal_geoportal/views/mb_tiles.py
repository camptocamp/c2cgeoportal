# Copyright (c) 2021, Camptocamp SA
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

from pyramid.request import Request
from pyramid.response import Response
from tilecloud import TileCoord
from tilecloud.grid.free import FreeTileGrid

from c2cgeoportal_commons.models import DBSession, main

LOG = logging.getLogger(__name__)


class MbTilesViews:
    def __init__(self, request: Request) -> None:
        self.request = request

    def mb_tiles(self) -> Response:

        settings = self.request.registry.settings["vectortile"]
        grid = FreeTileGrid(settings["resolutions"], max_extent=settings["extent"], tile_size=256)

        layerid = self.request.matchdict["layerid"]
        z = int(self.request.matchdict["z"])
        x = int(self.request.matchdict["x"])
        y = int(self.request.matchdict["y"])
        coord = TileCoord(z, x, y)
        minx, miny, maxx, maxy = grid.extent(coord, 0)

        LOG.warning(layerid)
        result = DBSession.query(main.LayerVectorTiles.id).all()
        for r in result:
            LOG.warning(r)
        sql = DBSession.query(main.LayerVectorTiles.sql).filter(main.LayerVectorTiles.id == layerid).one()[0]

        raw_sql = sql.format(envelope=f"{minx}, {miny}, {maxx}, {maxy}")

        result = DBSession.execute(raw_sql)

        response = self.request.response
        response.content_type = "application/x-protobuf"
        for row in result:
            response.body = row[0].tobytes()
            response.conditional_response = True
            response.md5_etag()
            return response
