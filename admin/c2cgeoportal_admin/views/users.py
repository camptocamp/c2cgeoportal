from pyramid.view import view_defaults
from pyramid.view import view_config
from c2cgeoform.views.abstract_views import AbstractViews
from c2cgeoportal_commons.models.main import User
from colanderalchemy import setup_schema
from deform.widget import HiddenWidget
from deform.widget import CheckboxWidget

@view_defaults(match_param='table=user')
class UserViews(AbstractViews):
    _list_fields = ['username', 'email']
    _id_field = 'id'
    _model = User
    _base_schema = User.__colanderalchemy__

    @view_config(match_param=("id=all", "action=index"), renderer="c2cgeoform:templates/site/index.pt")
    def index(self):
        return super().index()

    @view_config(match_param=("id=all", "action=grid"), renderer="json")
    def grid(self):
        return super().grid()

    @view_config(match_param=("action=edit"), renderer="c2cgeoform:templates/site/edit.pt")
    def edit(self):
        return super().edit()

    @view_config(match_param=("action=view"), renderer="json")
    def view(self):
        return {}
