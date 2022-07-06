# -*- coding: utf-8 -*-

# Copyright (c) 2017-2022, Camptocamp SA
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
import logging
import threading
from typing import Any, Dict, List, cast

from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoform.views.abstract_views import AbstractViews, ItemAction, ListField
from deform.widget import FormWidget
from pyramid.view import view_config, view_defaults
import requests
from sqlalchemy import inspect

from c2cgeoportal_admin import _
from c2cgeoportal_commons.models import cache_invalidate_cb
from c2cgeoportal_commons.models.main import OGCServer

_list_field = partial(ListField, OGCServer)

base_schema = GeoFormSchemaNode(OGCServer, widget=FormWidget(fields_template="ogcserver_fields"))
base_schema.add_unique_validator(OGCServer.name, OGCServer.id)

LOG = logging.getLogger(__name__)


@view_defaults(match_param="table=ogc_servers")
class OGCServerViews(AbstractViews):
    _list_fields = [
        _list_field("id"),
        _list_field("name"),
        _list_field("description"),
        _list_field("url"),
        _list_field("url_wfs"),
        _list_field("type"),
        _list_field("image_type"),
        _list_field("auth"),
        _list_field("wfs_support"),
        _list_field("is_single_tile"),
    ]
    _id_field = "id"
    _model = OGCServer
    _base_schema = base_schema

    @view_config(route_name="c2cgeoform_index", renderer="../templates/index.jinja2")
    def index(self):
        return super().index()

    @view_config(route_name="c2cgeoform_grid", renderer="fast_json")
    def grid(self):
        return super().grid()

    def _item_actions(self, item: OGCServer, readonly: bool = False) -> List[Any]:
        actions = cast(List[Any], super()._item_actions(item, readonly))
        if inspect(item).persistent:
            actions.insert(
                next((i for i, v in enumerate(actions) if v.name() == "delete")),
                ItemAction(
                    name="clear-cache",
                    label=_("Clear the cache"),
                    icon="glyphicon glyphicon-hdd",
                    url=self._request.route_url(
                        "ogc_server_clear_cache",
                        id=getattr(item, self._id_field),
                        _query={
                            "came_from": self._request.current_route_url(),
                        },
                    ),
                    confirmation=_("The current changes will be lost."),
                ),
            )
        return actions

    @view_config(route_name="c2cgeoform_item", request_method="GET", renderer="../templates/edit.jinja2")
    def view(self):
        return super().edit()

    @view_config(route_name="c2cgeoform_item", request_method="POST", renderer="../templates/edit.jinja2")
    def save(self):
        result: Dict[str, Any] = super().save()
        self._update_cache(self._get_object())
        return result

    @view_config(route_name="c2cgeoform_item", request_method="DELETE", renderer="fast_json")
    def delete(self):
        result: Dict[str, Any] = super().delete()
        cache_invalidate_cb()
        return result

    @view_config(
        route_name="c2cgeoform_item_duplicate", request_method="GET", renderer="../templates/edit.jinja2"
    )
    def duplicate(self):
        result: Dict[str, Any] = super().duplicate()
        self._update_cache(self._get_object())
        return result

    def _update_cache(self, ogc_server: OGCServer) -> None:
        try:
            ogc_server_id = ogc_server.id

            def update_cache() -> None:
                response = requests.get(
                    self._request.route_url(
                        "ogc_server_clear_cache",
                        id=ogc_server_id,
                        _query={
                            "came_from": self._request.current_route_url(),
                        },
                    )
                )
                if not response.ok:
                    LOG.error("Error while cleaning the OGC server cache:\n%s", response.text)

            threading.Thread(target=update_cache).start()
        except Exception:
            LOG.error("Error on cleaning the OGC server cache", exc_info=True)
