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

import json
from typing import Any, cast

import colander
import pyramid.request
from c2cgeoform.schema import GeoFormSchemaNode
from deform.widget import MappingWidget, SelectWidget, SequenceWidget, TextAreaWidget
from sqlalchemy import inspect
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.mapper import Mapper

from c2cgeoportal_admin import _
from c2cgeoportal_commons.lib.validators import url
from c2cgeoportal_commons.models.main import Metadata


def get_relevant_for(model: type[Any] | Mapper[Any]) -> set[str]:
    """Return list of relevant_for values for passed class."""
    mapper = inspect(model)
    assert mapper is not None
    relevant_for = {mapper.local_table.name}  # or mapper.polymorphic_identity
    if mapper.inherits:
        relevant_for |= get_relevant_for(mapper.inherits)
    return relevant_for


def metadata_definitions(settings: dict[str, Any], model: type[Any]) -> list[dict[str, Any]]:
    """Return filtered list metadata definitions."""
    return [
        m
        for m in settings["admin_interface"]["available_metadata"]
        if get_relevant_for(model) & set(m.get("relevant_for", ["treeitem"]))
    ]


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


def metadata_name_widget(model: type[Any]) -> colander.deferred:
    """Return a colander deferred which itself returns a widget for the metadata name field."""

    def create_widget(node, kw):
        del node
        return MetadataSelectWidget(
            values=[
                (m["name"], m["name"])
                for m in sorted(
                    metadata_definitions(kw["request"].registry.settings, model),
                    key=lambda m: cast(str, m["name"]),
                )
            ]
        )

    return colander.deferred(create_widget)


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


class MetadataSchemaNode(GeoFormSchemaNode):  # pylint: disable=abstract-method
    """The metadata schema."""

    metadata_definitions: dict[str, Any] | None = None

    def __init__(self, *args: Any, **kw: Any):
        super().__init__(*args, **kw)

        self.available_types: list[str] = []

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
            cast(dict[str, dict[str, str]], self.metadata_definitions)
            .get(metadata_name, {})
            .get("type", "string")
        )
        return metadata_type if metadata_type in self.available_types else "string"


def _translate_available_metadata(
    available_metadata: dict[str, Any], request: pyramid.request.Request
) -> dict[str, Any]:
    result = {}
    result.update(available_metadata)
    result["description"] = request.localizer.translate(_(available_metadata.get("description", "").strip()))
    return result


def metadata_schema_node(prop: InstrumentedAttribute[Any], model: type[Any]) -> colander.SequenceSchema:
    """Get the schema of a collection of metadata."""

    # Deferred which returns a dictionary with metadata name as key and metadata definition as value.
    # Needed to get the metadata types on UI side.
    metadata_definitions_dict = colander.deferred(
        lambda node, kw: {
            m["name"]: _translate_available_metadata(m, kw["request"])
            for m in metadata_definitions(kw["request"].registry.settings, model)
        }
    )

    return colander.SequenceSchema(
        MetadataSchemaNode(
            Metadata,
            name="metadata",
            metadata_definitions=metadata_definitions_dict,
            validator=regex_validator,
            widget=MappingWidget(template="metadata"),
            overrides={"name": {"widget": metadata_name_widget(model)}},
        ),
        name=prop.key,
        title=prop.info["colanderalchemy"]["title"],
        description=prop.info["colanderalchemy"]["description"],
        metadata_definitions=metadata_definitions_dict,
        widget=SequenceWidget(template="metadatas", category="structural"),
    )
