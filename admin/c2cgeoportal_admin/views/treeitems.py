# pylint: disable=no-self-use

from functools import partial

from c2cgeoform.views.abstract_views import AbstractViews, ListField
from sqlalchemy.orm import subqueryload
from sqlalchemy.sql.functions import concat
from pyramid.view import view_config

from c2cgeoportal_commons.models.main import TreeItem, Metadata, \
    LayergroupTreeitem, TreeGroup

_list_field = partial(ListField, TreeItem)


class TreeItemViews(AbstractViews):
    _list_fields = [
        _list_field('id'),
        _list_field('name'),
        _list_field('metadata_url'),
        _list_field('description')
    ]

    _extra_list_fields_no_parents = [
        _list_field(
            'metadatas',
            renderer=lambda layers_group: ', '.join(['{}: {}'.format(m.name, m.value) or ''
                                                     for m in layers_group.metadatas]),
            filter_column=concat(Metadata.name, ': ', Metadata.value).label('metadata'))
    ]
    _extra_list_fields = [
        _list_field(
            'parents_relation',
            renderer=lambda layer_wms:', '.join(
                [p.treegroup.name or '' for p in sorted(
                    layer_wms.parents_relation,
                    key=lambda p: p.treegroup.name or '')]))] + _extra_list_fields_no_parents

    @view_config(route_name='c2cgeoform_item',
                 request_method='POST',
                 renderer='../templates/edit.jinja2')
    def save(self):
        response = super().save()
        # correctly handles the validation error as if there is a validation error, cstruct is empty
        has_to_be_registred_in_parent = (hasattr(self, '_appstruct') and
                                         self._appstruct is not None and
                                         self._appstruct.get('parent_id'))
        if has_to_be_registred_in_parent:
            parent = self._request.dbsession.query(TreeGroup).get(has_to_be_registred_in_parent)
            rel = LayergroupTreeitem(parent, self._obj, 100)
            self._request.dbsession.add(rel)
        return response

    def _base_query(self, query):
        return query. \
            outerjoin('metadatas').\
            options(subqueryload('parents_relation').joinedload('treegroup')). \
            options(subqueryload('metadatas'))
