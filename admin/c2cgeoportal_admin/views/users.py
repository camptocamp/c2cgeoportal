from functools import partial
from pyramid.view import view_defaults
from pyramid.view import view_config

from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoform.views.abstract_views import AbstractViews, ListField

from c2cgeoportal_commons.models.static import User

_list_field = partial(ListField, User)


@view_defaults(match_param='table=users')
class UserViews(AbstractViews):
    _list_fields = [
        _list_field('username'),
        _list_field('role_name'),
        _list_field('email')]
    _id_field = 'id'
    _model = User
    _base_schema = GeoFormSchemaNode(User)

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
