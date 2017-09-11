from pyramid.view import view_defaults
from pyramid.view import view_config
from c2cgeoform.views.abstract_views import AbstractViews
from c2cgeoportal_commons.models.main import Role


@view_defaults(match_param='table=role')
class RoleViews(AbstractViews):
    _list_fields = ['name']
    _id_field = 'id'
    _model = Role

    @view_config(match_param=("id=all", "action=index"), renderer="c2cgeoform:templates/site/index.pt")
    def index(self):
        return super().index()

    @view_config(match_param=("id=all", "action=grid"), renderer="json")
    def grid(self):
        return super().grid()

    @view_config(match_param=("action=edit"), renderer="json")
    def edit(self):
        return {}

    @view_config(match_param=("action=view"), renderer="json")
    def view(self):
        return {}
