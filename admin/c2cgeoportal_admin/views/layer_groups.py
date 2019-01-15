from functools import partial
from pyramid.view import view_defaults
from pyramid.view import view_config

from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoform.views.abstract_views import ListField
from deform.widget import FormWidget

from c2cgeoportal_admin.schemas.treegroup import children_schema_node
from c2cgeoportal_admin.schemas.metadata import metadatas_schema_node
from c2cgeoportal_admin.schemas.treeitem import parent_id_node
from c2cgeoportal_admin.views.treeitems import TreeItemViews
from c2cgeoportal_commons.models.main import LayerGroup, TreeGroup


_list_field = partial(ListField, LayerGroup)


base_schema = GeoFormSchemaNode(LayerGroup, widget=FormWidget(fields_template='layer_group_fields'))
base_schema.add(children_schema_node())
base_schema.add(metadatas_schema_node.clone())
base_schema.add_unique_validator(LayerGroup.name, LayerGroup.id)
base_schema.add(parent_id_node(TreeGroup))


@view_defaults(match_param='table=layer_groups')
class LayerGroupsViews(TreeItemViews):

    _list_fields = TreeItemViews._list_fields + \
        [_list_field('is_expanded')] + \
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
