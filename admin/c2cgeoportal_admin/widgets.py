import colander
from colander import Mapping, SchemaNode
from deform import widget
from deform.widget import MappingWidget, SequenceWidget

registry = widget.default_resource_registry
registry.set_js_resources(
    'magicsuggest', None, 'c2cgeoportal_admin:node_modules/magicsuggest-alpine/magicsuggest-min.js'
)
registry.set_css_resources(
    'magicsuggest', None, 'c2cgeoportal_admin:node_modules/magicsuggest-alpine/magicsuggest-min.css'
)


# temporary workaround for https://github.com/Pylons/deform/pull/369
widget.DateTimeInputWidget._pstruct_schema = SchemaNode(  # pylint: disable=protected-access
    Mapping(),
    SchemaNode(widget._StrippedString(), name='date'),  # pylint: disable=protected-access
    SchemaNode(widget._StrippedString(), name='time'),  # pylint: disable=protected-access
    SchemaNode(widget._StrippedString(), name='date_submit', missing=''),  # pylint: disable=protected-access
    SchemaNode(widget._StrippedString(), name='time_submit', missing='')  # pylint: disable=protected-access
)


class ChildWidget(MappingWidget):

    template = 'child'

    def serialize(self, field, cstruct, **kw):
        from c2cgeoportal_commons.models.main import TreeItem
        if cstruct['treeitem_id'] == colander.null:
            kw['treeitem'] = TreeItem()
        else:
            kw['treeitem'] = field.schema.dbsession.query(TreeItem).get(int(cstruct['treeitem_id']))
        return super().serialize(field, cstruct, **kw)


class ThemeOrderWidget(MappingWidget):

    template = 'child'

    def serialize(self, field, cstruct, **kw):
        from c2cgeoportal_commons.models.main import TreeItem
        if cstruct['id'] == colander.null:
            kw['treeitem'] = TreeItem()
        else:
            kw['treeitem'] = field.schema.dbsession.query(TreeItem).get(int(cstruct['id']))
        return super().serialize(field, cstruct, **kw)


class ChildrenWidget(SequenceWidget):

    template = 'children'
    add_subitem = True
    requirements = SequenceWidget.requirements + (('magicsuggest', None),)

    def __init__(self, **kw):
        SequenceWidget.__init__(self, orderable=True, **kw)

    def deserialize(self, field, pstruct):
        for i, dict_ in enumerate(pstruct):
            dict_['ordering'] = str(i)
        return super().deserialize(field, pstruct)

    def serialize(self, field, cstruct, **kw):
        kw['treeitems'] = [
            {
                'id': item.id,
                'name': item.name,
                'item_type': item.item_type,
                'group': group
            } for item, group in field.schema.treeitems]
        return super().serialize(field, cstruct, **kw)
