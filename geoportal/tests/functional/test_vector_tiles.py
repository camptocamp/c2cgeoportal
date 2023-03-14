# Copyright (c) 2021-2023, Camptocamp SA
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

# pylint: disable=missing-docstring,attribute-defined-outside-init,protected-access

import mapbox_vector_tile
import pytest
from geoalchemy2 import WKTElement
from pyramid.httpexceptions import HTTPNotFound
from tests.functional.geodata_model import PointTest


@pytest.fixture
def test_data(dbsession, transact):
    from c2cgeoportal_commons.models.main import LayerVectorTiles

    del transact

    points = {
        "p1": PointTest(
            geom=WKTElement("POINT(599910 199955)", srid=21781), name="foo", city="Lausanne", country="Swiss"
        ),
        "p2": PointTest(
            geom=WKTElement("POINT(599910 200045)", srid=21781), name="bar", city="Chambéry", country="France"
        ),
        "p3": PointTest(
            geom=WKTElement("POINT(600090 200045)", srid=21781), name="éàè", city="Paris", country="France"
        ),
        "p4": PointTest(
            geom=WKTElement("POINT(600090 199955)", srid=21781), name="123", city="Londre", country="UK"
        ),
    }
    dbsession.add_all(points.values())

    layers = {
        "layer_vector_tiles": LayerVectorTiles(
            name="layer_vector_tiles",
            style="https://example.com/style.json",
            sql="""
            SELECT ST_AsMVT(q, 'mvt_routes') FROM (
            SELECT
                name,
                city,
                country,
                ST_AsMVTGeom("geom", {envelope}) as geom
                FROM geodata.testpoint
                WHERE ST_Intersects("geom", {envelope})
            ) AS q
            """,
        )
    }
    dbsession.add_all(layers.values())

    dbsession.flush()

    yield {
        "layers": layers,
        "points": points,
    }


class TestVectorTilesViews:
    def test_vector_tiles_success(self, dummy_request, test_data):
        from c2cgeoportal_geoportal.views.vector_tiles import VectorTilesViews

        request = dummy_request
        request.matchdict["layer_name"] = test_data["layers"]["layer_vector_tiles"].name
        request.matchdict["z"] = 11
        request.matchdict["x"] = 0
        request.matchdict["y"] = 0

        resp = VectorTilesViews(request).vector_tiles()

        # assert False
        assert isinstance(resp.body, bytes)

        data = mapbox_vector_tile.decode(resp.body)
        assert data["mvt_routes"]["features"][0]["properties"]["city"] == test_data["points"]["p1"].city

    def test_vector_tiles_layer_not_found(self, dummy_request, test_data):
        from c2cgeoportal_geoportal.views.vector_tiles import VectorTilesViews

        request = dummy_request
        request.matchdict["layer_name"] = "not_existing_layer_name"
        request.matchdict["z"] = 11
        request.matchdict["x"] = 0
        request.matchdict["y"] = 0

        with pytest.raises(HTTPNotFound) as excinfo:
            VectorTilesViews(request).vector_tiles()
        assert "Not found any vector tile layer named not_existing_layer_name"
