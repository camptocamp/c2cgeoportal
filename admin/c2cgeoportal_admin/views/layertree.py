# Copyright (c) 2017-2024, Camptocamp SA
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


from typing import Any

import pyramid.request
from c2cgeoform.views.abstract_views import DeleteResponse, ItemAction
from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config, view_defaults
from translationstring import TranslationStringFactory

from c2cgeoportal_admin import _
from c2cgeoportal_commons.models.main import Interface, Layer, LayergroupTreeitem, Theme, TreeItem

itemtypes_tables = {
    "theme": "themes",
    "group": "layer_groups",
    "l_wms": "layers_wms",
    "l_wmts": "layers_wmts",
    "l_cog": "layers_cog",
}


@view_defaults(match_param="application=admin")
class LayerTreeViews:
    """The layer tree administration view."""

    def __init__(self, request: pyramid.request.Request):
        self._request = request
        self._dbsession = request.dbsession

    @view_config(route_name="layertree", renderer="../templates/layertree.jinja2")  # type: ignore[misc]
    def index(self) -> dict[str, int]:
        node_limit = self._request.registry.settings["admin_interface"].get("layer_tree_max_nodes")
        limit_exceeded = self._dbsession.query(LayergroupTreeitem).count() < node_limit
        return {"limit_exceeded": limit_exceeded, "interfaces": self._dbsession.query(Interface).all()}

    @view_config(route_name="layertree_children", renderer="fast_json")  # type: ignore[misc]
    def children(self) -> list[dict[str, Any]]:
        interface = self._request.params.get("interface", None)
        group_id = self._request.params.get("group_id", None)
        path = self._request.params.get("path", "")

        client_tsf = TranslationStringFactory(f"{self._request.registry.package_name}-client")

        if group_id is None:
            items = self._dbsession.query(Theme).order_by(Theme.ordering)
            if interface is not None:
                items = items.join(Theme.interfaces).filter(Interface.name == interface)

        else:
            items = (
                self._dbsession.query(TreeItem)
                .join(TreeItem.parents_relation)
                .filter(LayergroupTreeitem.treegroup_id == group_id)
                .order_by(LayergroupTreeitem.ordering)
            )

        return [
            {
                "id": item.id,
                "item_type": item.item_type,
                "name": item.name,
                "translated_name": self._request.localizer.translate(client_tsf(item.name)),
                "description": item.description,
                "path": f"{path}_{item.id}",
                "parent_path": path,
                "actions": [action.to_dict(self._request) for action in self._item_actions(item, group_id)],
            }
            for item in items
            if interface is None
            or not isinstance(item, Layer)
            or interface in [interface.name for interface in item.interfaces]
        ]

    def _item_actions(self, item: TreeItem, parent_id: int | None = None) -> list[ItemAction]:
        actions = []
        actions.append(
            ItemAction(
                name="edit",
                label=_("Edit"),
                icon="glyphicon glyphicon-pencil",
                url=self._request.route_url(
                    "c2cgeoform_item", table=itemtypes_tables[item.item_type], id=item.id
                ),
            )
        )

        if item.item_type in ("theme", "group"):
            actions.append(
                ItemAction(
                    name="new_layer_group",
                    label=_("New layer group"),
                    icon="glyphicon glyphicon-plus",
                    url=f"{self._request.route_url('c2cgeoform_item', table='layer_groups', id='new')}?"
                    f"parent_id={item.id}",
                )
            )

        if item.item_type == "group":
            actions.append(
                ItemAction(
                    name="new_layer_wms",
                    label=_("New WMS layer"),
                    icon="glyphicon glyphicon-plus",
                    url=f"{self._request.route_url('c2cgeoform_item', table='layers_wms', id='new')}?"
                    f"parent_id={item.id}",
                )
            )

            actions.append(
                ItemAction(
                    name="new_layer_wmts",
                    label=_("New WMTS layer"),
                    icon="glyphicon glyphicon-plus",
                    url=f"{self._request.route_url('c2cgeoform_item', table='layers_wmts', id='new')}?"
                    f"parent_id={item.id}",
                )
            )

        actions.append(
            ItemAction(
                name="duplicate",
                label=_("Duplicate"),
                icon="glyphicon glyphicon-duplicate",
                url=self._request.route_url(
                    "c2cgeoform_item_duplicate", table=itemtypes_tables[item.item_type], id=item.id
                ),
            )
        )

        if parent_id is not None:
            actions.append(
                ItemAction(
                    name="unlink",
                    label=_("Unlink"),
                    icon="glyphicon glyphicon-log-out",
                    url=self._request.route_url("layertree_unlink", group_id=parent_id, item_id=item.id),
                    method="DELETE",
                    confirmation=_("Are your sure you want to unlink this record from his parent?"),
                )
            )

        actions.append(
            ItemAction(
                name="delete",
                label=_("Delete"),
                icon="glyphicon glyphicon-remove",
                url=self._request.route_url("layertree_delete", item_id=item.id),
                method="DELETE",
                confirmation=_("Are your sure you want to delete this record?"),
            )
        )

        return actions

    @view_config(route_name="layertree_unlink", request_method="DELETE", renderer="fast_json")  # type: ignore[misc]
    def unlink(self) -> dict[str, Any]:
        group_id = self._request.matchdict.get("group_id")
        item_id = self._request.matchdict.get("item_id")
        link = (
            self._request.dbsession.query(LayergroupTreeitem)
            .filter(LayergroupTreeitem.treegroup_id == group_id)
            .filter(LayergroupTreeitem.treeitem_id == item_id)
            .one_or_none()
        )
        if link is None:
            raise HTTPNotFound()
        self._request.dbsession.delete(link)
        self._request.dbsession.flush()
        return {"success": True, "redirect": self._request.route_url("layertree")}

    @view_config(route_name="layertree_delete", request_method="DELETE", renderer="fast_json")  # type: ignore[misc]
    def delete(self) -> DeleteResponse:
        item_id = self._request.matchdict.get("item_id")
        item = self._request.dbsession.query(TreeItem).get(item_id)
        if item is None:
            raise HTTPNotFound()
        self._request.dbsession.delete(item)
        self._request.dbsession.flush()
        return {"success": True, "redirect": self._request.route_url("layertree")}
