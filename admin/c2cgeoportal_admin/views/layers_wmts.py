from functools import partial
from sqlalchemy import insert, delete, update
from zope.sqlalchemy import mark_changed
from pyramid.view import view_defaults
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound, HTTPFound

from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoform.views.abstract_views import ListField

from c2cgeoportal_admin import _
from c2cgeoportal_commons.models.main import LayerWMTS, LayerWMS, TreeItem
from c2cgeoportal_admin.schemas.dimensions import dimensions_schema_node
from c2cgeoportal_admin.schemas.metadata import metadatas_schema_node
from c2cgeoportal_admin.schemas.interfaces import interfaces_schema_node
from c2cgeoportal_admin.schemas.restrictionareas import restrictionareas_schema_node
from c2cgeoportal_admin.views.dimension_layers import DimensionLayerViews

_list_field = partial(ListField, LayerWMTS)

base_schema = GeoFormSchemaNode(LayerWMTS)
base_schema.add(dimensions_schema_node.clone())
base_schema.add(metadatas_schema_node.clone())
base_schema.add(interfaces_schema_node.clone())
base_schema.add(restrictionareas_schema_node.clone())
base_schema.add_unique_validator(LayerWMTS.name, LayerWMTS.id)


@view_defaults(match_param='table=layers_wmts')
class LayerWmtsViews(DimensionLayerViews):
    _list_fields = DimensionLayerViews._list_fields + [
        _list_field('url'),
        _list_field('layer'),
        _list_field('style'),
        _list_field('matrix_set'),
        _list_field('image_type'),
    ] + DimensionLayerViews._extra_list_fields
    _id_field = 'id'
    _model = LayerWMTS
    _base_schema = base_schema

    def _base_query(self, query=None):
        return super()._base_query(
            self._request.dbsession.query(LayerWMTS).distinct())

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
                'name': 'convert_to_wms',
                'label': _('Convert to wms'),
                'url': self._request.route_url(
                    'layers_wms_from_wmts',
                    table='layers_wms',
                    wmts_layer_id=self._request.matchdict.get('id'),
                    action='from_wmts')})
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
                 match_param=('table=layers_wmts', 'action=duplicate'),
                 renderer='../templates/edit.jinja2')
    def duplicate(self):
        return super().duplicate()

    @view_config(route_name='layers_wmts_from_wms',
                 request_method='GET')
    def convert(self):
        pk = self._request.matchdict.get('wms_layer_id')
        src = self._request.dbsession.query(LayerWMS).get(pk)
        default_wmts = self._request.dbsession.query(LayerWMTS). \
            filter(LayerWMTS.name == 'wmts-defaults').one()
        if src is None:
            raise HTTPNotFound()
        _dbsession = self._request.dbsession
        with _dbsession.no_autoflush:
            d = delete(LayerWMS.__table__)
            d = d.where(LayerWMS.__table__.c.id == pk)
            _dbsession.execute(d)
            i = insert(LayerWMTS.__table__)
            i = i.values({
                'id': pk,
                'url': default_wmts.url,
                'matrix_set': default_wmts.matrix_set,
                'layer': src.layer,
                'image_type': src.ogc_server.image_type,
                'style': src.style})
            _dbsession.execute(i)
            u = update(TreeItem.__table__)
            u = u.where(TreeItem.__table__.c.id == pk)
            u = u.values({'type': 'l_wmts'})
            _dbsession.execute(u)
            _dbsession.expunge(src)

        _dbsession.flush()
        mark_changed(_dbsession)

        return HTTPFound(self._request.route_url('c2cgeoform_item', action='edit', id=pk))
