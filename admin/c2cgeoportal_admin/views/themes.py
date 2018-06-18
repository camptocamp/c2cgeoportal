from functools import partial
from pyramid.view import view_defaults
from pyramid.view import view_config

from sqlalchemy.orm import subqueryload
from sqlalchemy.sql.functions import concat
from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoform.views.abstract_views import ListField
from deform.widget import FormWidget

from c2cgeoportal_commons.models.main import Theme, Interface, Role, Functionality
from c2cgeoportal_admin.schemas.treegroup import children_schema_node
from c2cgeoportal_admin.schemas.functionalities import functionalities_schema_node
from c2cgeoportal_admin.schemas.metadata import metadatas_schema_node
from c2cgeoportal_admin.schemas.interfaces import interfaces_schema_node
from c2cgeoportal_admin.schemas.roles import roles_schema_node
from c2cgeoportal_admin.views.treeitems import TreeItemViews


_list_field = partial(ListField, Theme)

base_schema = GeoFormSchemaNode(Theme, widget=FormWidget(fields_template='theme_fields'))
base_schema.add(children_schema_node(only_groups=True))
base_schema.add(functionalities_schema_node.clone())
base_schema.add(roles_schema_node('restricted_roles'))
base_schema.add(interfaces_schema_node.clone())
base_schema.add(metadatas_schema_node.clone())
base_schema.add_unique_validator(Theme.name, Theme.id)


@view_defaults(match_param='table=themes')
class ThemeViews(TreeItemViews):

    _list_fields = TreeItemViews._list_fields + [
        _list_field('ordering'),
        _list_field('public'),
        _list_field('icon'),
        _list_field(
            'functionalities',
            renderer=lambda themes: ', '.join(
                ['{}={}'.format(f.name, f.value)
                    for f in sorted(themes.functionalities, key=lambda f: f.name)]),
            filter_column=concat(Functionality.name, '=', Functionality.value)
        ),
        _list_field(
            'restricted_roles',
            renderer=lambda themes: ', '.join([r.name or '' for r in themes.restricted_roles]),
            filter_column=Role.name
        ),
        _list_field(
            'interfaces',
            renderer=lambda themes: ', '.join(
                [i.name or '' for i in sorted(themes.interfaces, key=lambda i: i.name)]),
            filter_column=Interface.name
        )] + TreeItemViews._extra_list_fields_no_parents

    _id_field = 'id'
    _model = Theme
    _base_schema = base_schema

    def _base_query(self, query=None):
        return super()._base_query(
            self._request.dbsession.query(Theme).distinct().
            outerjoin('interfaces').
            outerjoin('restricted_roles').
            outerjoin('functionalities').
            options(subqueryload('functionalities')).
            options(subqueryload('restricted_roles')).
            options(subqueryload('interfaces')))

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
