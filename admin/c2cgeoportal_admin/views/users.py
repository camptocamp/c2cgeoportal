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


import os
from functools import partial

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
from passwordgenerator import pwgenerator
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config, view_defaults
from sqlalchemy.orm import aliased, subqueryload

from c2cgeoportal_admin.schemas.roles import roles_schema_node
from c2cgeoportal_admin.views.logged_views import LoggedViews
from c2cgeoportal_commons.lib.email_ import send_email_config
from c2cgeoportal_commons.models.main import Role
from c2cgeoportal_commons.models.static import Log, User

_list_field = partial(ListField, User)

base_schema = GeoFormSchemaNode(User, widget=FormWidget(fields_template="user_fields"))
base_schema.add(roles_schema_node(User.roles))
base_schema.add_unique_validator(User.username, User.id)

settings_role = aliased(Role)

_OPENID_CONNECT_ENABLED = os.environ.get("OPENID_CONNECT_ENABLED", "false").lower() in ("true", "yes", "1")


@view_defaults(match_param="table=users")
class UserViews(LoggedViews[User]):
    """The admin user view."""

    _list_fields = [
        _list_field("id"),
        *([_list_field("username")] if not _OPENID_CONNECT_ENABLED else []),
        _list_field("display_name"),
        _list_field("email"),
        *(
            [_list_field("last_login"), _list_field("expire_on"), _list_field("deactivated")]
            if not _OPENID_CONNECT_ENABLED
            else []
        ),
        _list_field(
            "settings_role",
            renderer=lambda user: user.settings_role.name if user.settings_role else "",
            sort_column=settings_role.name,
            filter_column=settings_role.name,
        ),
        _list_field(
            "roles",
            renderer=lambda user: ", ".join([r.name or "" for r in user.roles]),
            filter_column=Role.name,
        ),
    ]
    _id_field = "id"
    _model = User
    _base_schema = base_schema
    _log_model = Log
    _name_field = "username"

    def _base_query(self):
        return (
            self._request.dbsession.query(User)
            .distinct()
            .outerjoin(settings_role, settings_role.id == User.settings_role_id)
            .outerjoin(User.roles)
            .options(subqueryload(User.settings_role))
            .options(subqueryload(User.roles))
        )

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
        if self._is_new():
            response = super().save()

            if isinstance(response, HTTPFound):
                password = pwgenerator.generate()

                user = self._obj
                assert user is not None
                user.password = password
                user.is_password_changed = False
                user = self._request.dbsession.merge(user)
                assert user is not None
                self._request.dbsession.flush()

                send_email_config(
                    settings=self._request.registry.settings,
                    email_config_name="welcome_email",
                    email=user.email,
                    user=user.username,
                    password=password,
                    application_url=self._request.route_url("base"),
                    current_url=self._request.current_route_url(),
                )

            return response

        return super().save()

    @view_config(route_name="c2cgeoform_item", request_method="DELETE", renderer="fast_json")  # type: ignore[misc]
    def delete(self) -> DeleteResponse:
        return super().delete()

    @view_config(  # type: ignore[misc]
        route_name="c2cgeoform_item_duplicate", request_method="GET", renderer="../templates/edit.jinja2"
    )
    def duplicate(self) -> ObjectResponse:
        return super().duplicate()
