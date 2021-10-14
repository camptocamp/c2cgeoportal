# Copyright (c) 2018-2021, Camptocamp SA
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


import json
from typing import Any, Dict, List, Optional, cast

import colander
import pyramid.request
from c2cgeoform.schema import GeoFormSchemaNode
from deform.widget import MappingWidget, SelectWidget, SequenceWidget, TextAreaWidget
from sqlalchemy.orm.attributes import InstrumentedAttribute

from c2cgeoportal_admin import _
from c2cgeoportal_commons.lib.validators import url
from c2cgeoportal_commons.models.main import Metadata


@colander.deferred
def metadata_definitions(node, kw):
    """Get the metadata serializable representation."""
    del node
    return {m["name"]: m for m in kw["request"].registry.settings["admin_interface"]["available_metadata"]}


class MetadataSelectWidget(SelectWidget):  # type: ignore
    """
    Extends class SelectWidget to support undefined metadata.

    Override serialize to add option in values for current cstruct when needed.
    """

    def serialize(self, field: Any, cstruct: Any, **kw: Any) -> Any:
        values = kw.get("values", self.values)
        if isinstance(cstruct, str) and (cstruct, cstruct) not in values:
            values = values.copy()
            values.append((cstruct, cstruct))
        kw["values"] = values
        return super().serialize(field, cstruct, **kw)


@colander.deferred  # type: ignore
def metadata_name_widget(node: Any, kw: Dict[str, pyramid.request.Request]) -> MetadataSelectWidget:
    """Widget used to render a metadata."""
    del node
    return MetadataSelectWidget(
        values=[
            (m["name"], m["name"])
            for m in sorted(
                kw["request"].registry.settings["admin_interface"]["available_metadata"],
                key=lambda m: cast(str, m["name"]),
            )
        ]
    )


def json_validator(node, value):
    """Validate the value to be a valid JSON."""
    try:
        json.loads(value)
    except ValueError as e:
        raise colander.Invalid(node, _('Parser report: "{}"').format(str(e)))


def regex_validator(node, value):
    """Validate the value with a regexp."""
    definition = node.metadata_definitions.get(value["name"], {})
    if definition.get("type", "string") == "regex":
        validator = colander.Regex(definition["regex"], msg=_(definition["error_message"]))
        try:
            validator(node["string"], value["string"])
        except colander.Invalid as e:
            error = colander.Invalid(node)
            error.add(e, node.children.index(node["string"]))
            raise error from e


class BooleanMetadata(colander.Boolean):  # type: ignore
    """Boolean metadata values are stored as string in database."""

    def serialize(self, node, appstruct):
        if appstruct == "true":
            appstruct = True
        elif appstruct == "false":
            appstruct = False
        else:
            appstruct = colander.null
        return super().serialize(node, appstruct)

    def deserialize(self, node, cstruct):
        appstruct = super().deserialize(node, cstruct)
        if appstruct is True:
            return "true"
        if appstruct is False:
            return "false"
        return None


class MetadataSchemaNode(GeoFormSchemaNode):  # type: ignore # pylint: disable=abstract-method
    """The metadata schema."""

    metadata_definitions: Optional[Dict[str, Any]] = None

    def __init__(self, *args: Any, **kw: Any):
        super().__init__(*args, **kw)

        self.available_types: List[str] = []

        self._add_value_node("string", colander.String())
        self._add_value_node("liste", colander.String())
        self._add_value_node("boolean", BooleanMetadata())
        self._add_value_node("int", colander.Int())
        self._add_value_node("float", colander.Float())
        self._add_value_node("url", colander.String(), validator=url)
        self._add_value_node(
            "json", colander.String(), widget=TextAreaWidget(rows=10), validator=json_validator
        )

    def _add_value_node(self, type_name: str, colander_type: colander.SchemaType, **kw: Any) -> None:
        self.add_before(
            "description",
            colander.SchemaNode(
                colander_type,
                name=type_name,
                title=Metadata.value.info["colanderalchemy"]["title"],
                description=Metadata.value.info["colanderalchemy"]["description"],
                missing=colander.null,
                **kw,
            ),
        )
        self.available_types.append(type_name)

    def objectify(self, dict_, context=None):
        # depending on the type get the value from the right widget
        dict_["value"] = dict_[self._ui_type(dict_["name"])]
        return super().objectify(dict_, context)

    def dictify(self, obj):
        dict_ = super().dictify(obj)
        value = obj.value or colander.null
        # depending on the type set the value in the right widget
        dict_[self._ui_type(obj.name)] = value
        return dict_

    def _ui_type(self, metadata_name: str) -> str:
        metadata_type = (
            cast(Dict[str, Dict[str, str]], self.metadata_definitions)
            .get(metadata_name, {})
            .get("type", "string")
        )
        return metadata_type if metadata_type in self.available_types else "string"


def metadata_schema_node(prop: InstrumentedAttribute) -> colander.SequenceSchema:
    """Get the schema of the metadata."""
    return colander.SequenceSchema(
        MetadataSchemaNode(
            Metadata,
            name="metadata",
            metadata_definitions=metadata_definitions,
            validator=regex_validator,
            widget=MappingWidget(template="metadata"),
            overrides={"name": {"widget": metadata_name_widget}},
        ),
        name=prop.key,
        title=prop.info["colanderalchemy"]["title"],
        description=prop.info["colanderalchemy"]["description"],
        metadata_definitions=metadata_definitions,
        widget=SequenceWidget(template="metadatas", category="structural"),
    )
