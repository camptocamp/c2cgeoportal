from functools import partial

from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoform.views.abstract_views import ListField
from deform.widget import FormWidget
from pyramid.view import view_config, view_defaults

from c2cgeoportal_admin.schemas.interfaces import interfaces_schema_node
from c2cgeoportal_admin.schemas.metadata import metadatas_schema_node
from c2cgeoportal_admin.schemas.restriction_areas import restrictionareas_schema_node
from c2cgeoportal_admin.schemas.treeitem import parent_id_node
from c2cgeoportal_admin.views.dimension_layers import DimensionLayerViews
from c2cgeoportal_commons.models.main import LayerGroup, LayerVectorTiles

_list_field = partial(ListField, LayerVectorTiles)


base_schema = GeoFormSchemaNode(LayerVectorTiles, widget=FormWidget(fields_template="layer_fields"))
base_schema.add(metadatas_schema_node.clone())
base_schema.add(interfaces_schema_node.clone())
base_schema.add(restrictionareas_schema_node.clone())
base_schema.add_unique_validator(LayerVectorTiles.name, LayerVectorTiles.id)
base_schema.add(parent_id_node(LayerGroup))


@view_defaults(match_param="table=layers_vectortiles")
class LayerVectorTilesViews(DimensionLayerViews):
    _list_fields = (
        DimensionLayerViews._list_fields
        + [_list_field("style"), _list_field("xyz")]
        + DimensionLayerViews._extra_list_fields
    )
    _id_field = "id"
    _model = LayerVectorTiles
    _base_schema = base_schema

    def _base_query(self):
        return super()._base_query(self._request.dbsession.query(LayerVectorTiles).distinct())

    @view_config(route_name="c2cgeoform_index", renderer="../templates/index.jinja2")
    def index(self):
        return super().index()

    @view_config(route_name="c2cgeoform_grid", renderer="fast_json")
    def grid(self):
        return super().grid()

    @view_config(route_name="c2cgeoform_item", request_method="GET", renderer="../templates/edit.jinja2")
    def view(self):
        return super().edit()

    @view_config(route_name="c2cgeoform_item", request_method="POST", renderer="../templates/edit.jinja2")
    def save(self):
        return super().save()

    @view_config(route_name="c2cgeoform_item", request_method="DELETE", renderer="fast_json")
    def delete(self):
        return super().delete()

    @view_config(
        route_name="c2cgeoform_item_duplicate", request_method="GET", renderer="../templates/edit.jinja2"
    )
    def duplicate(self):
        return super().duplicate()
