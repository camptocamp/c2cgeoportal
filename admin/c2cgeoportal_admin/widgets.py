# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020, Camptocamp SA
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.


import colander
from colander import Mapping, SchemaNode
from deform import widget
from deform.widget import MappingWidget, SequenceWidget

registry = widget.default_resource_registry
registry.set_js_resources(
    "magicsuggest", None, "c2cgeoportal_admin:node_modules/magicsuggest-alpine/magicsuggest-min.js"
)
registry.set_css_resources(
    "magicsuggest", None, "c2cgeoportal_admin:node_modules/magicsuggest-alpine/magicsuggest-min.css"
)


# temporary workaround for https://github.com/Pylons/deform/pull/369
widget.DateTimeInputWidget._pstruct_schema = SchemaNode(  # pylint: disable=protected-access
    Mapping(),
    SchemaNode(widget._StrippedString(), name="date"),  # pylint: disable=protected-access
    SchemaNode(widget._StrippedString(), name="time"),  # pylint: disable=protected-access
    SchemaNode(widget._StrippedString(), name="date_submit", missing=""),  # pylint: disable=protected-access
    SchemaNode(widget._StrippedString(), name="time_submit", missing=""),  # pylint: disable=protected-access
)


class ChildWidget(MappingWidget):

    template = "child"

    def serialize(self, field, cstruct, **kw):
        from c2cgeoportal_commons.models.main import TreeItem  # pylint: disable=import-outside-toplevel

        if cstruct["treeitem_id"] == colander.null:
            kw["treeitem"] = TreeItem()
        else:
            kw["treeitem"] = field.schema.dbsession.query(TreeItem).get(int(cstruct["treeitem_id"]))
        return super().serialize(field, cstruct, **kw)


class ThemeOrderWidget(MappingWidget):

    template = "child"

    def serialize(self, field, cstruct, **kw):
        from c2cgeoportal_commons.models.main import TreeItem  # pylint: disable=import-outside-toplevel

        if cstruct["id"] == colander.null:
            kw["treeitem"] = TreeItem()
        else:
            kw["treeitem"] = field.schema.dbsession.query(TreeItem).get(int(cstruct["id"]))
        return super().serialize(field, cstruct, **kw)


class ChildrenWidget(SequenceWidget):

    template = "children"
    add_subitem = True
    requirements = SequenceWidget.requirements + (("magicsuggest", None),)

    def __init__(self, **kw):
        SequenceWidget.__init__(self, orderable=True, **kw)

    def deserialize(self, field, pstruct):
        for i, dict_ in enumerate(pstruct):
            dict_["ordering"] = str(i)
        return super().deserialize(field, pstruct)

    def serialize(self, field, cstruct, **kw):
        kw["treeitems"] = [
            {"id": item.id, "name": item.name, "item_type": item.item_type, "group": group}
            for item, group in field.schema.treeitems
        ]
        return super().serialize(field, cstruct, **kw)
