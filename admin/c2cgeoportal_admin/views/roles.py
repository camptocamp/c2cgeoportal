from functools import partial
from pyramid.view import view_defaults
from pyramid.view import view_config

from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoform.views.abstract_views import AbstractViews, ListField
from sqlalchemy.orm import subqueryload

from c2cgeoportal_commons.models.main import Role
from c2cgeoportal_admin.schemas.map import map_widget
from c2cgeoportal_admin.schemas.functionalities import functionalities_schema_node
from c2cgeoportal_admin.schemas.restriction_areas import restrictionareas_schema_node
from deform.widget import FormWidget


_list_field = partial(ListField, Role)


base_schema = GeoFormSchemaNode(Role, widget=FormWidget(fields_template='role_fields'))
base_schema['extent'].widget = map_widget
base_schema.add_before('extent', functionalities_schema_node.clone())
base_schema.add_before('extent', restrictionareas_schema_node.clone())
base_schema.add_unique_validator(Role.name, Role.id)


@view_defaults(match_param='table=roles')
class RoleViews(AbstractViews):
    _list_fields = [
        _list_field('id'),
        _list_field('name'),
        _list_field('description'),
        _list_field(
            'functionalities',
            renderer=lambda role: ', '.join(['{}={}'.format(f.name, f.value) for f in role.functionalities])
        ),
        _list_field(
            'restrictionareas',
            renderer=lambda role: ', '.join([r.name or '' for r in role.restrictionareas])
        ),
    ]
    _id_field = 'id'
    _model = Role
    _base_schema = base_schema

    def _base_query(self):
        return self._request.dbsession.query(Role). \
            options(subqueryload('functionalities')). \
            options(subqueryload('restrictionareas'))

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
