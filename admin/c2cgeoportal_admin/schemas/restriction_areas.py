# Copyright (c) 2017-2025, Camptocamp SA
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
from c2cgeoform.ext.deform_ext import RelationCheckBoxListWidget
from c2cgeoform.schema import GeoFormManyToManySchemaNode, manytomany_validator
from c2cgeoportal_commons.models.main import RestrictionArea
from sqlalchemy.orm.attributes import InstrumentedAttribute


def restrictionareas_schema_node(
    prop: InstrumentedAttribute[Any],  # pylint: disable=unsubscriptable-object
) -> colander.SequenceSchema:
    """Get the schema of a restriction area."""
    return colander.SequenceSchema(
        GeoFormManyToManySchemaNode(RestrictionArea, None),
        name=prop.key,
        title=prop.info["colanderalchemy"]["title"],
        description=prop.info["colanderalchemy"].get("description"),
        widget=RelationCheckBoxListWidget(
            RestrictionArea,
            "id",
            "name",
            order_by="name",
            edit_url=lambda request, value: request.route_url(
                "c2cgeoform_item",
                table="restriction_areas",
                id=value,
            ),
        ),
        validator=manytomany_validator,
        missing=colander.drop,
    )
