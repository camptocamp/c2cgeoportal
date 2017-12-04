from itertools import groupby
from functools import partial
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

from c2cgeoportal_commons.models.main import LayerWMS, RestrictionArea, Interface, OGCServer

_list_field = partial(ListField, LayerWMS)

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
        _list_field('name'),
        _list_field('metadata_url'),
        _list_field('description'),
        _list_field('public'),
        _list_field('geo_table'),
        _list_field('exclude_properties'),
        _list_field('layer'),
        _list_field('style'),
        _list_field('time_mode'),
        _list_field('time_widget'),
        _list_field(
            'ogc_server',
            renderer=lambda layer_wms: layer_wms.ogc_server.name,
            sort_column=OGCServer.name,
            filter_column=OGCServer.name),
        _list_field(
            'interfaces',
            renderer=lambda layer_wms: ', '.join([i.name or '' for i in layer_wms.interfaces]),
            sort_column=Interface.name,
            filter_column=Interface.name),
        _list_field(
            'dimensions',
            renderer=lambda layer_wms: '; '.join(
                ['{}: {}'.format(group[0], ', '.join([d.value for d in group[1]]))
                 for group in groupby(layer_wms.dimensions, lambda d: d.name)])),
        _list_field(
            'parents_relation',
            renderer=lambda layer_wms:', '.join([p.treegroup.name or ''
                                                 for p in layer_wms.parents_relation])),
        _list_field(
            'restrictionareas',
            renderer=lambda layer_wms: ', '.join([r.name or '' for r in layer_wms.restrictionareas])),
        _list_field(
            'metadatas',
            renderer=lambda layer_wms: ', '.join(['{}: {}'.format(m.name, m.value) or ''
                                                  for m in layer_wms.metadatas]))]
    _id_field = 'id'
    _model = LayerWMS
    _base_schema = base_schema

    def _base_query(self):
        return self._request.dbsession.query(LayerWMS).distinct(). \
            outerjoin('ogc_server'). \
            outerjoin('interfaces'). \
            options(subqueryload('interfaces')). \
            options(subqueryload('dimensions')). \
            options(subqueryload('restrictionareas')). \
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
