from pyramid.view import view_defaults
from pyramid.view import view_config
from c2cgeoform.views.abstract_views import AbstractViews
from c2cgeoportal_commons.models.main import Role
from c2cgeoportal_commons.models.main  import RestrictionArea
from colanderalchemy import setup_schema
from c2cgeoform.ext import colander_ext

Role.extent.info.update({'colanderalchemy': {
    'typ': colander_ext.Geometry(
        'POLYGON', srid=4326, map_srid=3857),
}})

RestrictionArea.area.info.update({'colanderalchemy': {
    'typ': colander_ext.Geometry(
        'POLYGON', srid=4326, map_srid=3857),
}})


setup_schema(None, Role)

@view_config(route_name='role_', renderer='json')
def role_test_insert(request):
    request.dbsession.begin_nested()
    for i in range (0, 23):
        role = Role("secretary_" + str(i))
        request.dbsession.add(role)
    request.dbsession.commit()
    return {}


@view_defaults(match_param='table=role')
class UserViews(AbstractViews):
    _list_fields = ['name']
    _id_field = 'id'
    _model = Role
    _base_schema = Role.__colanderalchemy__

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
        return super().save()
