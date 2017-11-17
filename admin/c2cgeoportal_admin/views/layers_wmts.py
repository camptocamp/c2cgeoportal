from pyramid.view import view_defaults
from pyramid.view import view_config
from c2cgeoform.views.abstract_views import AbstractViews
from c2cgeoportal_commons.models.main import LayerWMTS
from colanderalchemy import setup_schema
from c2cgeoform.views.abstract_views import ListField

setup_schema(None, LayerWMTS)


@view_defaults(match_param='table=layers_wmts')
class LayerWmtsViews(AbstractViews):
    _list_fields = [
        ListField('name'),
        ListField('public'),
        ListField('layer'),
    ]
    _id_field = 'id'
    _model = LayerWMTS
    _base_schema = LayerWMTS.__colanderalchemy__

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
