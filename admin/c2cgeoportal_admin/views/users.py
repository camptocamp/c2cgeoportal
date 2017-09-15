from pyramid.view import view_defaults
from pyramid.view import view_config
from c2cgeoform.views.abstract_views import AbstractViews
from c2cgeoportal_commons.models.main import User
from colanderalchemy import setup_schema
from deform.widget import HiddenWidget
from deform.widget import CheckboxWidget

@view_config(route_name='user_', renderer='json')
def user_test_insert(request):
    request.dbsession.begin_nested()
    for i in range (0, 23):
        user = User("babar_" + str(i), email='mail' + str(i))
        request.dbsession.add(user)
    request.dbsession.commit()
    return {}

HIDE_FIELD = {'colanderalchemy': {
                'widget': HiddenWidget()
        }}

User.id.info.update(HIDE_FIELD)
User.is_password_changed.info.update({'colanderalchemy': {'widget': CheckboxWidget(readonly=True)}})
User.item_type.info.update(HIDE_FIELD)

setup_schema(None, User)

@view_defaults(match_param='table=user')
class UserViews(AbstractViews):
    _list_fields = ['username', 'email']
    _id_field = 'id'
    _model = User
    _base_schema = User.__colanderalchemy__

    @view_config(route_name='c2cgeoform_index', renderer="c2cgeoform:templates/site/index.pt")
    def index(self):
        return super().index()

    @view_config(route_name='c2cgeoform_grid', renderer="json")
    def grid(self):
        return super().grid()

    @view_config(route_name='c2cgeoform_action', request_method='GET', renderer="c2cgeoform:templates/site/edit.pt")
    def view(self):
        return super().view()

    @view_config(route_name='c2cgeoform_action', request_method='POST', renderer="c2cgeoform:templates/site/edit.pt")
    def save(self):
        current = super()._get_object()
        if current._password != self._request.POST.get('_password'):
            current._set_password(self._request.POST.get('_password'))
            self._request.POST.__setitem__('_password', current._password)
        if current.temp_password != self._request.POST.get('temp_password') and self._request.POST.get('temp_password') != '':
            current.set_temp_password(self._request.POST.get('temp_password'))
            self._request.POST.__setitem__('temp_password', current.temp_password)
        return super().save()
