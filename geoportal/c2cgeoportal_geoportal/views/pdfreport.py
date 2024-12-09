# Copyright (c) 2011-2024, Camptocamp SA
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
from json import dumps, loads
from typing import Any

import pyramid.request
import pyramid.response
from pyramid.httpexceptions import HTTPBadRequest, HTTPForbidden
from pyramid.view import view_config

from c2cgeoportal_commons import models
from c2cgeoportal_commons.lib.url import Url
from c2cgeoportal_commons.models import main
from c2cgeoportal_geoportal.lib.common_headers import Cache
from c2cgeoportal_geoportal.lib.layers import get_private_layers, get_protected_layers
from c2cgeoportal_geoportal.views.ogcproxy import OGCProxy

_LOG = logging.getLogger(__name__)


class PdfReport(OGCProxy):
    """All the views concerned the PDF report."""

    layername = None

    def __init__(self, request: pyramid.request.Request):
        OGCProxy.__init__(self, request)
        self.config = self.request.registry.settings.get("pdfreport", {})

    def _do_print(self, spec: dict[str, Any]) -> pyramid.response.Response:
        """Create and get report PDF."""
        headers = dict(self.request.headers)
        headers["Content-Type"] = "application/json"
        response = self._proxy(
            Url(f"{self.config['print_url']}/buildreport.{spec['outputFormat']}"),
            method="POST",
            body=dumps(spec).encode("utf-8"),
            headers=headers,
        )

        return self._build_response(response, response.content, Cache.PRIVATE_NO, "pdfreport")

    @staticmethod
    def _build_map(
        mapserv_url: str, vector_request_url: str, srs: str, map_config: dict[str, Any]
    ) -> dict[str, Any]:
        backgroundlayers = map_config["backgroundlayers"]
        imageformat = map_config["imageformat"]
        return {
            "projection": srs,
            "dpi": 254,
            "rotation": 0,
            "bbox": [0, 0, 1000000, 1000000],
            "zoomToFeatures": {
                "zoomType": map_config["zoomType"],
                "layer": "vector",
                "minScale": map_config["minScale"],
            },
            "layers": [
                {
                    "type": "gml",
                    "name": "vector",
                    "style": {"version": "2", "[1 > 0]": map_config["style"]},
                    "opacity": 1,
                    "url": vector_request_url,
                },
                {
                    "baseURL": mapserv_url,
                    "opacity": 1,
                    "type": "WMS",
                    "serverType": "mapserver",
                    "layers": backgroundlayers,
                    "imageFormat": imageformat,
                },
            ],
        }

    @view_config(route_name="pdfreport", renderer="json")  # type: ignore[misc]
    def get_report(self) -> pyramid.response.Response:
        assert models.DBSession is not None

        self.layername = self.request.matchdict["layername"]
        layer_config = self.config["layers"].get(self.layername)

        if layer_config is None:
            raise HTTPBadRequest("Layer not found: " + self.layername)

        multiple = layer_config.get("multiple", False)
        ids = self.request.matchdict["ids"]
        if multiple:
            ids = ids.split(",")

        features_ids = (
            [self.layername + "." + id_ for id_ in ids] if multiple else [self.layername + "." + ids]
        )

        if layer_config["check_credentials"]:
            # FIXME: support of mapserver groups
            ogc_server = (
                models.DBSession.query(main.OGCServer)
                .filter(main.OGCServer.name == layer_config["ogc_server"])
                .one()
            )
            ogc_server_ids = [ogc_server]

            private_layers_object = get_private_layers(ogc_server_ids)
            private_layers_names = [private_layers_object[oid].name for oid in private_layers_object]

            protected_layers_object = get_protected_layers(self.request.user, ogc_server_ids)
            protected_layers_names = [protected_layers_object[oid].name for oid in protected_layers_object]

            if self.layername in private_layers_names and self.layername not in protected_layers_names:
                raise HTTPForbidden

        srs = layer_config["srs"]

        mapserv_url = self.request.route_url(
            "mapserverproxy", _query={"ogcserver": layer_config["ogc_server"]}
        )
        url = Url(mapserv_url)
        url.add_query(
            {
                "service": "WFS",
                "version": "1.1.0",
                "outputformat": "gml3",
                "request": "GetFeature",
                "typeName": self.layername,
                "featureid": ",".join(features_ids),
                "srsName": srs,
            }
        )
        vector_request_url = url.url()

        spec = layer_config["spec"]
        if spec is None:
            spec = {
                "layout": self.layername,
                "outputFormat": "pdf",
                "attributes": {"ids": [{"id": id_} for id_ in ids]} if multiple else {"id": id},
            }
            map_config = layer_config.get("map")
            if map_config is not None:
                spec["attributes"]["map"] = self._build_map(mapserv_url, vector_request_url, srs, map_config)

            maps_config = layer_config.get("maps")
            if maps_config is not None:
                spec["attributes"]["maps"] = []
                for map_config in maps_config:
                    spec["attributes"]["maps"].append(
                        self._build_map(mapserv_url, vector_request_url, srs, map_config)
                    )
        else:
            datasource = layer_config.get("datasource", True)
            if multiple and datasource:
                data = dumps(layer_config["data"])
                data_list = [
                    loads(
                        data
                        % {
                            "layername": self.layername,
                            "id": id_,
                            "srs": srs,
                            "mapserv_url": mapserv_url,
                            "vector_request_url": vector_request_url,
                        }
                    )
                    for id_ in ids
                ]
                self.walker(spec, "%(datasource)s", data_list)
                spec = loads(
                    dumps(spec)
                    % {
                        "layername": self.layername,
                        "srs": srs,
                        "mapserv_url": mapserv_url,
                        "vector_request_url": vector_request_url,
                    }
                )
            elif multiple:
                spec = loads(
                    dumps(spec)
                    % {
                        "layername": self.layername,
                        "ids": ",".join(ids),
                        "srs": srs,
                        "mapserv_url": mapserv_url,
                        "vector_request_url": vector_request_url,
                    }
                )
            else:
                spec = loads(
                    dumps(spec)
                    % {
                        "layername": self.layername,
                        "id": ids,
                        "srs": srs,
                        "mapserv_url": mapserv_url,
                        "vector_request_url": vector_request_url,
                    }
                )

        return self._do_print(spec)

    def walker(self, spec: dict[str, Any] | list[dict[str, Any]], name: str, value: Any) -> None:
        if isinstance(spec, dict):
            for k, v in spec.items():
                if isinstance(v, str):
                    if v == name:
                        spec[k] = value
                else:
                    self.walker(v, name, value)

        if isinstance(spec, list):
            for k2, v2 in enumerate(spec):
                if isinstance(v2, str):
                    if v2 == name:
                        spec[k2] = value
                else:
                    self.walker(v2, name, value)
