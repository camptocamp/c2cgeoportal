from functools import partial
from sqlalchemy.orm import subqueryload
from pyramid.view import view_defaults
from pyramid.view import view_config

from c2cgeoportal_commons.models.main import RestrictionArea
from c2cgeoportal_admin.schemas.map import map_widget
from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoportal_admin.schemas.roles import roles_schema_node

from c2cgeoform.views.abstract_views import AbstractViews
from c2cgeoform.views.abstract_views import ListField
from deform.widget import FormWidget

_list_field = partial(ListField, RestrictionArea)

base_schema = GeoFormSchemaNode(RestrictionArea, widget=FormWidget(fields_template='restriction_area_fields'))
base_schema['area'].widget = map_widget
base_schema.add_before('area', roles_schema_node('roles'))
base_schema.add_unique_validator(RestrictionArea.name, RestrictionArea.id)


@view_defaults(match_param='table=restriction_areas')
class RestrictionAreaViews(AbstractViews):
    _list_fields = [
        _list_field('id'),
        _list_field('name'),
        _list_field('description'),
        _list_field('readwrite'),
        _list_field(
            'roles',
            renderer=lambda restriction_area: ', '.join(r.name for r in restriction_area.roles)
        ),
        _list_field(
            'layers',
            renderer=lambda restriction_area: ', '.join(
                '{}-{}'.format(l.item_type, l.name) or '' for l in restriction_area.layers)
        ),
    ]
    _id_field = 'id'
    _model = RestrictionArea
    _base_schema = base_schema

    def _base_query(self):
        return self._request.dbsession.query(RestrictionArea). \
            options(subqueryload('roles')). \
            options(subqueryload('layers'))

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
