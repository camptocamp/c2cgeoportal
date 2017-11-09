from pyramid.view import view_defaults
from pyramid.view import view_config
from c2cgeoform.views.abstract_views import AbstractViews
from c2cgeoportal_commons.models.main import Role
from c2cgeoform.views.abstract_views import ListField as ListField
from colanderalchemy import setup_schema

setup_schema(None, Role)


@view_defaults(match_param='table=roles')
class RoleViews(AbstractViews):
    _list_fields = [
        ListField('name'),
        ListField('description'),
        ListField('functionalities', renderer=lambda role:
                  ", ".join(["{}={}".format(f.name, f.value) for f in role.functionalities])),
        ListField('restrictionareas', renderer=lambda role:
                  ", ".join([r.name or '' for r in role.restrictionareas]))]
    _id_field = 'id'
    _model = Role
    _base_schema = Role.__colanderalchemy__

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

    @view_config(route_name='c2cgeoform_action',
                 request_method='DELETE')
    def delete(self):
        return super().delete()
