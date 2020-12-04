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


import logging
from io import StringIO
from typing import Set, cast  # noqa, pylint: disable=unused-import

import requests
from defusedxml import ElementTree

from c2cgeoportal_commons.lib.url import add_url_params, get_url2
from c2cgeoportal_commons.models import main


class dry_run_transaction:  # noqa N801: class names should use CapWords convention
    def __init__(self, dbsession, dry_run):
        self.dbsession = dbsession
        self.dry_run = dry_run

    def __enter__(self):
        if self.dry_run:
            self.dbsession.begin_nested()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.dry_run:
            self.dbsession.rollback()


class OGCServerSynchronizer:
    def __init__(self, request, ogc_server):
        self._request = request
        self._ogc_server = ogc_server
        self._default_wms = main.LayerWMS()
        self._interfaces = None

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

    def check_layers(self):
        capabilities = ElementTree.fromstring(self.wms_capabilities())
        layers = self._request.dbsession.query(main.LayerWMS).filter(
            main.LayerWMS.ogc_server == self._ogc_server
        )
        items = 0
        invalids = 0
        for layer in layers:
            valid = True
            reason = None
            for name in layer.layer.split(","):
                el = capabilities.find(".//Layer[Name='{}']".format(name))
                if el is None:
                    valid = False
                    reason = "Layer {} does not exists on OGC server".format(name)
                    self._logger.info(reason)
                    break
                if layer.style and el.find("./Style/Name[.='{}']".format(layer.style)) is None:
                    valid = False
                    reason = "Style {} does not exists in Layer {}".format(layer.style, name)
                    self._logger.info(reason)
                    break
            layer.valid = valid
            if not valid:
                invalids += 1
            layer.invalid_reason = reason
            items += 1
        self._logger.info("Checked %s layers, %s are invalid", items, invalids)

    def synchronize(self, dry_run=False):
        with dry_run_transaction(self._request.dbsession, dry_run):
            self.do_synchronize()
            if dry_run:
                self._logger.info("Rolling back transaction due to dry run")

    def do_synchronize(self):
        self._items_found = 0
        self._themes_added = 0
        self._groups_added = 0
        self._layers_added = 0

        self._default_wms = cast(
            main.LayerWMS, main.LayerWMS.get_default(self._request.dbsession) or main.LayerWMS()
        )
        self._interfaces = self._request.dbsession.query(main.Interface).all()

        capabilities = ElementTree.fromstring(self.wms_capabilities())
        theme_layers = capabilities.findall("Capability/Layer/Layer")
        for theme_layer in theme_layers:
            self.synchronize_layer(theme_layer)

        self._logger.info("%s items were found", self._items_found)
        self._logger.info("%s themes were added", self._themes_added)
        self._logger.info("%s groups were added", self._groups_added)
        self._logger.info("%s layers were added", self._layers_added)

    def synchronize_layer(self, el, parent=None):
        if el.find("Layer") is None:
            tree_item = self.get_layer_wms(el, parent)
        elif parent is None:
            tree_item = self.get_theme(el)
        else:
            tree_item = self.get_layer_group(el, parent)

        for child in el.findall("Layer"):
            self.synchronize_layer(child, tree_item)

    def get_theme(self, el):
        name = el.find("Name").text

        theme = self._request.dbsession.query(main.Theme).filter(main.Theme.name == name).one_or_none()

        if theme is None:
            theme = main.Theme()
            theme.name = name
            theme.public = False
            theme.interfaces = self._interfaces

            self._request.dbsession.add(theme)
            self._logger.info("Layer %s added as new theme", name)
            self._themes_added += 1
        else:
            self._items_found += 1

        return theme

    def get_layer_group(self, el, parent):
        name = el.find("Name").text

        group = (
            self._request.dbsession.query(main.LayerGroup).filter(main.LayerGroup.name == name).one_or_none()
        )

        if group is None:
            group = main.LayerGroup(name=el.find("Name").text)
            group.parents_relation.append(main.LayergroupTreeitem(group=parent))  # noqa, pylint: no-member

            self._request.dbsession.add(group)
            self._logger.info("Layer %s added as new group in theme %s", name, parent.name)
            self._groups_added += 1
        else:
            self._items_found += 1

        return group

    def get_layer_wms(self, el, parent):
        name = el.find("Name").text

        layer = self._request.dbsession.query(main.LayerWMS).filter(main.LayerWMS.name == name).one_or_none()

        if layer is None:
            layer = main.LayerWMS()

            # TreeItem
            layer.name = el.find("Name").text
            layer.description = self._default_wms.description
            layer.metadatas = [main.Metadata(name=m.name, value=m.value) for m in self._default_wms.metadatas]

            # Layer
            layer.public = False
            layer.geo_table = None
            layer.exclude_properties = self._default_wms.exclude_properties
            layer.interfaces = list(self._default_wms.interfaces) or self._interfaces

            # DimensionLayer
            layer.dimensions = [
                main.Dimension(
                    name=d.name,
                    value=d.value,
                    field=d.field,
                    description=d.description,
                )
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

            self._request.dbsession.add(layer)
            if parent is None or isinstance(parent, main.Theme):
                self._logger.info("Layer %s added as new layer with no parent", name)
            else:
                layer.parents_relation.append(main.LayergroupTreeitem(group=parent))
                self._logger.info("Layer %s added as new layer in group %s", name, parent.name)
            self._layers_added += 1

        else:
            self._items_found += 1
            if layer.ogc_server is not self._ogc_server:
                self._logger.info(
                    "Layer %s: another layer already exists with the same name in OGC server %s",
                    name,
                    self._ogc_server.name,
                )

        return layer

    def wms_capabilities(self):
        errors: Set[str] = set()
        url = get_url2(
            "The OGC server '{}'".format(self._ogc_server.name),
            self._ogc_server.url,
            self._request,
            errors,
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
