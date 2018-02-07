from functools import partial
from pyramid.view import view_defaults
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound

from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoform.views.abstract_views import ListField

from c2cgeoportal_commons.models.main import LayerWMTS, LayerWMS
from c2cgeoportal_admin.views.dimension_layers import DimensionLayerViews
from c2cgeoportal_admin.schemas.dimension import dimensions_schema_node
from c2cgeoportal_admin.schemas.metadata import metadatas_schema_node
from c2cgeoportal_admin.views.interfaces import interfaces_schema_node
from c2cgeoportal_admin.views.restrictionareas import restrictionareas_schema_node

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
                 request_method='GET',
                 renderer='../templates/edit.jinja2')
    def convert(self):
        pk = self._request.matchdict.get('wms_layer_id')
        src = self._request.dbsession.query(LayerWMS).get(pk)
        if src is None:
            raise HTTPNotFound()

        form = self._form(
            action=self._request.route_url(
                'c2cgeoform_item',
                id='new',
                table='layers_wmts'))

        with self._request.dbsession.no_autoflush:
            dest = self.copy_members_if_duplicates(src, dest=LayerWMTS())
            # TODO, please set the default value from settings
            dest.url = 'www.default_server.com'
            dest.image_type = src.ogc_server.image_type
            dict_ = form.schema.dictify(dest)
            self._request.dbsession.expunge_all()

        self._populate_widgets(form.schema)

        rendered = form.render(dict_,
                               request=self._request,
                               actions=self._item_actions())
        return {
            'form': rendered,
            'deform_dependencies': form.get_widget_resources()
        }
