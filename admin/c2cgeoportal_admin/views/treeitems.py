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


from functools import partial
from typing import Generic, TypeVar

import sqlalchemy
from c2cgeoform.views.abstract_views import ListField, SaveResponse
from pyramid.view import view_config
from sqlalchemy.orm import subqueryload
from sqlalchemy.sql.functions import concat

from c2cgeoportal_admin.views.logged_views import LoggedViews
from c2cgeoportal_commons.models.main import LayergroupTreeitem, Metadata, TreeGroup, TreeItem

_list_field = partial(ListField, TreeItem)


_T = TypeVar("_T", bound=TreeItem)


class TreeItemViews(LoggedViews[_T], Generic[_T]):
    """The admin tree item view."""

    _list_fields = [
        _list_field("id"),
        _list_field("name"),
        _list_field("description"),
    ]

    _extra_list_fields_no_parents = [
        _list_field(
            "metadatas",
            renderer=lambda treeitem: ", ".join([f"{m.name}: {m.value}" or "" for m in treeitem.metadatas]),
            filter_column=concat(Metadata.name, ": ", Metadata.value).label("metadata"),
        )
    ]
    _extra_list_fields = [
        _list_field(
            "parents_relation",
            renderer=lambda layer_wms: ", ".join(
                [
                    p.treegroup.name or ""
                    for p in sorted(layer_wms.parents_relation, key=lambda p: p.treegroup.name or "")
                ]
            ),
        )
    ] + _extra_list_fields_no_parents

    @view_config(route_name="c2cgeoform_item", request_method="POST", renderer="../templates/edit.jinja2")  # type: ignore[misc]
    def save(self) -> SaveResponse:
        response = super().save()
        # correctly handles the validation error as if there is a validation error, cstruct is empty
        has_to_be_registered_in_parent = (
            hasattr(self, "_appstruct") and self._appstruct is not None and self._appstruct.get("parent_id")
        )
        if has_to_be_registered_in_parent:
            parent = self._request.dbsession.query(TreeGroup).get(has_to_be_registered_in_parent)
            rel = LayergroupTreeitem(parent, self._obj, 100)
            self._request.dbsession.add(rel)
        return response

    def _sub_query(self, query: sqlalchemy.orm.query.Query[TreeItem]) -> sqlalchemy.orm.query.Query[TreeItem]:
        return (
            query.outerjoin(TreeItem.metadatas)
            .options(subqueryload(TreeItem.parents_relation).joinedload(LayergroupTreeitem.treegroup))
            .options(subqueryload(TreeItem.metadatas))
        )
