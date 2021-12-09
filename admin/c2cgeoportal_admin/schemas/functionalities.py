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


from typing import Any, Dict, List

import colander
from c2cgeoform.ext.deform_ext import RelationCheckBoxListWidget
from c2cgeoform.schema import GeoFormManyToManySchemaNode, manytomany_validator
from sqlalchemy import inspect, select
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.sql.functions import concat

from c2cgeoportal_commons.models.main import Functionality


def available_functionalities_for(settings: Dict[str, Any], model: DeclarativeMeta) -> List[Dict[str, Any]]:
    """Return filtered list of functionality definitions."""
    mapper = inspect(model)
    relevant_for = {mapper.local_table.name}
    return [
        f
        for f in settings["admin_interface"]["available_functionalities"]
        if relevant_for & set(f.get("relevant_for", relevant_for))
    ]


def functionalities_widget(model: DeclarativeMeta) -> colander.deferred:
    """Return a colander deferred which itself returns a widget for the functionalities field."""

    def create_widget(node, kw):
        del node

        return RelationCheckBoxListWidget(
            select(
                [
                    Functionality.id,
                    concat(Functionality.name, "=", Functionality.value).label("label"),
                ]
            )
            .where(
                Functionality.name.in_(
                    [f["name"] for f in available_functionalities_for(kw["request"].registry.settings, model)]
                )
            )
            .alias("functionality_labels"),
            "id",
            "label",
            order_by="label",
            edit_url=lambda request, value: request.route_url(
                "c2cgeoform_item", table="functionalities", id=value
            ),
        )

    return colander.deferred(create_widget)


def functionalities_schema_node(
    prop: InstrumentedAttribute, model: DeclarativeMeta
) -> colander.SequenceSchema:
    """Get the schema of the functionalities."""

    return colander.SequenceSchema(
        GeoFormManyToManySchemaNode(Functionality),
        name=prop.key,
        title=prop.info["colanderalchemy"]["title"],
        description=prop.info["colanderalchemy"].get("description"),
        widget=functionalities_widget(model),
        validator=manytomany_validator,
        missing=colander.drop,
    )
