# Copyright (c) 2023-2024, Camptocamp SA
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

from c2cgeoform import JSONDict
from c2cgeoform.views.abstract_views import AbstractViews, GridResponse, IndexResponse, ItemAction, ListField
from pyramid.view import view_config, view_defaults

from c2cgeoportal_commons.models import _
from c2cgeoportal_commons.models.main import AbstractLog

_list_field = partial(ListField, AbstractLog)


@view_defaults(match_param="table=logs")
class LogViews(AbstractViews[AbstractLog]):
    """The theme administration view."""

    # We pass labels explicitly because actually we are not able to get info
    # from InstrumentedAttribute created from AbstractConcreteBase.
    _list_fields = [
        _list_field("id"),
        _list_field("date", label=_("Date")),
        _list_field("username", label=_("Username")),
        _list_field("action", label=_("Action"), renderer=lambda log: log.action.name),
        _list_field("element_type", label=_("Element type")),
        _list_field("element_id", label=_("Element identifier")),
        _list_field("element_name", label=_("Element name")),
    ]
    _list_ordered_fields = [AbstractLog.date.desc()]

    _id_field = "id"
    _model = AbstractLog

    @view_config(route_name="c2cgeoform_index", renderer="../templates/index.jinja2")  # type: ignore[misc]
    def index(self) -> IndexResponse:
        return super().index()

    @view_config(route_name="c2cgeoform_grid", renderer="fast_json")  # type: ignore[misc]
    def grid(self) -> GridResponse:
        return super().grid()

    def _grid_actions(self):
        return []

    def _grid_item_actions(self, item: AbstractLog) -> JSONDict:
        element_url = self._request.route_url(
            "c2cgeoform_item",
            table=item.element_url_table,
            id=item.element_id,
        )

        return {
            "dblclick": element_url,
            "dropdown": [
                ItemAction(
                    name="edit_element",
                    label=_("Edit element"),
                    icon="glyphicon glyphicon-pencil",
                    url=element_url,
                ).to_dict(self._request)
            ],
        }

    def _item_actions(self, item, readonly=False):
        return []
