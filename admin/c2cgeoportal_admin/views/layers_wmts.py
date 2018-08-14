from functools import partial
from pyramid.view import view_defaults
from pyramid.view import view_config

from sqlalchemy import inspect, insert, delete, update
from zope.sqlalchemy import mark_changed

from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoform.views.abstract_views import ListField, ItemAction
from deform.widget import FormWidget

from c2cgeoportal_admin import _
from c2cgeoportal_admin.schemas.dimensions import dimensions_schema_node
from c2cgeoportal_commons.models.main import \
    LayerWMTS, LayerWMS, LayerGroup, OGCServer, TreeItem
from c2cgeoportal_admin.schemas.metadata import metadatas_schema_node
from c2cgeoportal_admin.schemas.interfaces import interfaces_schema_node
from c2cgeoportal_admin.schemas.restriction_areas import restrictionareas_schema_node
from c2cgeoportal_admin.schemas.treeitem import parent_id_node
from c2cgeoportal_admin.views.dimension_layers import DimensionLayerViews

_list_field = partial(ListField, LayerWMTS)

base_schema = GeoFormSchemaNode(LayerWMTS, widget=FormWidget(fields_template='layer_fields'))
base_schema.add(dimensions_schema_node.clone())
base_schema.add(metadatas_schema_node.clone())
base_schema.add(interfaces_schema_node.clone())
base_schema.add(restrictionareas_schema_node.clone())
base_schema.add_unique_validator(LayerWMTS.name, LayerWMTS.id)
base_schema.add(parent_id_node(LayerGroup))


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
                 renderer='fast_json')
    def grid(self):
        return super().grid()

    def _item_actions(self, item):
        actions = super()._item_actions(item)
        if inspect(item).persistent:
            actions.insert(next((i for i, v in enumerate(actions) if v.name() == 'delete')), ItemAction(
                name='convert_to_wms',
                label=_('Convert to WMS'),
                icon='glyphicon icon-l_wmts',
                url=self._request.route_url(
                    'convert_to_wms',
                    id=getattr(item, self._id_field)),
                method='POST',
                confirmation=_('Are you sure you want to convert this layer to WMS?')))
        return actions

    @view_config(route_name='c2cgeoform_item',
                 request_method='GET',
                 renderer='../templates/edit.jinja2')
    def view(self):
        if self._is_new():
            dbsession = self._request.dbsession
            default_wmts = LayerWMTS.get_default(dbsession)
            if default_wmts:
                return self.copy(default_wmts, excludes=['name', 'layer'])
        return super().edit()

    @view_config(route_name='c2cgeoform_item',
                 request_method='POST',
                 renderer='../templates/edit.jinja2')
    def save(self):
        return super().save()

    @view_config(route_name='c2cgeoform_item',
                 request_method='DELETE',
                 renderer='fast_json')
    def delete(self):
        return super().delete()

    @view_config(route_name='c2cgeoform_item_duplicate',
                 request_method='GET',
                 renderer='../templates/edit.jinja2')
    def duplicate(self):
        return super().duplicate()

    @view_config(route_name='convert_to_wms',
                 request_method='POST',
                 renderer='fast_json')
    def convert_to_wms(self):
        src = self._get_object()
        dbsession = self._request.dbsession
        default_wms = LayerWMS.get_default(dbsession)
        values = {
            'ogc_server_id': default_wms.ogc_server_id,
            'time_mode': default_wms.time_mode,
            'time_widget': default_wms.time_widget
        } if default_wms else {
            'ogc_server_id': dbsession.query(OGCServer.id).order_by(OGCServer.id).first()[0],
            'time_mode': 'disabled',
            'time_widget': 'slider'
        }
        with dbsession.no_autoflush:
            d = delete(LayerWMTS.__table__)
            d = d.where(LayerWMTS.__table__.c.id == src.id)
            i = insert(LayerWMS.__table__)
            values.update({
                'id': src.id,
                'layer': src.layer,
                'style': src.style
            })
            i = i.values(values)
            u = update(TreeItem.__table__)
            u = u.where(TreeItem.__table__.c.id == src.id)
            u = u.values({'type': 'l_wms'})
            dbsession.execute(d)
            dbsession.execute(i)
            dbsession.execute(u)
            dbsession.expunge(src)

        dbsession.flush()
        mark_changed(dbsession)

        return {
            'success': True,
            'redirect': self._request.route_url(
                'c2cgeoform_item',
                table='layers_wms',
                id=self._request.matchdict['id'],
                _query=[('msg_col', 'submit_ok')])
        }
