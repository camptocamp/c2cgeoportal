# Copyright (c) 2011-2025, Camptocamp SA
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


import pyramid.request
from c2cgeoportal_commons.models import DBSession
from geoalchemy2.shape import from_shape, to_shape
from geojson import loads
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.view import view_config
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry
from sqlalchemy import func


class GeometryProcessing:
    """
    View used to provide processing on a geometry.

    Currently only difference between geometries.
    """

    def __init__(self, request: pyramid.request.Request) -> None:
        self.request = request

    @view_config(route_name="difference", renderer="geojson")  # type: ignore[misc]
    def difference(self) -> BaseGeometry | None:
        assert DBSession is not None

        body = loads(self.request.body)
        if (
            "geometries" not in body
            or not isinstance(body["geometries"], list)
            or len(body["geometries"]) != 2
        ):
            raise HTTPBadRequest(
                """Wrong body, it should be like that:
            {
                "geometries": [geomA, geomB]
            }
            """,
            )

        return to_shape(
            DBSession.query(
                func.ST_Difference(
                    from_shape(shape(body["geometries"][0])),
                    from_shape(shape(body["geometries"][1])),
                ),
            ).scalar(),
        )
