# Copyright (c) 2018-2024, Camptocamp SA
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

from typing import Any

import colander
import pyramid.request
from colander import Mapping, SchemaNode
from deform import widget
from deform.widget import MappingWidget, SequenceWidget

from c2cgeoportal_commons.models.main import TreeItem

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


class ChildWidget(MappingWidget):  # type: ignore
    """
    Extension of the widget ````deform.widget.MappingWidget``.

    To be used in conjunction with ChildrenWidget, to manage n-m relationships.

    Do not embed complete children forms, but just an hidden input for child primary key.

    **Attributes/Arguments**

    input_name (required)
        Form input name namely the name of the schema field identifying the child in the relation.

    model (required)
        The child model class.

    label_field (required)
        The name of the field used for display.

    icon_class (optional)
        A function which takes a child as parameter and returns a CSS class.

    edit_url (optional)
        A function taking request and child as parameter and returning
        an URL to the corresponding resource.

    For further attributes, please refer to the documentation of
    ``deform.widget.MappingWidget`` in the deform documentation:
    <https://deform.readthedocs.org/en/latest/api.html>
    """

    template = "child"
    input_name = "treeitem_id"
    model = TreeItem
    label_field = "name"

    def icon_class(self, child: Any) -> str | None:  # pylint: disable=useless-return
        del child
        return None

    def edit_url(  # pylint: disable=useless-return
        self, request: pyramid.request.Request, child: Any
    ) -> str | None:
        del request
        del child
        return None

    def serialize(self, field, cstruct, **kw):
        if cstruct[self.input_name] == colander.null:
            kw["child"] = self.model()
        else:
            kw["child"] = field.schema.dbsession.query(self.model).get(int(cstruct[self.input_name]))
        return super().serialize(field, cstruct, **kw)


class ChildrenWidget(SequenceWidget):  # type: ignore
    """
    Extension of the widget ````deform.widget.SequenceWidget``.

    To be used in conjunction with ChildWidget, to manage n-m relationships.

    Use Magicsuggest for searching into parent schema candidates property, which should be a list of
    dictionaries of the form:
    {
        "id": "Value to be set in child identifier input (child_input_name)",
        "label": "The text to display in MagicSuggest",
        "icon_class": "An optional icon class for the MagisSuggest entries",
        "edit_url": "An optional url to edit the child resource",
        "group": "An optional group name for grouping entries in MagicSuggest",
    }

    **Attributes/Arguments**

    child_input_name (required)
        The name of the child input to fill with selected child primary key.

    For further attributes, please refer to the documentation of
    ``deform.widget.SequenceWidget`` in the deform documentation:
    <https://deform.readthedocs.org/en/latest/api.html>
    """

    template = "children"
    category = "structural"
    add_subitem = True
    orderable = True
    child_input_name = "treeitem_id"
    requirements = SequenceWidget.requirements + (("magicsuggest", None),)

    def deserialize(self, field, pstruct):
        if self.orderable and pstruct != colander.null:
            for i, dict_ in enumerate(pstruct):
                dict_["ordering"] = str(i)
        return super().deserialize(field, pstruct)

    def serialize(self, field, cstruct, **kw):
        kw["candidates"] = field.schema.candidates
        return super().serialize(field, cstruct, **kw)
