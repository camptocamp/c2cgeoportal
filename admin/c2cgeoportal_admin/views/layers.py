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
from typing import Generic, TypeVar, cast

import sqlalchemy
import sqlalchemy.orm.query
from c2cgeoform.views.abstract_views import ListField
from sqlalchemy.orm import subqueryload

from c2cgeoportal_admin.views.treeitems import TreeItemViews
from c2cgeoportal_commons.models.main import Interface, Layer

_list_field = partial(ListField, Layer)

_T = TypeVar("_T", bound=Layer)


class LayerViews(TreeItemViews[_T], Generic[_T]):
    """The layer administration view."""

    _list_fields = TreeItemViews._list_fields + [  # type: ignore[misc] # pylint: disable=protected-access
        _list_field("public"),
        _list_field("geo_table"),
        _list_field("exclude_properties"),
    ]

    _extra_list_fields = [
        _list_field(
            "interfaces",
            renderer=lambda layer_wms: ", ".join(
                [i.name or "" for i in sorted(layer_wms.interfaces, key=lambda i: cast(str, i.name))]
            ),
            sort_column=Interface.name,
            filter_column=Interface.name,
        ),
        _list_field(
            "restrictionareas",
            renderer=lambda layer_wms: ", ".join(
                [r.name or "" for r in sorted(layer_wms.restrictionareas, key=lambda r: cast(str, r.name))]
            ),
        ),
    ] + TreeItemViews._extra_list_fields  # pylint: disable=protected-access

    def _sub_query(self, query: sqlalchemy.orm.query.Query[Layer]) -> sqlalchemy.orm.query.Query[Layer]:
        return super()._sub_query(
            query.outerjoin(Layer.interfaces)
            .options(subqueryload(Layer.interfaces))
            .options(subqueryload(Layer.restrictionareas))
        )
