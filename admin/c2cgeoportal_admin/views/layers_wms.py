from functools import partial
from sqlalchemy import insert, delete, update
from zope.sqlalchemy import mark_changed
from pyramid.view import view_defaults
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound, HTTPFound

from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoform.views.abstract_views import ListField

from c2cgeoportal_commons.models.main import LayerWMS, LayerWMTS, OGCServer, TreeItem

from c2cgeoportal_admin import _
from c2cgeoportal_admin.schemas.dimensions import dimensions_schema_node
from c2cgeoportal_admin.schemas.metadata import metadatas_schema_node
from c2cgeoportal_admin.schemas.interfaces import interfaces_schema_node
from c2cgeoportal_admin.schemas.restrictionareas import restrictionareas_schema_node
from c2cgeoportal_admin.views.dimension_layers import DimensionLayerViews

_list_field = partial(ListField, LayerWMS)

base_schema = GeoFormSchemaNode(LayerWMS)
base_schema.add(dimensions_schema_node.clone())
base_schema.add(metadatas_schema_node.clone())
base_schema.add(interfaces_schema_node.clone())
base_schema.add(restrictionareas_schema_node.clone())
base_schema.add_unique_validator(LayerWMS.name, LayerWMS.id)


@view_defaults(match_param='table=layers_wms')
class LayerWmsViews(DimensionLayerViews):
    _list_fields = DimensionLayerViews._list_fields + [
        _list_field('layer'),
        _list_field('style'),
        _list_field('time_mode'),
        _list_field('time_widget'),
        _list_field(
            'ogc_server',
            renderer=lambda layer_wms: layer_wms.ogc_server.name,
            sort_column=OGCServer.name,
            filter_column=OGCServer.name)
    ] + DimensionLayerViews._extra_list_fields
    _id_field = 'id'
    _model = LayerWMS
    _base_schema = base_schema

    def _base_query(self):
        return super()._base_query(
            self._request.dbsession.query(LayerWMS).distinct().
            outerjoin('ogc_server'))

    @view_config(route_name='c2cgeoform_index',
                 renderer='../templates/index.jinja2')
    def index(self):
        return super().index()

    @view_config(route_name='c2cgeoform_grid',
                 renderer='json')
    def grid(self):
        return super().grid()

    def _item_actions(self):
        actions = super()._item_actions()
        if not self._is_new():
            actions.append({
                'name': 'convert_to_wmts',
                'label': _('Convert to wmts'),
                'url': self._request.route_url(
                    'layers_wmts_from_wms',
                    table='layers_wmts',
                    wms_layer_id=self._request.matchdict.get('id'),
                    action='from_wms')})
        return actions

    @view_config(route_name='c2cgeoform_item',
                 request_method='GET',
                 renderer='../templates/edit.jinja2')
    def view(self):
        return super().edit()

    @view_config(route_name='c2cgeoform_item',
                 request_method='POST',
                 renderer='../templates/edit.jinja2')
    def save(self):
        return super().save()

    @view_config(route_name='c2cgeoform_item',
                 request_method='DELETE')
    def delete(self):
        return super().delete()

    @view_config(route_name='c2cgeoform_item_action',
                 request_method='GET',
                 renderer='../templates/edit.jinja2')
    def duplicate(self):
        return super().duplicate()

    @view_config(route_name='layers_wms_from_wmts',
                 request_method='GET')
    def convert(self):
        pk = self._request.matchdict.get('wmts_layer_id')
        src = self._request.dbsession.query(LayerWMTS).get(pk)
        default_wms = self._request.dbsession.query(LayerWMS).filter(LayerWMS.name == 'wms-defaults').one()
        if src is None:
            raise HTTPNotFound()
        _dbsession = self._request.dbsession
        with _dbsession.no_autoflush:
            d = delete(LayerWMTS.__table__)
            d = d.where(LayerWMTS.__table__.c.id == pk)
            _dbsession.execute(d)
            i = insert(LayerWMS.__table__)
            i = i.values({
                'id': pk,
                'layer': src.layer,
                'style': src.style,
                'ogc_server_id': default_wms.ogc_server_id,
                'time_mode': default_wms.time_mode,
                'time_widget': default_wms.time_widget})
            _dbsession.execute(i)
            u = update(TreeItem.__table__)
            u = u.where(TreeItem.__table__.c.id == pk)
            u = u.values({'type': 'l_wms'})
            _dbsession.execute(u)
            _dbsession.expunge(src)

        _dbsession.flush()
        mark_changed(_dbsession)

        return HTTPFound(self._request.route_url('c2cgeoform_item', action='edit', id=pk))
