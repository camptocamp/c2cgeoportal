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
from itertools import groupby
from typing import Generic, TypeVar, cast

import sqlalchemy.orm.query
from c2cgeoform.views.abstract_views import ListField
from sqlalchemy.orm import subqueryload

from c2cgeoportal_admin.views.layers import LayerViews
from c2cgeoportal_commons.models.main import DimensionLayer

_list_field = partial(ListField, DimensionLayer)

_T = TypeVar("_T", bound=DimensionLayer)


class DimensionLayerViews(LayerViews[_T], Generic[_T]):
    """The layer with dimensions administration view."""

    _extra_list_fields = [
        _list_field(
            "dimensions",
            renderer=lambda layer_wms: "; ".join(
                [
                    f"{group[0]}: {', '.join([d.value or 'NULL' for d in group[1]])}"
                    for group in groupby(layer_wms.dimensions, lambda d: cast(str, d.name))
                ]
            ),
        )
    ] + LayerViews._extra_list_fields  # pylint: disable=protected-access

    def _sub_query(
        self, query: sqlalchemy.orm.query.Query[DimensionLayer]
    ) -> sqlalchemy.orm.query.Query[DimensionLayer]:
        return super()._sub_query(query.options(subqueryload(DimensionLayer.dimensions)))
