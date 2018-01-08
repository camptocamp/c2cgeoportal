import colander
from functools import partial
from sqlalchemy.sql.expression import func, case
from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoportal_commons.models.main import LayergroupTreeitem, TreeItem
from c2cgeoportal_admin.widgets import ChildrenWidget, ChildWidget


class ChildSchemaNode(GeoFormSchemaNode):

    def objectify(self, dict_, context=None):
        if dict_.get('id', None):
            context = self.dbsession.query(LayergroupTreeitem).get(dict_['id'])
        context = super().objectify(dict_, context)
        context.treeitem = self.dbsession.query(TreeItem).get(dict_['treeitem_id'])
        return context


def treeitems(node, kw, only_groups=False):  # pylint: disable=unused-argument
    group = case(
        [(func.count(LayergroupTreeitem.id) == 0, 'Unlinked')],
        else_='Others'
    ).label('group')

    query = kw['request'].dbsession.query(TreeItem, group).distinct(). \
        outerjoin('parents_relation'). \
        filter(TreeItem.item_type != 'theme'). \
        group_by(TreeItem.id). \
        order_by(group.desc(), TreeItem.name)

    if only_groups:
        query = query.filter(TreeItem.item_type == 'group')

    return query


def children_validator(node, cstruct):
    for dict_ in cstruct:
        if not dict_['treeitem_id'] in [item.id for item, group in node.treeitems]:
            raise colander.Invalid(
                'Value {} does not exist in table {}'.
                format(dict_['treeitem_id'], TreeItem.__tablename__))


def children_schema_node(only_groups=False):
    return colander.SequenceSchema(
        ChildSchemaNode(
            LayergroupTreeitem,
            name='layergroup_treeitem',
            widget=ChildWidget()
        ),
        name='children_relation',
        treeitems=colander.deferred(partial(treeitems, only_groups=only_groups)),
        validator=children_validator,
        widget=ChildrenWidget()
    )
