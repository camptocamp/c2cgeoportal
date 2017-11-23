from pyramid.view import view_defaults
from pyramid.view import view_config

from sqlalchemy.orm import subqueryload

from c2cgeoform.views.abstract_views import AbstractViews
from c2cgeoportal_commons.models.main import LayerWMS
from colanderalchemy import setup_schema
from c2cgeoform.views.abstract_views import ListField

setup_schema(None, LayerWMS)


@view_defaults(match_param='table=layers_wms')
class LayerWmsViews(AbstractViews):
    _list_fields = [
        ListField('name'),
        ListField('metadata_url'),
        ListField('description'),
        ListField('public'),
        ListField('geo_table'),
        ListField('exclude_properties'),
        ListField('layer'),
        ListField('style'),
        ListField('time_mode'),
        ListField('time_widget'),
        ListField('ogc_server', renderer=lambda layer_wms: layer_wms.ogc_server.name),
        ListField('restrictionareas', renderer=lambda layer_wms:
                  ", ".join([r.name or '' for r in layer_wms.restrictionareas]))]
    _id_field = 'id'
    _model = LayerWMS
    _base_schema = LayerWMS.__colanderalchemy__

    def _base_query(self):
        return self._request.dbsession.query(LayerWMS). \
            options(subqueryload("restrictionareas"))

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
