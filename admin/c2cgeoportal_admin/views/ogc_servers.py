# -*- coding: utf-8 -*-

# Copyright (c) 2017-2021, Camptocamp SA
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

from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoform.views.abstract_views import AbstractViews, ItemAction, ListField, UserMessage
from deform.widget import FormWidget
from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config, view_defaults
from sqlalchemy import inspect

from c2cgeoportal_admin import _
from c2cgeoportal_admin.lib.ogcserver_synchronizer import OGCServerSynchronizer
from c2cgeoportal_commons.models.main import OGCServer

_list_field = partial(ListField, OGCServer)

base_schema = GeoFormSchemaNode(OGCServer, widget=FormWidget(fields_template="ogcserver_fields"))
base_schema.add_unique_validator(OGCServer.name, OGCServer.id)


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

    MSG_COL = {
        **AbstractViews.MSG_COL,
        "cannot_delete": UserMessage(
            _("Impossible to delete this server while it contains WMS layers."),
            "alert-danger",
        ),
    }

    @view_config(route_name="c2cgeoform_index", renderer="../templates/index.jinja2")
    def index(self):
        return super().index()

    @view_config(route_name="c2cgeoform_grid", renderer="fast_json")
    def grid(self):
        return super().grid()

    def schema(self):
        try:
            obj = self._get_object()
        except HTTPNotFound:
            obj = None

        schema = self._base_schema.clone()
        schema["url"].description = obj.url_description(self._request)
        schema["url_wfs"].description = obj.url_wfs_description(self._request)
        return schema

    def _item_actions(self, item, readonly=False):
        actions = super()._item_actions(item, readonly)
        if inspect(item).persistent:
            actions.insert(
                next((i for i, v in enumerate(actions) if v.name() == "delete")),
                ItemAction(
                    name="synchronize",
                    label=_("Synchronize"),
                    icon="glyphicon glyphicon-import",
                    url=self._request.route_url("ogcserver_synchronize", id=getattr(item, self._id_field)),
                ),
            )
        return actions

    @view_config(route_name="c2cgeoform_item", request_method="GET", renderer="../templates/edit.jinja2")
    def view(self):
        return super().edit(self.schema())

    @view_config(route_name="c2cgeoform_item", request_method="POST", renderer="../templates/edit.jinja2")
    def save(self):
        return super().save()

    @view_config(route_name="c2cgeoform_item", request_method="DELETE", renderer="fast_json")
    def delete(self):
        obj = self._get_object()
        if len(obj.layers) > 0:
            return {
                "success": True,
                "redirect": self._request.route_url(
                    "c2cgeoform_item",
                    action="edit",
                    id=obj.id,
                    _query=[("msg_col", "cannot_delete")],
                ),
            }
        return super().delete()

    @view_config(
        route_name="c2cgeoform_item_duplicate", request_method="GET", renderer="../templates/edit.jinja2"
    )
    def duplicate(self):
        return super().duplicate()

    @view_config(route_name="ogcserver_synchronize", renderer="../templates/ogcserver_synchronize.jinja2")
    def synchronize(self):
        obj = self._get_object()

        if self._request.method == "GET":
            return {
                "ogcserver": obj,
                "success": None,
                "report": None,
            }

        if self._request.method == "POST":
            synchronizer = OGCServerSynchronizer(self._request, obj)
            if "check" in self._request.params:
                synchronizer.check_layers()
            elif "dry-run" in self._request.params:
                synchronizer.synchronize(dry_run=True)
            elif "synchronize" in self._request.params:
                synchronizer.synchronize()
            return {
                "ogcserver": obj,
                "success": True,
                "report": synchronizer.report(),
            }

        return {}
