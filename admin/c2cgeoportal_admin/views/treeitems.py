# pylint: disable=no-self-use

from functools import partial

from c2cgeoform.views.abstract_views import AbstractViews, ListField
from sqlalchemy.orm import subqueryload
from sqlalchemy.sql.functions import concat

from c2cgeoportal_commons.models.main import TreeItem, Metadata

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
                                                 for p in layer_wms.parents_relation])),
        _list_field(
            'metadatas',
            renderer=lambda layers_group: ', '.join(['{}: {}'.format(m.name, m.value) or ''
                                                     for m in layers_group.metadatas]),
            filter_column=concat(Metadata.name, ': ', Metadata.value).label('metadata'))
    ]

    def _base_query(self, query):
        return query. \
            outerjoin('metadatas').\
            options(subqueryload('parents_relation').joinedload('treegroup')). \
            options(subqueryload('metadatas'))
