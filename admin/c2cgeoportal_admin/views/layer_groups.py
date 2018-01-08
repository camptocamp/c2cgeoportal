from functools import partial
from pyramid.view import view_defaults
from pyramid.view import view_config
from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoform.views.abstract_views import ListField
from c2cgeoportal_commons.models.main import LayerGroup
from c2cgeoportal_admin.schemas.treegroup import children_schema_node
from c2cgeoportal_admin.views.treeitems import TreeItemViews

_list_field = partial(ListField, LayerGroup)


base_schema = GeoFormSchemaNode(LayerGroup)
base_schema.add(children_schema_node())


@view_defaults(match_param='table=layer_groups')
class LayerGroupsViews(TreeItemViews):

    _list_fields = TreeItemViews._list_fields + [
        _list_field('is_expanded'),
        _list_field('is_internal_wms'),
        _list_field('is_base_layer')] + \
        TreeItemViews._extra_list_fields

    _id_field = 'id'
    _model = LayerGroup
    _base_schema = base_schema

    def _base_query(self, query=None):
        return super()._base_query(
            self._request.dbsession.query(LayerGroup).distinct())

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
