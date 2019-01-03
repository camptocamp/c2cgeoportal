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


import logging
from c2cgeoportal_geoportal.lib import get_setting, get_typed, get_types_map

log = logging.getLogger(__name__)


def _get_config_functionality(name, registered, types, request, errors):
    result = None

    if registered:
        result = get_setting(
            request.registry.settings, ("functionalities", "registered", name)
        )
    if result is None:
        result = get_setting(
            request.registry.settings, ("functionalities", "anonymous", name)
        )

    if result is None:
        result = []
    elif not isinstance(result, list):
        result = [result]

    result = [get_typed(name, r, types, request, errors) for r in result]
    return [r for r in result if r is not None]


def _get_db_functionality(name, role, types, request, errors):
    result = [
        get_typed(name, functionality.value, types, request, errors)
        for functionality in role.functionalities
        if functionality.name == name
    ]
    return [r for r in result if r is not None]


FUNCTIONALITIES_TYPES = None


def get_functionality(name, request):
    global FUNCTIONALITIES_TYPES

    result = []
    errors = set()
    if FUNCTIONALITIES_TYPES is None:
        FUNCTIONALITIES_TYPES = get_types_map(
            request.registry.settings.get("admin_interface", {})
            .get("available_functionalities", [])
        )

    if request.user is not None and request.user.role is not None:
        result = _get_db_functionality(
            name, request.user.role,
            FUNCTIONALITIES_TYPES, request, errors
        )
    if len(result) == 0:
        result = _get_config_functionality(
            name, request.user is not None, FUNCTIONALITIES_TYPES, request, errors
        )

    if errors != set():  # pragma: no cover
        log.error("\n".join(errors))
    return result


def get_mapserver_substitution_params(request):
    params = {}
    mss = get_functionality(
        "mapserver_substitution", request
    )
    if mss:
        for s in mss:
            index = s.find("=")
            if index > 0:
                attribute = "s_" + s[:index]
                value = s[index + 1:]
                if attribute in params:
                    params[attribute] += "," + value
                else:
                    params[attribute] = value
            else:
                log.warning(
                    "Mapserver Substitution '%s' does not "
                    "respect pattern: <attribute>=<value>" % s
                )
    return params
