from functools import partial
from pyramid.view import view_defaults
from pyramid.view import view_config

from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoform.views.abstract_views import ListField
from deform.widget import FormWidget

from c2cgeoportal_commons.models.main import LayerV1

from c2cgeoportal_admin.schemas.metadata import metadatas_schema_node
from c2cgeoportal_admin.schemas.interfaces import interfaces_schema_node
from c2cgeoportal_admin.schemas.restriction_areas import restrictionareas_schema_node
from c2cgeoportal_admin.views.layers import LayerViews

_list_field = partial(ListField, LayerV1)

base_schema = GeoFormSchemaNode(LayerV1, widget=FormWidget(fields_template='layer_v1_fields'))
base_schema.add(interfaces_schema_node.clone())
base_schema.add(restrictionareas_schema_node.clone())
base_schema.add(metadatas_schema_node.clone())
base_schema.add_unique_validator(LayerV1.name, LayerV1.id)


@view_defaults(match_param='table=layers_v1')
class LayerV1Views(LayerViews):
    _list_fields = LayerViews._list_fields + [
        _list_field('layer'),
        _list_field('is_checked'),
        _list_field('icon'),
        _list_field('layer_type'),
        _list_field('url'),
        _list_field('image_type'),
        _list_field('style'),
        _list_field('dimensions'),
        _list_field('matrix_set'),
        _list_field('wms_url'),
        _list_field('wms_layers'),
        _list_field('query_layers'),
        _list_field('kml'),
        _list_field('is_single_tile'),
        _list_field('legend'),
        _list_field('legend_image'),
        _list_field('legend_rule'),
        _list_field('is_legend_expanded'),
        _list_field('min_resolution'),
        _list_field('max_resolution'),
        _list_field('disclaimer'),
        _list_field('identifier_attribute_field'),
        _list_field('time_mode'),
        _list_field('time_widget')
    ] + LayerViews._extra_list_fields
    _id_field = 'id'
    _model = LayerV1
    _base_schema = base_schema

    def _base_query(self, query=None):
        return super()._base_query(
            self._request.dbsession.query(LayerV1).distinct())

    @view_config(route_name='c2cgeoform_index',
                 renderer='../templates/index.jinja2')
    def index(self):
        return super().index()

    @view_config(route_name='c2cgeoform_grid',
                 renderer='fast_json')
    def grid(self):
        return super().grid()

    @view_config(route_name='c2cgeoform_item',
                 request_method='GET',
                 renderer='../templates/edit.jinja2')
    def view(self):
        return super().edit()

    @view_config(route_name='c2cgeoform_item',
                 request_method='POST',
                 renderer='../templates/edit.jinja2')
    def save(self):
        return super().save()

    @view_config(route_name='c2cgeoform_item',
                 request_method='DELETE',
                 renderer='fast_json')
    def delete(self):
        return super().delete()

    @view_config(route_name='c2cgeoform_item_duplicate',
                 request_method='GET',
                 renderer='../templates/edit.jinja2')
    def duplicate(self):
        return super().duplicate()
