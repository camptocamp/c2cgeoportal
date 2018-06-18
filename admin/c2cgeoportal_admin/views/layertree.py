from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config
from translationstring import TranslationStringFactory

from c2cgeoform.views.abstract_views import ItemAction

from c2cgeoportal_commons.models.main import \
    LayergroupTreeitem, Theme, TreeItem

from c2cgeoportal_admin import _


itemtypes_tables = {
    'theme': 'themes',
    'group': 'layer_groups',
    'layerv1': 'layers_v1',
    'l_wms': 'layers_wms',
    'l_wmts': 'layers_wmts'
}


class LayerTreeViews():

    def __init__(self, request):
        self._request = request
        self._dbsession = request.dbsession

    @view_config(route_name='layertree',
                 renderer='../templates/layertree.jinja2')
    def index(self):
        node_limit = self._request.registry.settings['admin_interface'].get('layer_tree_max_nodes')
        limit_exceeded = self._dbsession.query(LayergroupTreeitem).count() < node_limit
        return {'limit_exceeded': limit_exceeded}

    @view_config(route_name='layertree_children',
                 renderer='fast_json')
    def children(self):
        group_id = self._request.params.get('group_id', None)
        path = self._request.params.get('path', '')

        client_tsf = TranslationStringFactory('{}-client'.format(self._request.registry.package_name))

        if group_id is None:
            items = self._dbsession.query(Theme). \
                order_by(Theme.ordering)
        else:
            items = self._dbsession.query(TreeItem). \
                join(TreeItem.parents_relation). \
                filter(LayergroupTreeitem.treegroup_id == group_id)

        return [
            {
                'id': item.id,
                'item_type': item.item_type,
                'name': item.name,
                'translated_name': self._request.localizer.translate(client_tsf(item.name)),
                'description': item.description,
                'path': '{}_{}'.format(path, item.id),
                'parent_path': path,
                'actions': [
                    action.to_dict(self._request) for action in self._item_actions(item, group_id)
                ]
            } for item in items]

    def _item_actions(self, item, parent_id=None):
        actions = []
        actions.append(ItemAction(
            name='edit',
            label=_('Edit'),
            icon='glyphicon glyphicon-pencil',
            url=self._request.route_url(
                'c2cgeoform_item',
                table=itemtypes_tables[item.item_type],
                id=item.id)))

        if item.item_type in ('theme', 'group'):
            actions.append(ItemAction(
                name='new_layer_group',
                label=_('New layer group'),
                icon='glyphicon glyphicon-plus',
                url='{}?parent_id={}'.format(
                    self._request.route_url(
                        'c2cgeoform_item',
                        table='layer_groups',
                        id='new'),
                    item.id)))

        if item.item_type == 'group':
            actions.append(ItemAction(
                name='new_layer_wms',
                label=_('New WMS layer'),
                icon='glyphicon glyphicon-plus',
                url='{}?parent_id={}'.format(
                    self._request.route_url(
                        'c2cgeoform_item',
                        table='layers_wms',
                        id='new'),
                    item.id)))

            actions.append(ItemAction(
                name='new_layer_wmts',
                label=_('New WMTS layer'),
                icon='glyphicon glyphicon-plus',
                url='{}?parent_id={}'.format(
                    self._request.route_url(
                        'c2cgeoform_item',
                        table='layers_wmts',
                        id='new'),
                    item.id)))

        actions.append(ItemAction(
            name='duplicate',
            label=_('Duplicate'),
            icon='glyphicon glyphicon-duplicate',
            url=self._request.route_url(
                'c2cgeoform_item_duplicate',
                table=itemtypes_tables[item.item_type],
                id=item.id)))

        if parent_id is not None:
            actions.append(ItemAction(
                name='unlink',
                label=_('Unlink'),
                icon='glyphicon glyphicon-log-out',
                url=self._request.route_url(
                    'layertree_unlink',
                    group_id=parent_id,
                    item_id=item.id),
                method='DELETE',
                confirmation=_('Are your sure you want to unlink this record from his parent ?')))

        actions.append(ItemAction(
            name='delete',
            label=_('Delete'),
            icon='glyphicon glyphicon-remove',
            url=self._request.route_url(
                'layertree_delete',
                item_id=item.id),
            method='DELETE',
            confirmation=_('Are your sure you want to delete this record ?')))

        return actions

    @view_config(route_name='layertree_unlink',
                 request_method='DELETE',
                 renderer='fast_json')
    def unlink(self):
        group_id = self._request.matchdict.get('group_id')
        item_id = self._request.matchdict.get('item_id')
        link = self._request.dbsession.query(LayergroupTreeitem). \
            filter(LayergroupTreeitem.treegroup_id == group_id). \
            filter(LayergroupTreeitem.treeitem_id == item_id). \
            one_or_none()
        if link is None:
            raise HTTPNotFound()
        self._request.dbsession.delete(link)
        self._request.dbsession.flush()
        return {
            'success': True,
            'redirect': self._request.route_url('layertree')
        }

    @view_config(route_name='layertree_delete',
                 request_method='DELETE',
                 renderer='fast_json')
    def delete(self):
        item_id = self._request.matchdict.get('item_id')
        item = self._request.dbsession.query(TreeItem).get(item_id)
        if item is None:
            raise HTTPNotFound()
        self._request.dbsession.delete(item)
        self._request.dbsession.flush()
        return {
            'success': True,
            'redirect': self._request.route_url('layertree')
        }
