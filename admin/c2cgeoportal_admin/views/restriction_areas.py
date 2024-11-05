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

import colander
import sqlalchemy.orm.query
from c2cgeoform.schema import GeoFormManyToManySchemaNode, GeoFormSchemaNode
from c2cgeoform.views.abstract_views import (
    DeleteResponse,
    GridResponse,
    IndexResponse,
    ListField,
    ObjectResponse,
    SaveResponse,
)
from deform.widget import FormWidget
from pyramid.view import view_config, view_defaults
from sqlalchemy.orm import subqueryload

from c2cgeoportal_admin.schemas.roles import roles_schema_node
from c2cgeoportal_admin.schemas.treegroup import treeitem_edit_url
from c2cgeoportal_admin.views.logged_views import LoggedViews
from c2cgeoportal_admin.widgets import ChildrenWidget, ChildWidget
from c2cgeoportal_commons.models.main import Layer, RestrictionArea

_list_field = partial(ListField, RestrictionArea)

base_schema = GeoFormSchemaNode(RestrictionArea, widget=FormWidget(fields_template="restriction_area_fields"))
base_schema.add_before("area", roles_schema_node(RestrictionArea.roles))
base_schema.add_unique_validator(RestrictionArea.name, RestrictionArea.id)


def layers(node, kw):  # pylint: disable=unused-argument
    """Get the layers serializable representation."""
    dbsession = kw["request"].dbsession
    query = dbsession.query(Layer).order_by(Layer.name)
    return [
        {
            "id": layer.id,
            "label": layer.name,
            "icon_class": f"icon-{layer.item_type}",
            "edit_url": treeitem_edit_url(kw["request"], layer),
            "group": "All",
        }
        for layer in query
    ]


base_schema.add(
    colander.SequenceSchema(
        GeoFormManyToManySchemaNode(
            Layer,
            name="layer",
            includes=["id"],
            widget=ChildWidget(
                input_name="id",
                model=Layer,
                label_field="name",
                icon_class=lambda layer: f"icon-{layer.item_type}",
                edit_url=treeitem_edit_url,
            ),
        ),
        name="layers",
        title=RestrictionArea.layers.info["colanderalchemy"]["title"],
        description=RestrictionArea.layers.info["colanderalchemy"]["description"],
        candidates=colander.deferred(layers),
        widget=ChildrenWidget(child_input_name="id", orderable=False),
    )
)


@view_defaults(match_param="table=restriction_areas")
class RestrictionAreaViews(LoggedViews[RestrictionArea]):
    """The restriction area administration view."""

    _list_fields = [
        _list_field("id"),
        _list_field("name"),
        _list_field("description"),
        _list_field("readwrite"),
        _list_field(
            "roles", renderer=lambda restriction_area: ", ".join(r.name for r in restriction_area.roles)
        ),
        _list_field(
            "layers",
            renderer=lambda restriction_area: ", ".join(
                f"{layer.item_type}-{layer.name}" or "" for layer in restriction_area.layers
            ),
        ),
    ]
    _id_field = "id"
    _model = RestrictionArea
    _base_schema = base_schema

    def _base_query(self) -> sqlalchemy.orm.query.Query[RestrictionArea]:
        session = self._request.dbsession
        assert isinstance(session, sqlalchemy.orm.Session)
        return (
            session.query(RestrictionArea)
            .options(subqueryload(RestrictionArea.roles))
            .options(subqueryload(RestrictionArea.layers))
        )

    @view_config(route_name="c2cgeoform_index", renderer="../templates/index.jinja2")  # type: ignore[misc]
    def index(self) -> IndexResponse:
        return super().index()

    @view_config(route_name="c2cgeoform_grid", renderer="fast_json")  # type: ignore[misc]
    def grid(self) -> GridResponse:
        return super().grid()

    @view_config(route_name="c2cgeoform_item", request_method="GET", renderer="../templates/edit.jinja2")  # type: ignore[misc]
    def view(self) -> ObjectResponse:
        return super().edit()

    @view_config(route_name="c2cgeoform_item", request_method="POST", renderer="../templates/edit.jinja2")  # type: ignore[misc]
    def save(self) -> SaveResponse:
        return super().save()

    @view_config(route_name="c2cgeoform_item", request_method="DELETE", renderer="fast_json")  # type: ignore[misc]
    def delete(self) -> DeleteResponse:
        return super().delete()

    @view_config(  # type: ignore[misc]
        route_name="c2cgeoform_item_duplicate", request_method="GET", renderer="../templates/edit.jinja2"
    )
    def duplicate(self) -> ObjectResponse:
        return super().duplicate()
