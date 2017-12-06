from functools import partial

from c2cgeoform.views.abstract_views import AbstractViews, ListField
from sqlalchemy.orm import subqueryload

from c2cgeoportal_commons.models.main import TreeItem

_list_field = partial(ListField, TreeItem)


class TreeItemViews(AbstractViews):
    _list_fields = [
        _list_field('name'),
        _list_field('metadata_url'),
        _list_field('description')
    ]
    _extra_list_fields = [
        _list_field(
            'parents_relation',
            renderer=lambda layer_wms:', '.join([p.treegroup.name or ''
                                                 for p in layer_wms.parents_relation]))
    ]

    def _base_query(self, query):
        return query. \
            options(subqueryload('parents_relation').joinedload('treegroup'))
