from functools import partial
from pyramid.view import view_defaults
from pyramid.view import view_config

from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoform.views.abstract_views import ListField

from c2cgeoportal_commons.models.main import LayerWMS, OGCServer

from c2cgeoportal_admin.views.dimension_layers import DimensionLayerViews
from c2cgeoportal_admin.views.interfaces import interfaces_schema_node
from c2cgeoportal_admin.views.restrictionareas import restrictionareas_schema_node

_list_field = partial(ListField, LayerWMS)

base_schema = GeoFormSchemaNode(LayerWMS)
base_schema.add(interfaces_schema_node.clone())
base_schema.add(restrictionareas_schema_node.clone())


@view_defaults(match_param='table=layers_wms')
class LayerWmsViews(DimensionLayerViews):
    _list_fields = DimensionLayerViews._list_fields + [
        _list_field('layer'),
        _list_field('style'),
        _list_field('time_mode'),
        _list_field('time_widget'),
        _list_field(
            'ogc_server',
            renderer=lambda layer_wms: layer_wms.ogc_server.name,
            sort_column=OGCServer.name,
            filter_column=OGCServer.name)
    ] + DimensionLayerViews._extra_list_fields
    _id_field = 'id'
    _model = LayerWMS
    _base_schema = base_schema

    def _base_query(self):
        return super()._base_query(
            self._request.dbsession.query(LayerWMS).distinct().
            outerjoin('ogc_server'))

    @view_config(route_name='c2cgeoform_index',
                 renderer='../templates/index.jinja2')
    def index(self):
        return super().index()

    @view_config(route_name='c2cgeoform_grid',
                 renderer='json')
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
                 request_method='DELETE')
    def delete(self):
        return super().delete()

    @view_config(route_name='c2cgeoform_item_action',
                 request_method='GET',
                 renderer='../templates/edit.jinja2')
    def duplicate(self):
        return super().duplicate()
