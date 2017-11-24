from itertools import groupby
from pyramid.view import view_defaults
from pyramid.view import view_config

import colander

from c2cgeoform.ext.deform_ext import RelationCheckBoxListWidget
from c2cgeoform.schema import (
    GeoFormSchemaNode,
    GeoFormManyToManySchemaNode,
    manytomany_validator,
)
from c2cgeoform.views.abstract_views import AbstractViews
from c2cgeoform.views.abstract_views import ListField
from sqlalchemy.orm import subqueryload

from c2cgeoportal_commons.models.main import LayerWMS, RestrictionArea, Interface


base_schema = GeoFormSchemaNode(LayerWMS)
base_schema.add(
    colander.SequenceSchema(
        GeoFormManyToManySchemaNode(Interface),
        name='interfaces',
        widget=RelationCheckBoxListWidget(
            Interface,
            'id',
            'name',
            order_by='name'
        ),
        validator=manytomany_validator
    )
)
base_schema.add(
    colander.SequenceSchema(
        GeoFormManyToManySchemaNode(RestrictionArea),
        name='restrictionareas',
        widget=RelationCheckBoxListWidget(
            RestrictionArea,
            'id',
            'name',
            order_by='name'
        ),
        validator=manytomany_validator
    )
)


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
        ListField(
            'interfaces',
            sortable=False,
            renderer=lambda layer_wms: ', '.join([i.name or '' for i in layer_wms.interfaces])),
        ListField(
            'dimensions',
            sortable=False,
            renderer=lambda layer_wms: '; '.join(
                ['{}: {}'.format(group[0], ', '.join([d.value for d in group[1]]))
                 for group in groupby(layer_wms.dimensions, lambda d: d.name)])),
        ListField(
            'parents_relation',
            sortable=False,
            renderer=lambda layer_wms:', '.join([p.treegroup.name or ''
                                                 for p in layer_wms.parents_relation])),
        ListField(
            'restrictionareas',
            sortable=False,
            renderer=lambda layer_wms: ', '.join([r.name or '' for r in layer_wms.restrictionareas])),
        ListField(
            'metadatas',
            sortable=False,
            renderer=lambda layer_wms: ', '.join(['{}: {}'.format(m.name, m.value) or ''
                                                  for m in layer_wms.metadatas]))]
    _id_field = 'id'
    _model = LayerWMS
    _base_schema = base_schema

    def _base_query(self):
        return self._request.dbsession.query(LayerWMS). \
            options(subqueryload('restrictionareas'))

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
