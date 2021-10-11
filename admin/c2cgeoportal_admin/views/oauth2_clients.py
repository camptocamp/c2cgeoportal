# Copyright (c) 2021, Camptocamp SA
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
from typing import Any, Dict

from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoform.views.abstract_views import AbstractViews, ListField
from pyramid.view import view_config, view_defaults

from c2cgeoportal_commons.models.static import OAuth2Client

_list_field = partial(ListField, OAuth2Client)

base_schema = GeoFormSchemaNode(OAuth2Client)
base_schema.add_unique_validator(OAuth2Client.client_id, OAuth2Client.id)


@view_defaults(match_param="table=oauth2_clients")
class OAuth2ClientViews(AbstractViews):  # type: ignore
    """The oAuth2 client administration view."""

    _list_fields = [
        _list_field("id"),
        _list_field("client_id"),
        _list_field("secret"),
        _list_field("redirect_uri"),
    ]
    _id_field = "id"
    _model = OAuth2Client
    _base_schema = base_schema

    def _base_query(self):
        return self._request.dbsession.query(OAuth2Client)

    @view_config(route_name="c2cgeoform_index", renderer="../templates/index.jinja2")  # type: ignore
    def index(self) -> Dict[str, Any]:
        return super().index()  # type: ignore

    @view_config(route_name="c2cgeoform_grid", renderer="fast_json")  # type: ignore
    def grid(self) -> Dict[str, Any]:
        return super().grid()  # type: ignore

    @view_config(  # type: ignore
        route_name="c2cgeoform_item", request_method="GET", renderer="../templates/edit.jinja2"
    )
    def view(self) -> Dict[str, Any]:
        return super().edit()  # type: ignore

    @view_config(  # type: ignore
        route_name="c2cgeoform_item", request_method="POST", renderer="../templates/edit.jinja2"
    )
    def save(self) -> Dict[str, Any]:
        return super().save()  # type: ignore

    @view_config(route_name="c2cgeoform_item", request_method="DELETE", renderer="fast_json")  # type: ignore
    def delete(self) -> Dict[str, Any]:
        return super().delete()  # type: ignore

    @view_config(  # type: ignore
        route_name="c2cgeoform_item_duplicate", request_method="GET", renderer="../templates/edit.jinja2"
    )
    def duplicate(self) -> Dict[str, Any]:
        return super().duplicate()  # type: ignore
