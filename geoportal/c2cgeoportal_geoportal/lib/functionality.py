# -*- coding: utf-8 -*-

# Copyright (c) 2011-2019, Camptocamp SA
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


import logging.config
from typing import Any, Dict, List, Set, Union, cast

from sqlalchemy.orm import joinedload

from c2cgeoportal_commons.models import main, static
from c2cgeoportal_geoportal.lib import get_typed, get_types_map, is_intranet
from c2cgeoportal_geoportal.lib.caching import get_region

LOG = logging.getLogger(__name__)
CACHE_REGION_OBJ = get_region("obj")
CACHE_REGION = get_region("std")


@CACHE_REGION_OBJ.cache_on_arguments()
def _get_role(name: str) -> Dict[str, Any]:
    from c2cgeoportal_commons.models import DBSession  # pylint: disable=import-outside-toplevel

    role = (
        DBSession.query(static.Role)
        .filter(static.Role.name == name)
        .options(joinedload(main.Role.functionalities))
        .one_or_none()
    )
    struct = _role_to_struct(role)
    return {"settings_functionalities": struct, "roles_functionalities": {name: struct}}


def _user_to_struct(user):
    return {
        "settings_functionalities": _role_to_struct(user.settings_role),
        "roles_functionalities": {role.name: _role_to_struct(role) for role in user.roles},
    }


def _role_to_struct(role):
    return [{"name": f.name, "value": f.value} for f in role.functionalities] if role else []


def _get_db_functionality(
    name, user: Dict[str, Any], types, request, errors
) -> List[Union[str, int, float, bool, List[Any], Dict[str, Any]]]:
    if types.get(name, {}).get("single", False):
        values = [
            get_typed(name, functionality["value"], types, request, errors)
            for functionality in user["settings_functionalities"]
            if functionality["name"] == name
        ]
        return [r for r in values if r is not None]
    functionalities = {
        functionality["value"]
        for functionalities in user["roles_functionalities"].values()
        for functionality in functionalities
        if functionality["name"] == name
    }
    values = [
        get_typed(name, functionality_value, types, request, errors)
        for functionality_value in functionalities
    ]

    return [r for r in values if r is not None]


@CACHE_REGION_OBJ.cache_on_arguments()
def _get_functionalities_type(request):
    return get_types_map(
        request.registry.settings.get("admin_interface", {}).get("available_functionalities", [])
    )


def get_functionality(
    name, request, is_intranet_
) -> List[Union[str, int, float, bool, List[Any], Dict[str, Any]]]:
    result: List[Union[str, int, float, bool, List[Any], Dict[str, Any]]] = []
    errors: Set[str] = set()

    if request.user is not None:
        result = _get_db_functionality(
            name, _user_to_struct(request.user), _get_functionalities_type(request), request, errors
        )
        if not result:
            result = _get_db_functionality(
                name, _get_role("registered"), _get_functionalities_type(request), request, errors
            )

    if not result and is_intranet_:
        result = _get_db_functionality(
            name, _get_role("intranet"), _get_functionalities_type(request), request, errors
        )

    if not result:
        result = _get_db_functionality(
            name, _get_role("anonymous"), _get_functionalities_type(request), request, errors
        )

    if errors != set():  # pragma: no cover
        LOG.error("\n".join(errors))
    return result


def get_mapserver_substitution_params(request):
    params: Dict[str, str] = {}
    mss = get_functionality("mapserver_substitution", request, is_intranet(request))
    if mss:
        for s_ in mss:
            s = cast(str, s_)
            index = s.find("=")
            if index > 0:
                attribute = "s_" + s[:index]
                # fmt: off
                value = s[index + 1:]
                # fmt: on
                if attribute in params:
                    params[attribute] += "," + value
                else:
                    params[attribute] = value
            else:
                LOG.warning("Mapserver Substitution '%s' does not " "respect pattern: <attribute>=<value>", s)
    return params
