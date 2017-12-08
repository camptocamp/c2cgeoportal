from functools import partial
from pyramid.view import view_defaults
from pyramid.view import view_config

from c2cgeoform.schema import GeoFormSchemaNode

from c2cgeoform.views.abstract_views import AbstractViews
from c2cgeoform.views.abstract_views import ListField
from sqlalchemy.orm import subqueryload
from sqlalchemy.sql.functions import concat

from c2cgeoportal_commons.models.main import LayerGroup, Metadata

_list_field = partial(ListField, LayerGroup)

base_schema = GeoFormSchemaNode(LayerGroup)


@view_defaults(match_param='table=layer_groups')
class LayerGroupsViews(AbstractViews):
    _list_fields = [
        _list_field('name'),
        _list_field('metadata_url'),
        _list_field('description'),
        _list_field('is_expanded'),
        _list_field('is_internal_wms'),
        _list_field('is_base_layer'),
        _list_field(
            'parents_relation',
            renderer=lambda layers_group:', '.join([p.treegroup.name or ''
                                                    for p in layers_group.parents_relation])),
        _list_field(
            'metadatas',
            renderer=lambda layers_group: ', '.join(['{}: {}'.format(m.name, m.value) or ''
                                                     for m in layers_group.metadatas]),
            filter_column=concat(Metadata.name, ': ', Metadata.value).label('metadata'))]
    _id_field = 'id'
    _model = LayerGroup
    _base_schema = base_schema

    def _base_query(self):
        return self._request.dbsession.query(LayerGroup).distinct(). \
            outerjoin('metadatas'). \
            options(subqueryload('metadatas')). \
            options(subqueryload('parents_relation').joinedload('treegroup'))

    @view_config(route_name='c2cgeoform_index',
                 renderer='../templates/index.jinja2')
    def index(self):
        return super().index()

    @view_config(route_name='c2cgeoform_grid',
                 renderer='json')
    def grid(self):
        return super().grid()

    @view_config(route_name='c2cgeoform_action',
                 request_method='GET',
                 renderer='../templates/edit.jinja2')
    def view(self):
        return super().edit()

    @view_config(route_name='c2cgeoform_action',
                 request_method='POST',
                 renderer='../templates/edit.jinja2')
    def save(self):
        return super().save()

    @view_config(route_name='c2cgeoform_action',
                 request_method='DELETE')
    def delete(self):
        return super().delete()
