# -*- coding: utf-8 -*-

# Copyright (c) 2018-2019, Camptocamp SA
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


import logging
from typing import Any, Dict, List

from c2cwsgiutils import broadcast
from c2cwsgiutils.auth import auth_view
from pympler import asizeof, muppy
from pyramid.view import view_config

from c2cgeoportal_geoportal.views import entry, raster

LOG = logging.getLogger(__name__)


@view_config(route_name="memory", renderer="fast_json")
def memory(request):
    auth_view(request)
    return _memory(
        with_others=request.params.get("with_others", "false").lower() in ["1", "on", "true"],
        with_all=request.params.get("with_all", "false").lower() in ["1", "on", "true"],
        with_repr=request.params.get("with_repr", "false").lower() in ["1", "on", "true"],
    )


@broadcast.decorator(expect_answers=True, timeout=110)
def _memory(with_others: bool, with_all: bool, with_repr: bool) -> Dict[str, Any]:
    wms_capabilities_cache = entry.Entry.server_wms_capabilities
    wfs_feature_type_cache = entry.Entry.server_wfs_feature_type
    raster_data = raster.Raster.data
    result = {
        "parsed_wms_capabilities_cache_by_ogcserver_id": {
            id: _get_size(wms_capabilities_cache[id]) / 1024 / 1024 for id in wms_capabilities_cache
        },
        "parsed_wfs_feature_type_cache_by_ogcserver_id": {
            id: _get_size(wfs_feature_type_cache[id]) / 1024 / 1024 for id in wfs_feature_type_cache
        },
        "raster_data": {
            id: _get_size(raster_data[id]) / 1024 / 1024 for id in raster_data
        },
    }  # type: Dict[str, Any]

    if with_others:
        result['others'] = _get_used_memory(with_all, with_repr)

    return result


def _filter(module_: str, with_all: bool) -> bool:
    return with_all or (
        module_ not in ("builtins", "<unknown>")
        and not module_.startswith("_")
        and not module_.startswith("pkg_resources")
    )


def _get_size(obj: Any) -> int:
    try:
        return asizeof.asizeof(obj)
    except Exception:
        LOG.exception("Unable to get the size")
        return 0


def _order_by_size(elements: Dict[str, Any]) -> List[Dict[str, Any]]:
    for name, elem in elements.items():
        if 'children' in elem:
            elem['children'] = _order_by_size(elem['children'])

    return sorted(elements.values(), key=lambda elem: elem['size'])


def _get_used_memory(with_all: bool, with_repr: bool) -> List[Dict[str, Any]]:
    all_objects = [(
        ".".join((type(o).__module__, type(o).__name__)),
        o,
        _get_size(o)
    ) for o in muppy.get_objects() if _filter(type(o).__module__, with_all)]
    result = {}  # type: Dict[str, Any]
    for name, obj, size in all_objects:
        path = name.split(".")
        _fill_path(result, path, obj, size, with_repr)

    return _order_by_size(result)


def _fill_path(base: Dict[str, Any], path: List[str], object_: Any, size: int, with_repr: bool):
    if len(path) == 1:
        base.setdefault(path[0], {
            "name": path[0],
            "size": 0,
            "numbers": 0,
        })
        obj = base[path[0]]
        obj["size"] += size
        obj["numbers"] += 1
        if with_repr:
            obj.setdefault("objects", [])
            obj["objects"].append((repr(object_), size))
    else:
        base.setdefault(path[0], {
            "name": path[0],
            "size": 0,
            "numbers": 0,
            "children": {},
        })
        obj = base[path[0]]
        obj["size"] += size
        obj["numbers"] += 1
        _fill_path(obj["children"], path[1:], object_, size, with_repr)
