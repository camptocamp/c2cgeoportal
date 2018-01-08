from functools import partial

from c2cgeoform.views.abstract_views import ListField
from sqlalchemy.orm import subqueryload

from c2cgeoportal_commons.models.main import Layer, Interface
from c2cgeoportal_admin.views.treeitems import TreeItemViews

_list_field = partial(ListField, Layer)


class LayerViews(TreeItemViews):

    _list_fields = TreeItemViews._list_fields + [
        _list_field('public'),
        _list_field('geo_table'),
        _list_field('exclude_properties')]

    _extra_list_fields = [
        _list_field(
            'interfaces',
            renderer=lambda layer_wms: ', '.join(
                [i.name or '' for i in sorted(layer_wms.interfaces, key=lambda i: i.name)]),
            sort_column=Interface.name,
            filter_column=Interface.name),
        _list_field(
            'restrictionareas',
            renderer=lambda layer_wms: ', '.join(
                [r.name or '' for r in sorted(layer_wms.restrictionareas, key=lambda r: r.name)]))] + \
        TreeItemViews._extra_list_fields

    def _base_query(self, query):
        return super()._base_query(
            query.
            outerjoin('interfaces').
            options(subqueryload('interfaces')).
            options(subqueryload('restrictionareas')))
