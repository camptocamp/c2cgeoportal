from itertools import groupby
from functools import partial

from c2cgeoform.views.abstract_views import ListField
from sqlalchemy.orm import subqueryload

from c2cgeoportal_commons.models.main import DimensionLayer

from c2cgeoportal_admin.views.layers import LayerViews

_list_field = partial(ListField, DimensionLayer)


class DimensionLayerViews(LayerViews):

    _extra_list_fields = [
        _list_field(
            'dimensions',
            renderer=lambda layer_wms: '; '.join(
                ['{}: {}'.format(group[0], ', '.join([d.value or 'NULL' for d in group[1]]))
                 for group in groupby(layer_wms.dimensions, lambda d: d.name)]))
    ] + LayerViews._extra_list_fields

    def _base_query(self, query):
        return super()._base_query(
            query.
            options(subqueryload('dimensions')))
