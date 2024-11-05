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
from typing import cast

import sqlalchemy
import sqlalchemy.orm.query
from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoform.views.abstract_views import (
    DeleteResponse,
    GridResponse,
    IndexResponse,
    ListField,
    ObjectResponse,
    SaveResponse,
)
from deform.widget import FormWidget
from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config, view_defaults

from c2cgeoportal_admin import _
from c2cgeoportal_admin.schemas.interfaces import interfaces_schema_node
from c2cgeoportal_admin.schemas.metadata import metadata_schema_node
from c2cgeoportal_admin.schemas.restriction_areas import restrictionareas_schema_node
from c2cgeoportal_admin.schemas.treeitem import parent_id_node
from c2cgeoportal_admin.views.dimension_layers import DimensionLayerViews
from c2cgeoportal_commons.lib.literal import Literal
from c2cgeoportal_commons.models.main import LayerGroup, LayerVectorTiles

_list_field = partial(ListField, LayerVectorTiles)


base_schema = GeoFormSchemaNode(LayerVectorTiles, widget=FormWidget(fields_template="layer_fields"))
base_schema.add(metadata_schema_node(LayerVectorTiles.metadatas, LayerVectorTiles))
base_schema.add(interfaces_schema_node(LayerVectorTiles.interfaces))
base_schema.add(restrictionareas_schema_node(LayerVectorTiles.restrictionareas))
base_schema.add_unique_validator(LayerVectorTiles.name, LayerVectorTiles.id)
base_schema.add(parent_id_node(LayerGroup))


@view_defaults(match_param="table=layers_vectortiles")
class LayerVectorTilesViews(DimensionLayerViews[LayerVectorTiles]):
    """The vector tiles administration view."""

    _list_fields = (
        DimensionLayerViews._list_fields  # typer: ignore[misc] # pylint: disable=protected-access
        + [_list_field("style"), _list_field("xyz")]
        + DimensionLayerViews._extra_list_fields  # pylint: disable=protected-access
    )

    _id_field = "id"
    _model = LayerVectorTiles
    _base_schema = base_schema

    def _base_query(self) -> sqlalchemy.orm.query.Query[LayerVectorTiles]:
        return super()._sub_query(self._request.dbsession.query(LayerVectorTiles).distinct())

    def _sub_query(
        self, query: sqlalchemy.orm.query.Query[LayerVectorTiles] | None
    ) -> sqlalchemy.orm.query.Query[LayerVectorTiles]:
        del query
        return self._base_query()

    @view_config(route_name="c2cgeoform_index", renderer="../templates/index.jinja2")  # type: ignore[misc]
    def index(self) -> IndexResponse:
        return super().index()

    @view_config(route_name="c2cgeoform_grid", renderer="fast_json")  # type: ignore[misc]
    def grid(self) -> GridResponse:
        return super().grid()

    def schema(self) -> GeoFormSchemaNode:
        try:
            obj = self._get_object()
        except HTTPNotFound:
            obj = None

        schema = cast(GeoFormSchemaNode, self._base_schema.clone())
        if obj is not None:
            schema["style"].description = Literal(
                _("{}<br>Current runtime value is: {}").format(
                    schema["style"].description,
                    obj.style_description(self._request),
                )
            )
        return schema

    @view_config(route_name="c2cgeoform_item", request_method="GET", renderer="../templates/edit.jinja2")  # type: ignore[misc]
    def view(self) -> ObjectResponse:
        return super().edit(self.schema())

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
