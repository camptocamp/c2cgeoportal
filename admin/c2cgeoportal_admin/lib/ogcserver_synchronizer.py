# -*- coding: utf-8 -*-

# Copyright (c) 2020, Camptocamp SA
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


from io import StringIO
import logging
from typing import Optional, Set, Type  # noqa, pylint: disable=unused-import

from defusedxml import ElementTree
import requests

from c2cgeoportal_commons.lib.url import add_url_params, get_url2
from c2cgeoportal_commons.models import main


class OGCServerSynchronizer:
    def __init__(self, request, ogc_server):
        self._request = request
        self._ogc_server = ogc_server
        self._default_wms = main.LayerWMS.get_default(request.dbsession) or main.LayerWMS()
        self._logger = logging.Logger(str(self), logging.INFO)

        self._log = StringIO()
        self._log_handler = logging.StreamHandler(self._log)
        self._logger.addHandler(self._log_handler)

        self._items_found = 0
        self._themes_added = 0
        self._groups_added = 0
        self._layers_added = 0

    def __str__(self):
        return "OGCServerSynchronizer({})".format(self._ogc_server.name)

    def logger(self):
        return self._logger

    def report(self):
        return self._log.getvalue()

    def synchronize(self):
        self._items_found = 0
        self._themes_added = 0
        self._groups_added = 0
        self._layers_added = 0

        capabilities = ElementTree.fromstring(self.wms_capabilities())
        theme_layers = capabilities.findall("Capability/Layer/Layer")
        for theme_layer in theme_layers:
            self.synchronize_layer(theme_layer)

        self._logger.info("%s items were found", self._items_found)
        self._logger.info("%s themes were added", self._themes_added)
        self._logger.info("%s groups were added", self._groups_added)
        self._logger.info("%s layers were added", self._layers_added)

    def synchronize_layer(self, el, parent=None):
        name = el.find("Name").text

        class_: Optional[Type[main.TreeItem]] = None
        if el.find("Layer") is None:
            class_ = main.LayerWMS
        elif parent is None:
            class_ = main.Theme
        else:
            class_ = main.LayerGroup

        tree_item = self._request.dbsession.query(class_).filter(class_.name == name).one_or_none()
        if tree_item is not None:
            self._items_found += 1
        else:
            if class_ == main.Theme:
                tree_item = self.create_theme(el)
                self._logger.info("Layer %s added as new theme", name)
                self._themes_added += 1

            if class_ == main.LayerGroup:
                tree_item = self.creare_layer_group(el)
                tree_item.parents_relation.append(  # noqa, pylint: no-member
                    main.LayergroupTreeitem(group=parent)
                )
                self._logger.info("Layer %s added as new group in theme %s", name, parent.name)
                self._groups_added += 1

            if class_ == main.LayerWMS:
                tree_item = self.create_layer_wms(el)
                if parent is None or isinstance(parent, main.Theme):
                    self._logger.info("Layer %s added as new layer with no parent", name)
                else:
                    tree_item.parents_relation.append(main.LayergroupTreeitem(group=parent))
                    self._logger.info("Layer %s added as new layer in group %s", name, parent.name)
                self._layers_added += 1

            self._request.dbsession.add(tree_item)

        for child in el.findall("Layer"):
            self.synchronize_layer(child, tree_item)

    @staticmethod
    def create_theme(el):
        theme = main.Theme()
        theme.name = el.find("Name").text
        theme.public = False
        return theme

    @staticmethod
    def creare_layer_group(el):
        return main.LayerGroup(name=el.find("Name").text,)

    def create_layer_wms(self, el):
        layer = main.LayerWMS()

        # TreeItem
        layer.name = el.find("Name").text
        layer.description = self._default_wms.description
        layer.metadatas = [main.Metadata(name=m.name, value=m.value) for m in self._default_wms.metadatas]

        # Layer
        layer.public = False
        layer.geo_table = None
        layer.exclude_properties = self._default_wms.exclude_properties
        layer.interfaces = list(self._default_wms.interfaces)

        # DimensionLayer
        layer.dimensions = [
            main.Dimension(name=d.name, value=d.value, field=d.field, description=d.description,)
            for d in self._default_wms.dimensions
        ]

        # LayerWMS
        layer.ogc_server = self._ogc_server
        layer.layer = el.find("Name").text
        layer.style = (
            self._default_wms.style
            if el.find("./Style/Name[.='{}']".format(self._default_wms.style)) is not None
            else None
        )
        # layer.time_mode =
        # layer.time_widget =

        return layer

    def wms_capabilities(self):
        errors: Set[str] = set()
        url = get_url2(
            "The OGC server '{}'".format(self._ogc_server.name), self._ogc_server.url, self._request, errors,
        )
        if url is None:
            raise Exception("\n".join(errors))

        # Add functionality params
        # sparams = get_mapserver_substitution_params(self.request)
        # url = add_url_params(url, sparams)

        url = add_url_params(
            url,
            {
                "SERVICE": "WMS",
                "VERSION": "1.1.1",
                "REQUEST": "GetCapabilities",
                "ROLE_ID": "0",
                "USER_ID": "0",
            },
        )

        self._logger.info("Get WMS GetCapabilities from: %s", url)

        headers = {}

        # Add headers for Geoserver
        if self._ogc_server.auth == main.OGCSERVER_AUTH_GEOSERVER:
            headers["sec-username"] = "root"
            headers["sec-roles"] = "root"

        response = requests.get(url, headers=headers, timeout=300)
        self._logger.info("Got response %s in %.1fs.", response.status_code, response.elapsed.total_seconds())
        response.raise_for_status()

        # With WMS 1.3 it returns text/xml also in case of error :-(
        if response.headers.get("Content-Type", "").split(";")[0].strip() not in [
            "application/vnd.ogc.wms_xml",
            "text/xml",
        ]:
            raise Exception(
                "GetCapabilities from URL {} returns a wrong Content-Type: {}\n{}".format(
                    url, response.headers.get("Content-Type", ""), response.text
                )
            )

        return response.content
