import colander
from functools import partial
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import func, case
from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoportal_commons.models.main import LayergroupTreeitem, TreeItem
from c2cgeoportal_admin import _
from c2cgeoportal_admin.widgets import ChildrenWidget, ChildWidget


class ChildSchemaNode(GeoFormSchemaNode):

    def objectify(self, dict_, context=None):
        if dict_.get('id', None):
            context = self.dbsession.query(LayergroupTreeitem).get(dict_['id'])
        context = super().objectify(dict_, context)
        context.treeitem = self.dbsession.query(TreeItem).get(dict_['treeitem_id'])
        return context


def treeitems(node, kw, only_groups=False):  # pylint: disable=unused-argument
    dbsession = kw['request'].dbsession

    group = case(
        [(func.count(LayergroupTreeitem.id) == 0, 'Unlinked')],
        else_='Others'
    ).label('group')

    query = dbsession.query(TreeItem, group).distinct(). \
        outerjoin('parents_relation'). \
        filter(TreeItem.item_type != 'theme'). \
        group_by(TreeItem.id). \
        order_by(group.desc(), TreeItem.name)

    # Do not propose ancestors to avoid cycles
    item_id = kw['request'].matchdict['id']
    if item_id != 'new':
        search_ancestors = dbsession.query(LayergroupTreeitem.treegroup_id). \
            filter(LayergroupTreeitem.treeitem_id == item_id). \
            cte(name='ancestors', recursive=True)
        search_alias = aliased(search_ancestors, name='search_ancestors')
        relation_alias = aliased(LayergroupTreeitem, name='relation')
        search_ancestors = search_ancestors.union_all(
            dbsession.query(relation_alias.treegroup_id).
            filter(relation_alias.treeitem_id == search_alias.c.treegroup_id))
        ancestors = dbsession.query(search_ancestors.c.treegroup_id).subquery('ancestors')

        query = query. \
            filter(~TreeItem.id.in_(ancestors)). \
            filter(TreeItem.id != item_id)

    if only_groups:
        query = query.filter(TreeItem.item_type == 'group')

    return query


def children_validator(node, cstruct):
    for dict_ in cstruct:
        if not dict_['treeitem_id'] in [item.id for item, group in node.treeitems]:
            raise colander.Invalid(
                node,
                _('Value {} does not exist in table {} or is not allowed to avoid cycles').
                format(dict_['treeitem_id'], TreeItem.__tablename__))


def base_deferred_parent_id_validator(node, kw, model):  # pylint: disable=unused-argument
    def validator(node, cstruct):
        if kw['dbsession'].query(model).filter(model.id == cstruct).count() == 0:
            raise colander.Invalid(
                node,
                'Value {} does not exist in table {}'.
                format(cstruct, model.__tablename__),
            )
    return validator


def children_schema_node(only_groups=False):
    return colander.SequenceSchema(
        ChildSchemaNode(
            LayergroupTreeitem,
            name='layergroup_treeitem',
            widget=ChildWidget()
        ),
        name='children_relation',
        title=_('Children'),
        treeitems=colander.deferred(partial(treeitems, only_groups=only_groups)),
        validator=children_validator,
        widget=ChildrenWidget(category='structural')
    )
