from pyramid.view import view_defaults
from pyramid.view import view_config
from c2cgeoform.views.abstract_views import AbstractViews
from c2cgeoportal_commons.models.main import User

@view_config(route_name='user_', renderer='json')
def user_test_insert(request):
    request.dbsession.begin_nested()
    for i in range (0, 23):
        user = User("babar_" + str(i), email='mail' + str(i))
        request.dbsession.add(user)
    request.dbsession.commit()
    return {}

@view_defaults(route_name='user')
class UserViews(AbstractViews):
    _list_fields = ['username', 'email']
    _id_field = 'username'
    _model = User

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
