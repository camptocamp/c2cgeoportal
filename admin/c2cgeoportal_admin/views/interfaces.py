# Copyright (c) 2017-2026, Camptocamp SA
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

import colander
import deform
from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoform.views.abstract_views import (
    DeleteResponse,
    GridResponse,
    IndexResponse,
    ListField,
    ObjectResponse,
    SaveResponse,
)
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config, view_defaults

from c2cgeoportal_admin.views.logged_views import LoggedViews
from c2cgeoportal_commons.models.main import Interface

_list_field = partial(ListField, Interface)

base_schema = GeoFormSchemaNode(Interface)
base_schema.add(
    colander.SchemaNode(
        colander.Integer(),
        name="duplicate_from",
        missing=colander.drop,
        widget=deform.widget.HiddenWidget(),
    ),
)


@view_defaults(match_param="table=interfaces")
class InterfacesViews(LoggedViews[Interface]):
    """The interface administration view."""

    _list_fields = [  # noqa: RUF012
        _list_field("id"),
        _list_field("name"),
        _list_field("description"),
        _list_field(
            "layers",
            renderer=lambda interface: ", ".join([layer.name or "" for layer in interface.layers]),
        ),
        _list_field(
            "theme",
            renderer=lambda interface: ", ".join([f"{t.name}-{t.name}" for t in interface.theme]),
        ),
    ]
    _id_field = "id"
    _model = Interface
    _base_schema = base_schema

    @view_config(route_name="c2cgeoform_index", renderer="../templates/index.jinja2")  # type: ignore[untyped-decorator]
    def index(self) -> IndexResponse[Interface]:
        return super().index()

    @view_config(route_name="c2cgeoform_grid", renderer="fast_json")  # type: ignore[untyped-decorator]
    def grid(self) -> GridResponse:
        return super().grid()

    @view_config(route_name="c2cgeoform_item", request_method="GET", renderer="../templates/edit.jinja2")  # type: ignore[untyped-decorator]
    def view(self) -> ObjectResponse:
        return super().edit()

    @view_config(route_name="c2cgeoform_item", request_method="POST", renderer="../templates/edit.jinja2")  # type: ignore[untyped-decorator]
    def save(self) -> SaveResponse:
        response = super().save()
        if self._is_new() and isinstance(response, HTTPFound):
            self._copy_relations_if_duplicate()
        return response

    def _copy_relations_if_duplicate(self) -> None:
        if self._appstruct is None or self._obj is None:
            return
        duplicate_from = self._appstruct.get("duplicate_from")
        if duplicate_from is None:
            return
        source = self._request.dbsession.query(Interface).get(duplicate_from)
        if source is not None:
            self._obj.layers = list(source.layers)
            self._obj.theme = list(source.theme)
            self._request.dbsession.flush()

    @view_config(route_name="c2cgeoform_item", request_method="DELETE", renderer="fast_json")  # type: ignore[untyped-decorator]
    def delete(self) -> DeleteResponse:
        return super().delete()

    @view_config(  # type: ignore[untyped-decorator]
        route_name="c2cgeoform_item_duplicate",
        request_method="GET",
        renderer="../templates/edit.jinja2",
    )
    def duplicate(self) -> ObjectResponse:
        source = self._get_object()
        response = super().duplicate()
        response["form_render_args"][0]["duplicate_from"] = source.id
        return response
