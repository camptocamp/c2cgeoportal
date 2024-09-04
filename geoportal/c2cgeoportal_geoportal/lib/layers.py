# Copyright (c) 2018-2024, Camptocamp SA
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


from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

import sqlalchemy.orm
from pyramid.request import Request
from sqlalchemy.orm.query import Query

from c2cgeoportal_geoportal.lib import caching, get_roles_id

if TYPE_CHECKING:
    from c2cgeoportal_commons.models import main

CACHE_REGION = caching.get_region("std")


def _get_layers_query(request: Request, what: sqlalchemy.orm.Mapper[Any] | type[Any]) -> Query[Any]:
    from c2cgeoportal_commons.models import DBSession, main  # pylint: disable=import-outside-toplevel

    assert DBSession is not None

    q = DBSession.query(what)
    q = q.join(main.Layer.restrictionareas)
    q = q.join(main.RestrictionArea.roles)
    q = q.filter(main.Role.id.in_(get_roles_id(request)))

    return q


def get_protected_layers_query(
    request: Request,
    ogc_server_ids: Iterable[int] | None,
    what: sqlalchemy.orm.Mapper[Any] | type[Any],
) -> Query[Any]:
    """
    Get the protected layers query.

    Private layers but accessible to the user.
    """
    from c2cgeoportal_commons.models import main  # pylint: disable=import-outside-toplevel

    q = _get_layers_query(request, what)
    q = q.filter(main.Layer.public.is_(False))
    if ogc_server_ids is not None:
        q = q.join(main.LayerWMS.ogc_server)
        q = q.filter(main.OGCServer.id.in_(ogc_server_ids))
    return q


def get_writable_layers_query(request: Request, ogc_server_ids: Iterable[int]) -> Query["main.LayerWMS"]:
    """Get the writable layers query."""
    from c2cgeoportal_commons.models import main  # pylint: disable=import-outside-toplevel

    q = _get_layers_query(request, main.LayerWMS)
    return (
        q.filter(main.RestrictionArea.readwrite.is_(True))
        .join(main.LayerWMS.ogc_server)
        .filter(main.OGCServer.id.in_(ogc_server_ids))
    )


def get_protected_layers(request: Request, ogc_server_ids: Iterable[int]) -> dict[int, "main.LayerWMS"]:
    """
    Get the protected layers.

    Private layers but accessible to the user.
    """
    from c2cgeoportal_commons.models import DBSession, main  # pylint: disable=import-outside-toplevel

    assert DBSession is not None

    q = get_protected_layers_query(request, ogc_server_ids, what=main.LayerWMS)
    results = q.all()
    DBSession.expunge_all()
    return {r.id: r for r in results}


def get_writable_layers(request: Request, ogc_server_ids: Iterable[int]) -> dict[int, "main.LayerWMS"]:
    """Get the writable layers."""
    from c2cgeoportal_commons.models import DBSession  # pylint: disable=import-outside-toplevel

    assert DBSession is not None

    q = get_writable_layers_query(request, ogc_server_ids)
    results = q.all()
    DBSession.expunge_all()
    return {r.id: r for r in results}


@CACHE_REGION.cache_on_arguments()
def get_private_layers(ogc_server_ids: Iterable[int]) -> dict[int, "main.LayerWMS"]:
    """Get the private layers."""
    from c2cgeoportal_commons.models import DBSession, main  # pylint: disable=import-outside-toplevel

    assert DBSession is not None

    q = (
        DBSession.query(main.LayerWMS)
        .filter(main.LayerWMS.public.is_(False))
        .join(main.LayerWMS.ogc_server)
        .filter(main.OGCServer.id.in_(ogc_server_ids))
    )
    results = q.all()
    DBSession.expunge_all()
    return {r.id: r for r in results}
