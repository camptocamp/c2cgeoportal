from pyramid.view import view_defaults
from pyramid.view import view_config
from c2cgeoform.views.abstract_views import AbstractViews
from c2cgeoportal_commons.models.static import User
from colanderalchemy import setup_schema

setup_schema(None, User)


@view_defaults(match_param='table=user')
class UserViews(AbstractViews):
    _list_fields = ['username', 'email']
    _id_field = 'id'
    _model = User
    _base_schema = User.__colanderalchemy__

    @view_config(route_name='c2cgeoform_index',
                 renderer="../templates/index.jinja2")
    def index(self):
        return super().index()

    @view_config(route_name='c2cgeoform_grid',
                 renderer="json")
    def grid(self):
        return super().grid()

    @view_config(route_name='c2cgeoform_action',
                 request_method='GET',
                 renderer="../templates/edit.jinja2")
    def view(self):
        return super().edit()

    @view_config(route_name='c2cgeoform_action',
                 request_method='POST',
                 renderer="../templates/edit.jinja2")
    def save(self):
        return super().save()
