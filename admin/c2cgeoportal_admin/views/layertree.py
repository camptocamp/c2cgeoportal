from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import Response
from pyramid.view import view_config

from sqlalchemy.orm import subqueryload

from c2cgeoportal_commons.models.main import \
    LayergroupTreeitem, Theme, TreeGroup, TreeItem


class LayerTreeViews():

    def __init__(self, request):
        self._request = request
        self._dbsession = request.dbsession

    @view_config(route_name="layertree",
                 renderer="../templates/layertree.jinja2")
    def index(self):
        # Preload treeitems and treegroups children relations.
        # Note that session.identity_map only keep weak references
        # so we need to keep strong references until the end of rendering.
        groups = self._dbsession.query(TreeGroup). \
            options(subqueryload("children_relation")). \
            all()
        items = self._dbsession.query(TreeItem). \
            all()

        themes = self._dbsession.query(Theme). \
            order_by(Theme.ordering). \
            all()

        return {
            "themes": themes,
            "groups": groups,  # keep strong references
            "items": items,  # keep strong references
            "tables": {
                "theme": "themes",
                "group": "groups",
                "layerv1": "layers_v1",
                "l_wms": "layers_wms",
                "l_wmts": "layers_wmts"
            }
        }

    @view_config(route_name="layertree_unlink",
                 request_method='DELETE')
    def unlink(self):
        group_id = self._request.matchdict.get("group_id")
        item_id = self._request.matchdict.get("item_id")
        link = self._request.dbsession.query(LayergroupTreeitem). \
            filter(LayergroupTreeitem.treegroup_id == group_id). \
            filter(LayergroupTreeitem.treeitem_id == item_id). \
            one_or_none()
        if link is None:
            raise HTTPNotFound()
        self._request.dbsession.delete(link)
        self._request.dbsession.flush()
        return Response('OK')

    @view_config(route_name="layertree_delete",
                 request_method='DELETE')
    def delete(self):
        item_id = self._request.matchdict.get("item_id")
        item = self._request.dbsession.query(TreeItem).get(item_id)
        if item is None:
            raise HTTPNotFound()
        self._request.dbsession.delete(item)
        self._request.dbsession.flush()
        return Response('OK')
