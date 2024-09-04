# Copyright (c) 2020-2024, Camptocamp SA
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


import functools
import logging
from io import StringIO
from typing import Any, Optional, cast
from xml.etree.ElementTree import Element  # nosec

import pyramid.request
import requests
from defusedxml import ElementTree
from sqlalchemy.orm.session import Session

from c2cgeoportal_commons.lib.url import get_url2
from c2cgeoportal_commons.models import main


class dry_run_transaction:  # noqa ignore=N801: class names should use CapWords convention
    def __init__(self, dbsession: Session, dry_run: bool):
        self.dbsession = dbsession
        self.dry_run = dry_run

    def __enter__(self) -> None:
        if self.dry_run:
            self.dbsession.begin_nested()

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.dry_run:
            self.dbsession.rollback()


class OGCServerSynchronizer:
    """A processor which imports WMS Capabilities in layer tree."""

    def __init__(
        self,
        request: pyramid.request.Request,
        ogc_server: main.OGCServer,
        force_parents: bool = False,
        force_ordering: bool = False,
        clean: bool = False,
    ) -> None:
        """
        Initialize the Synchronizer.

        request
            The current pyramid request object. Used to retrieve the SQLAlchemy Session object,
            and to construct the capabilities URL.

        ogc_server
            The considered OGCServer from witch to import the capabilities.

        force_parents
            When set to True, overwrite parents of each node with those from the capabilities.

        force_ordering
            When set to True, sort children of each node in order from the capabilities.

        clean
            When set to True, remove layers which do not exist in capabilities and remove all empty groups.
        """
        self._request = request
        self._ogc_server = ogc_server
        self._force_parents = force_parents
        self._force_ordering = force_ordering
        self._clean = clean

        self._default_wms = main.LayerWMS()
        self._interfaces = None

        self._logger = logging.Logger(str(self), logging.INFO)
        self._log = StringIO()
        self._log_handler = logging.StreamHandler(self._log)
        self._logger.addHandler(self._log_handler)

        self._items_found = 0
        self._themes_added = 0
        self._groups_added = 0
        self._groups_removed = 0
        self._layers_added = 0
        self._layers_removed = 0

    def __str__(self) -> str:
        return f"OGCServerSynchronizer({self._ogc_server.name})"

    def logger(self) -> logging.Logger:
        return self._logger

    def report(self) -> str:
        return self._log.getvalue()

    def check_layers(self) -> None:
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
                if "'" in name:
                    valid = False
                    reason = "Layer name contains quote"
                    self._logger.info(reason)
                    break
                el = capabilities.find(f".//Layer[Name='{name}']")
                if el is None:
                    valid = False
                    reason = f"Layer {name} does not exists on OGC server"
                    self._logger.info(reason)
                    if self._clean:
                        self._request.dbsession.delete(layer)
                        self._logger.info("Removed layer %s", name)
                        self._layers_removed += 1
                    break
                if layer.style and el.find(f"./Style/Name[.='{layer.style}']") is None:
                    valid = False
                    reason = f"Style {layer.style} does not exists in Layer {name}"
                    self._logger.info(reason)
                    break
            layer.valid = valid
            if not valid:
                invalids += 1
            layer.invalid_reason = reason
            items += 1

        if self._clean:
            groups = self._request.dbsession.query(main.LayerGroup)
            for group in groups:
                if len(group.children_relation) == 0:
                    self._request.dbsession.delete(group)
                    self._logger.info("Removed empty group %s", group.name)
                    self._groups_removed += 1

        self._logger.info("Checked %s layers, %s are invalid", items, invalids)

    def synchronize(self, dry_run: bool = False) -> None:
        """
        Run the import of capabilities in layer tree.

        dry_run
            When set to True, do not commit but roll back transaction at end of synchronization.
        """
        with dry_run_transaction(self._request.dbsession, dry_run):
            self.do_synchronize()
            if dry_run:
                self._logger.info("Rolling back transaction due to dry run")

    def do_synchronize(self) -> None:
        self._items_found = 0
        self._themes_added = 0
        self._groups_added = 0
        self._groups_removed = 0
        self._layers_added = 0
        self._layers_removed = 0

        self._default_wms = cast(
            main.LayerWMS, main.LayerWMS.get_default(self._request.dbsession) or main.LayerWMS()
        )
        self._interfaces = self._request.dbsession.query(main.Interface).all()

        capabilities = ElementTree.fromstring(self.wms_capabilities())
        theme_layers = capabilities.findall("Capability/Layer/Layer")
        for theme_layer in theme_layers:
            self.synchronize_layer(theme_layer)

        if self._clean:
            self.check_layers()

        self._logger.info("%s items found", self._items_found)
        self._logger.info("%s themes added", self._themes_added)
        self._logger.info("%s groups added", self._groups_added)
        self._logger.info("%s groups removed", self._groups_removed)
        self._logger.info("%s layers added", self._layers_added)
        self._logger.info("%s layers removed", self._layers_removed)

    def synchronize_layer(self, el: Element, parent: main.TreeGroup | None = None) -> main.TreeItem:
        if el.find("Layer") is None:
            tree_item = self.get_layer_wms(el, parent)
        elif parent is None:
            tree_item = self.get_theme(el)
        else:
            tree_item = self.get_layer_group(el, parent)

        server_children = []
        for child in el.findall("Layer"):
            child_item = self.synchronize_layer(child, tree_item)

            if isinstance(tree_item, main.Theme) and isinstance(child_item, main.LayerWMS):
                # We cannot add layers in themes
                continue

            server_children.append(child_item)

        if self._force_ordering and isinstance(tree_item, main.TreeGroup):
            # Force children ordering, server_children first, external_children last
            external_children = [item for item in tree_item.children if item not in server_children]
            children = server_children + external_children
            if tree_item.children != children:
                tree_item._set_children(  # pylint: disable=protected-access
                    server_children + external_children, order=True
                )
                self._logger.info("Children of %s have been sorted", tree_item.name)

        return tree_item

    def get_theme(self, el: ElementTree) -> main.Theme:
        name_el = el.find("Name")
        assert name_el is not None
        name = name_el.text

        theme = cast(
            Optional[main.Theme],
            self._request.dbsession.query(main.Theme).filter(main.Theme.name == name).one_or_none(),
        )

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

    def get_layer_group(self, el: Element, parent: main.TreeGroup) -> main.LayerGroup:
        name_el = el.find("Name")
        assert name_el is not None
        name = name_el.text
        assert name is not None

        group = cast(
            Optional[main.LayerGroup],
            (
                self._request.dbsession.query(main.LayerGroup)
                .filter(main.LayerGroup.name == name)
                .one_or_none()
            ),
        )

        if group is None:
            group = main.LayerGroup(name=name)
            group.parents_relation.append(main.LayergroupTreeitem(group=parent))

            self._request.dbsession.add(group)
            self._logger.info("Layer %s added as new group in theme %s", name, parent.name)
            self._groups_added += 1
        else:
            self._items_found += 1

            if self._force_parents and group.parents != [parent]:
                group.parents_relation = [main.LayergroupTreeitem(group=parent)]
                self._logger.info("Group %s moved to %s", name, parent.name)

        return group

    def get_layer_wms(self, el: Element, parent: main.TreeGroup | None = None) -> main.LayerWMS:
        name_el = el.find("Name")
        assert name_el is not None
        name = name_el.text
        assert name is not None

        layer = cast(
            Optional[main.LayerWMS],
            self._request.dbsession.query(main.LayerWMS).filter(main.LayerWMS.name == name).one_or_none(),
        )

        if layer is None:
            layer = main.LayerWMS()

            # TreeItem
            layer.name = name
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
            layer.layer = name
            layer.style = (
                self._default_wms.style
                if el.find(f"./Style/Name[.='{self._default_wms.style}']") is not None
                else None
            )
            # layer.time_mode =
            # layer.time_widget =

            self._request.dbsession.add(layer)
            if not isinstance(parent, main.LayerGroup):
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

            parents = [parent] if isinstance(parent, main.LayerGroup) else []
            if self._force_parents and layer.parents != parents:
                layer.parents_relation = [main.LayergroupTreeitem(group=parent) for parent in parents]
                self._logger.info("Layer %s moved to %s", name, parent.name if parent else "root")

        return layer

    @functools.lru_cache(maxsize=10)
    def wms_capabilities(self) -> bytes:
        errors: set[str] = set()
        url = get_url2(
            f"The OGC server '{self._ogc_server.name}'",
            self._ogc_server.url,
            self._request,
            errors,
        )
        if url is None:
            raise Exception("\n".join(errors))  # pylint: disable=broad-exception-raised

        # Add functionality params
        # sparams = get_mapserver_substitution_params(self.request)
        # url.add_query(url, sparams)

        url.add_query(
            {
                "SERVICE": "WMS",
                "VERSION": "1.1.1",
                "REQUEST": "GetCapabilities",
                "ROLE_IDS": "0",
                "USER_ID": "0",
            },
        )

        self._logger.info("Get WMS GetCapabilities from: %s", url)

        headers = {}

        # Add headers for Geoserver
        if self._ogc_server.auth == main.OGCSERVER_AUTH_GEOSERVER:
            headers["sec-username"] = "root"
            headers["sec-roles"] = "root"

        response = requests.get(url.url(), headers=headers, timeout=300)
        self._logger.info("Got response %s in %.1fs.", response.status_code, response.elapsed.total_seconds())
        response.raise_for_status()

        # With WMS 1.3 it returns text/xml also in case of error :-(
        if response.headers.get("Content-Type", "").split(";")[0].strip() not in [
            "application/vnd.ogc.wms_xml",
            "text/xml",
        ]:
            raise Exception(  # pylint: disable=broad-exception-raised
                f"GetCapabilities from URL '{url}' returns a wrong Content-Type: "
                f"{response.headers.get('Content-Type', '')}\n{response.text}"
            )

        return response.content
