# Copyright (c) 2017-2024, Camptocamp SA
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


from functools import partial
from typing import Any

import colander
import pyramid.request
from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoform.views.abstract_views import (
    DeleteResponse,
    GridResponse,
    IndexResponse,
    ListField,
    ObjectResponse,
    SaveResponse,
)
from deform.widget import FormWidget
from pyramid.view import view_config, view_defaults

from c2cgeoportal_admin import _
from c2cgeoportal_admin.views.logged_views import LoggedViews
from c2cgeoportal_commons.models.main import Functionality

_list_field = partial(ListField, Functionality)


def _translate_available_functionality(
    available_functionality: dict[str, Any], request: pyramid.request.Request
) -> dict[str, Any]:
    result = {}
    result.update(available_functionality)
    result["description"] = request.localizer.translate(
        _(available_functionality.get("description", "").strip())
    )
    return result


base_schema = GeoFormSchemaNode(
    Functionality,
    widget=FormWidget(fields_template="functionality_fields"),
    functionalities=colander.deferred(
        lambda node, kw: {
            f["name"]: _translate_available_functionality(f, kw["request"])
            for f in kw["request"].registry.settings["admin_interface"]["available_functionalities"]
        },
    ),
)


@view_defaults(match_param="table=functionalities")
class FunctionalityViews(LoggedViews[Functionality]):
    """The functionality administration view."""

    _list_fields = [_list_field("id"), _list_field("name"), _list_field("description"), _list_field("value")]
    _id_field = "id"
    _model = Functionality
    _base_schema = base_schema

    @view_config(route_name="c2cgeoform_index", renderer="../templates/index.jinja2")  # type: ignore[misc]
    def index(self) -> IndexResponse:
        return super().index()

    @view_config(route_name="c2cgeoform_grid", renderer="fast_json")  # type: ignore[misc]
    def grid(self) -> GridResponse:
        return super().grid()

    @view_config(route_name="c2cgeoform_item", request_method="GET", renderer="../templates/edit.jinja2")  # type: ignore[misc]
    def view(self) -> ObjectResponse:
        return super().edit()

    @view_config(route_name="c2cgeoform_item", request_method="POST", renderer="../templates/edit.jinja2")  # type: ignore[misc]
    def save(self) -> SaveResponse:
        return super().save()

    @view_config(route_name="c2cgeoform_item", request_method="DELETE", renderer="fast_json")  # type: ignore[misc]
    def delete(self) -> DeleteResponse:
        return super().delete()

    @view_config(
        route_name="c2cgeoform_item_duplicate", request_method="GET", renderer="../templates/edit.jinja2"  # type: ignore[misc]
    )
    def duplicate(self) -> ObjectResponse:
        return super().duplicate()
