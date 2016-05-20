# -*- coding: utf-8 -*-

# Copyright (c) 2011-2016, Camptocamp SA
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

from c2cgeoportal.lib.filter_capabilities import get_protected_layers, \
    get_private_layers

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPForbidden, HTTPInternalServerError

from c2cgeoportal.lib.caching import NO_CACHE
from c2cgeoportal.views.proxy import Proxy

log = logging.getLogger(__name__)


class PdfReport(Proxy):  # pragma: no cover

    def __init__(self, request):
        Proxy.__init__(self, request)
        self.config = self.request.registry.settings.get("pdfreport", {})

    def _do_print(self, spec):
        """ Create and get report PDF. """

        headers = dict(self.request.headers)
        headers["Content-Type"] = "application/json"
        resp, content = self._proxy(
            "%s/buildreport.pdf" % (
                self.config["print_url"],
            ),
            method="POST",
            body=dumps(spec),
            headers=headers
        )

        return self._build_response(
            resp, content, NO_CACHE, "pdfreport",
        )

    def _get_config(self, name, default=None):
        config = self.layer_config.get(name)
        if config is None:
            config = self.config. \
                get("defaults", {}). \
                get(name, default)
        return config

    def _get_map_config(self, name, map_config, default=None):
        config = map_config.get(name)
        if config is None:
            config = self.config. \
                get("defaults", {}). \
                get("map", {}). \
                get(name, default)
        return config

    def _build_map(self, mapserv_url, vector_request_url, srs, map_config):
        backgroundlayers = self._get_map_config("backgroundlayers", map_config, [])
        imageformat = self._get_map_config("imageformat", map_config, "image/png")
        return {
            "projection": srs,
            "dpi": 254,
            "rotation": 0,
            "bbox": [0, 0, 1000000, 1000000],
            "zoomToFeatures": {
                "zoomType": self._get_map_config("zoomType", map_config, "extent"),
                "layer": "vector",
                "minScale": self._get_map_config("minScale", map_config, 1000),
            },
            "layers": [{
                "type": "gml",
                "name": "vector",
                "style": {
                    "version": "2",
                    "[1 > 0]": self._get_map_config("style", map_config, {
                        "fillColor": "red",
                        "fillOpacity": 0.2,
                        "symbolizers": [{
                            "strokeColor": "red",
                            "strokeWidth": 1,
                            "type": "point",
                            "pointRadius": 10
                        }]
                    })
                },
                "opacity": 1,
                "url": vector_request_url
            }, {
                "baseURL": mapserv_url,
                "opacity": 1,
                "type": "WMS",
                "serverType": "mapserver",
                "layers": backgroundlayers,
                "imageFormat": imageformat
            }]
        }

    @view_config(route_name="pdfreport", renderer="json")
    def get_report(self):
        id = self.request.matchdict["id"]
        self.layername = self.request.matchdict["layername"]
        self.layer_config = self.config.get("layers", {}).get(self.layername, {})

        if self._get_config("check_credentials", True):
            # check user credentials
            role_id = None if self.request.user is None else \
                self.request.user.role.id

            # FIXME: support of mapserver groups
            if self.layername in get_private_layers() and \
                    self.layername not in get_protected_layers(role_id):
                raise HTTPForbidden

        srs = self._get_config("srs")
        if srs is None:
            raise HTTPInternalServerError(
                "Missing 'srs' in service configuration"
            )

        mapserv_url = self.request.route_url("mapserverproxy")
        vector_request_url = "%s?%s" % (
            mapserv_url,
            "&".join(["%s=%s" % i for i in {
                "service": "WFS",
                "version": "1.1.0",
                "outputformat": "gml3",
                "request": "GetFeature",
                "typeName": self.layername,
                "featureid": self.layername + "." + id,
                "srsName": "epsg:" + str(srs)
            }.items()])
        )

        spec = self._get_config("spec")
        if spec is None:
            spec = {
                "layout": self.layername,
                "outputFormat": "pdf",
                "attributes": {
                    "paramID": id
                }
            }
            map_config = self.layer_config.get("map")
            if map_config is not None:
                spec["attributes"]["map"] = self._build_map(
                    mapserv_url, vector_request_url, srs, map_config
                )

            maps_config = self.layer_config.get("maps")
            if maps_config is not None:
                spec["attributes"]["maps"] = []
                for map_config in maps_config:
                    spec["attributes"]["maps"].append(self._build_map(
                        mapserv_url, vector_request_url, srs, map_config
                    ))
        else:
            spec = loads(dumps(spec) % {
                "layername": self.layername,
                "id": id,
                "srs": srs,
                "mapserv_url": mapserv_url,
                "vector_request_url": vector_request_url,
            })

        return self._do_print(spec)
