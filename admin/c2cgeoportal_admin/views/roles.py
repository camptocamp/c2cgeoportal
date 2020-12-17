# -*- coding: utf-8 -*-

# Copyright (c) 2017-2020, Camptocamp SA
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
from c2cgeoform.schema import GeoFormManyToManySchemaNode, GeoFormSchemaNode
from c2cgeoform.views.abstract_views import AbstractViews, ListField
from deform.widget import FormWidget
from pyramid.view import view_config, view_defaults
from sqlalchemy.orm import subqueryload

from c2cgeoportal_admin import _
from c2cgeoportal_admin.schemas.functionalities import functionalities_schema_node
from c2cgeoportal_admin.schemas.restriction_areas import restrictionareas_schema_node
from c2cgeoportal_admin.widgets import ChildrenWidget, ChildWidget
from c2cgeoportal_commons.models.main import Role
from c2cgeoportal_commons.models.static import User

_list_field = partial(ListField, Role)

base_schema = GeoFormSchemaNode(Role, widget=FormWidget(fields_template="role_fields"))
base_schema.add_before("extent", functionalities_schema_node.clone())
base_schema.add_before("extent", restrictionareas_schema_node.clone())
base_schema.add_unique_validator(Role.name, Role.id)


def users(node, kw):  # pylint: disable=unused-argument
    dbsession = kw["request"].dbsession
    query = dbsession.query(User).order_by(User.username)
    return [
        {
            "id": user.id,
            "label": user.username,
            "icon_class": "icon-user",
            "edit_url": kw["request"].route_url(
                "c2cgeoform_item",
                table="users",
                id=user.id,
            ),
            "group": "All",
        }
        for user in query
    ]


base_schema.add(
    colander.SequenceSchema(
        GeoFormManyToManySchemaNode(
            User,
            name="layer",
            includes=["id"],
            widget=ChildWidget(
                input_name="id",
                model=User,
                label_field="username",
                icon_class=lambda user: "icon-user",
                edit_url=lambda request, user: request.route_url(
                    "c2cgeoform_item",
                    table="users",
                    id=user.id,
                ),
            ),
        ),
        name="users",
        title=_("Users"),
        candidates=colander.deferred(users),
        widget=ChildrenWidget(child_input_name="id", orderable=False, category="structural"),
    )
)


@view_defaults(match_param="table=roles")
class RoleViews(AbstractViews):
    _list_fields = [
        _list_field("id"),
        _list_field("name"),
        _list_field("description"),
        _list_field(
            "functionalities",
            renderer=lambda role: ", ".join(["{}={}".format(f.name, f.value) for f in role.functionalities]),
        ),
        _list_field(
            "restrictionareas", renderer=lambda role: ", ".join([r.name or "" for r in role.restrictionareas])
        ),
    ]
    _id_field = "id"
    _model = Role
    _base_schema = base_schema

    def _base_query(self):
        return (
            self._request.dbsession.query(Role)
            .options(subqueryload("functionalities"))
            .options(subqueryload("restrictionareas"))
        )

    @view_config(route_name="c2cgeoform_index", renderer="../templates/index.jinja2")
    def index(self):
        return super().index()

    @view_config(route_name="c2cgeoform_grid", renderer="fast_json")
    def grid(self):
        return super().grid()

    @view_config(route_name="c2cgeoform_item", request_method="GET", renderer="../templates/edit.jinja2")
    def view(self):
        return super().edit()

    @view_config(route_name="c2cgeoform_item", request_method="POST", renderer="../templates/edit.jinja2")
    def save(self):
        return super().save()

    @view_config(route_name="c2cgeoform_item", request_method="DELETE", renderer="fast_json")
    def delete(self):
        return super().delete()

    @view_config(
        route_name="c2cgeoform_item_duplicate", request_method="GET", renderer="../templates/edit.jinja2"
    )
    def duplicate(self):
        return super().duplicate()
