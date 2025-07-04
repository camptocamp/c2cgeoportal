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


from functools import partial
from typing import cast

import sqlalchemy
from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoform.views.abstract_views import (
    DeleteResponse,
    GridResponse,
    IndexResponse,
    ListField,
    ObjectResponse,
    SaveResponse,
)
from c2cgeoportal_commons.models.main import Functionality, Interface, Role, Theme
from deform.widget import FormWidget
from pyramid.view import view_config, view_defaults
from sqlalchemy.orm import subqueryload
from sqlalchemy.sql.functions import concat

from c2cgeoportal_admin.schemas.functionalities import functionalities_schema_node
from c2cgeoportal_admin.schemas.interfaces import interfaces_schema_node
from c2cgeoportal_admin.schemas.metadata import metadata_schema_node
from c2cgeoportal_admin.schemas.roles import roles_schema_node
from c2cgeoportal_admin.schemas.treegroup import children_schema_node
from c2cgeoportal_admin.views.treeitems import TreeItemViews

_list_field = partial(ListField, Theme)

base_schema = GeoFormSchemaNode(Theme, widget=FormWidget(fields_template="theme_fields"))
base_schema.add(children_schema_node(only_groups=True))
base_schema.add(functionalities_schema_node(Theme.functionalities, Theme))
base_schema.add(roles_schema_node(Theme.restricted_roles))
base_schema.add(interfaces_schema_node(Theme.interfaces))
base_schema.add(metadata_schema_node(Theme.metadatas, Theme))
base_schema.add_unique_validator(Theme.name, Theme.id)


@view_defaults(match_param="table=themes")
class ThemeViews(TreeItemViews[Theme]):
    """The theme administration view."""

    _list_fields = [  # noqa: RUF012
        *TreeItemViews._list_fields,  # type: ignore[misc] # pylint: disable=protected-access # noqa: SLF001
        _list_field("ordering"),
        _list_field("public"),
        _list_field("icon"),
        _list_field(
            "functionalities",
            renderer=lambda themes: ", ".join(
                [
                    f"{f.name}={f.value}"
                    for f in sorted(themes.functionalities, key=lambda f: cast("str", f.name))
                ],
            ),
            filter_column=concat(Functionality.name, "=", Functionality.value),
        ),
        _list_field(
            "restricted_roles",
            renderer=lambda themes: ", ".join([r.name or "" for r in themes.restricted_roles]),
            filter_column=Role.name,
        ),
        _list_field(
            "interfaces",
            renderer=lambda themes: ", ".join(
                [i.name or "" for i in sorted(themes.interfaces, key=lambda i: cast("str", i.name))],
            ),
            filter_column=Interface.name,
        ),
        *TreeItemViews._extra_list_fields_no_parents,  # pylint: disable=protected-access # noqa: SLF001
    ]

    _id_field = "id"
    _model = Theme
    _base_schema = base_schema

    def _base_query(self) -> sqlalchemy.orm.query.Query[Theme]:
        return super()._sub_query(
            self._request.dbsession.query(Theme)
            .distinct()
            .outerjoin(Theme.interfaces)
            .outerjoin(Theme.restricted_roles)
            .outerjoin(Theme.functionalities)
            .options(subqueryload(Theme.functionalities))
            .options(subqueryload(Theme.restricted_roles))
            .options(subqueryload(Theme.interfaces)),
        )

    def _sub_query(self, query: sqlalchemy.orm.query.Query[Theme]) -> sqlalchemy.orm.query.Query[Theme]:
        del query
        return self._base_query()

    @view_config(route_name="c2cgeoform_index", renderer="../templates/index.jinja2")  # type: ignore[misc]
    def index(self) -> IndexResponse[Theme]:
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

    @view_config(  # type: ignore[misc]
        route_name="c2cgeoform_item_duplicate",
        request_method="GET",
        renderer="../templates/edit.jinja2",
    )
    def duplicate(self) -> ObjectResponse:
        return super().duplicate()
