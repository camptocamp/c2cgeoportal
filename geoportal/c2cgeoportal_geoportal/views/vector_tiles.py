# Copyright (c) 2021-2024, Camptocamp SA
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

import sqlalchemy
from pyramid.httpexceptions import HTTPNotFound
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_config
from tilecloud import TileCoord
from tilecloud.grid.free import FreeTileGrid

from c2cgeoportal_commons.models import DBSession, main
from c2cgeoportal_geoportal.lib.common_headers import Cache, set_common_headers

_LOG = logging.getLogger(__name__)


class VectorTilesViews:
    """All the views concerning the vector tiles."""

    def __init__(self, request: Request) -> None:
        self.request = request

    @view_config(route_name="vector_tiles")  # type: ignore[misc]
    def vector_tiles(self) -> Response:
        assert DBSession is not None

        settings = self.request.registry.settings["vector_tiles"]
        grid = FreeTileGrid(settings["resolutions"], max_extent=settings["extent"], tile_size=256)

        layer_name = self.request.matchdict["layer_name"]

        z = int(self.request.matchdict["z"])
        x = int(self.request.matchdict["x"])
        y = int(self.request.matchdict["y"])
        coord = TileCoord(z, x, y)
        minx, miny, maxx, maxy = grid.extent(coord, 0)

        layer = (
            DBSession.query(main.LayerVectorTiles.sql)
            .filter(main.LayerVectorTiles.name == layer_name)
            .one_or_none()
        )
        if layer is None:
            raise HTTPNotFound(f"Not found any vector tile layer named {layer_name}")

        raw_sql = layer[0].format(
            envelope=f"ST_MakeEnvelope({minx}, {miny}, {maxx}, {maxy}, {settings['srid']})"
        )

        result = DBSession.execute(sqlalchemy.text(raw_sql))
        for row in result:  # pylint: disable=not-an-iterable
            set_common_headers(self.request, "vector_tiles", Cache.PUBLIC)
            response = self.request.response
            response.content_type = "application/vnd.mapbox-vector-tile"
            response.body = row[0].tobytes()
            return response
