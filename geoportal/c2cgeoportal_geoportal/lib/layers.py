# -*- coding: utf-8 -*-

# Copyright (c) 2018, Camptocamp SA
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


from c2cgeoportal_geoportal.lib import caching


cache_region = caching.get_region()


def _get_layers_query(role_id, what):
    from c2cgeoportal_commons.models import DBSession, main

    q = DBSession.query(what)
    q = q.join(main.Layer.restrictionareas)
    q = q.join(main.RestrictionArea.roles)
    q = q.filter(main.Role.id == role_id)

    return q


def get_protected_layers_query(role_id, ogc_server_ids, what=None, version=1):
    from c2cgeoportal_commons.models import main

    q = _get_layers_query(role_id, what)
    q = q.filter(main.Layer.public.is_(False))
    if version == 2 and ogc_server_ids is not None:
        q = q.join(main.LayerWMS.ogc_server)
        q = q.filter(main.OGCServer.id.in_(ogc_server_ids))
    return q


def get_writable_layers_query(role_id, ogc_server_ids):
    from c2cgeoportal_commons.models import main

    q = _get_layers_query(role_id, main.LayerWMS)
    return q \
        .filter(main.RestrictionArea.readwrite.is_(True)) \
        .join(main.LayerWMS.ogc_server) \
        .filter(main.OGCServer.id.in_(ogc_server_ids))


@cache_region.cache_on_arguments()
def get_protected_layers(role_id, ogc_server_ids):
    from c2cgeoportal_commons.models import DBSession, main

    q = get_protected_layers_query(role_id, ogc_server_ids, what=main.LayerWMS, version=2)
    results = q.all()
    DBSession.expunge_all()
    return {r.id: r for r in results}


@cache_region.cache_on_arguments()
def get_writable_layers(role_id, ogc_server_ids):
    from c2cgeoportal_commons.models import DBSession

    q = get_writable_layers_query(role_id, ogc_server_ids)
    results = q.all()
    DBSession.expunge_all()
    return {r.id: r for r in results}


@cache_region.cache_on_arguments()
def get_private_layers(ogc_server_ids):
    from c2cgeoportal_commons.models import DBSession, main

    q = DBSession.query(main.LayerWMS) \
        .filter(main.LayerWMS.public.is_(False)) \
        .join(main.LayerWMS.ogc_server) \
        .filter(main.OGCServer.id.in_(ogc_server_ids))
    results = q.all()
    DBSession.expunge_all()
    return {r.id: r for r in results}
