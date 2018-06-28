from c2cgeoportal_commons.models.main import OGCServer
from functools import partial
from pyramid.view import view_defaults
from pyramid.view import view_config

from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoform.views.abstract_views import AbstractViews
from c2cgeoform.views.abstract_views import ListField
from deform.widget import FormWidget

_list_field = partial(ListField, OGCServer)

base_schema = GeoFormSchemaNode(OGCServer, widget=FormWidget(fields_template='ogcserver_fields'))
base_schema.add_unique_validator(OGCServer.name, OGCServer.id)


@view_defaults(match_param='table=ogc_servers')
class OGCServerViews(AbstractViews):
    _list_fields = [
        _list_field('id'),
        _list_field('name'),
        _list_field('description'),
        _list_field('url'),
        _list_field('url_wfs'),
        _list_field('type'),
        _list_field('image_type'),
        _list_field('auth'),
        _list_field('wfs_support'),
        _list_field('is_single_tile')
    ]
    _id_field = 'id'
    _model = OGCServer
    _base_schema = base_schema

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
