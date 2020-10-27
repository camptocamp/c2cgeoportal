# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020, Camptocamp SA
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


import json
import re
from typing import Dict, List, Union
import urllib.parse

from pyramid.view import view_config
from sqlalchemy import func

from c2cgeoportal_commons import models
from c2cgeoportal_commons.models import main
from c2cgeoportal_geoportal.lib.cacheversion import get_cache_version
from c2cgeoportal_geoportal.lib.caching import NO_CACHE, get_region, set_common_headers

CACHE_REGION = get_region("std")


class DynamicView:
    def __init__(self, request):
        self.request = request
        self.settings = request.registry.settings
        self.interfaces_config = self.settings["interfaces_config"]
        self.default = self.interfaces_config.get("default", {})

    def get(self, value, interface):
        result = dict(self.default.get(value, {}))
        result.update(self.interfaces_config.get(interface, {}).get(value, {}))
        return result

    @CACHE_REGION.cache_on_arguments()
    def _fulltextsearch_groups(self):  # pylint: disable=no-self-use
        return [
            group[0]
            for group in models.DBSession.query(func.distinct(main.FullTextSearch.layer_name))
            .filter(main.FullTextSearch.layer_name.isnot(None))
            .all()
        ]

    def _interface(self, interface_config, interface_name, dynamic, constants):
        constants.update(interface_config.get("constants", {}))
        constants.update(
            {
                name: dynamic[value]
                for name, value in interface_config.get("dynamic_constants", {}).items()
                if value is not None
            }
        )
        constants.update(
            {
                name: self.request.static_url(static_["name"]) + static_.get("append", "")
                for name, static_ in interface_config.get("static", {}).items()
            }
        )

        routes = dict(currentInterfaceUrl={"name": interface_name})
        routes.update(interface_config.get("routes", {}))
        for constant, config in routes.items():
            params: Dict[str, str] = {}
            params.update(config.get("params", {}))
            for name, dyn in config.get("dynamic_params", {}).items():
                params[name] = dynamic[dyn]
            constants[constant] = self.request.route_url(
                config["name"], *config.get("elements", []), _query=params, **config.get("kw", {})
            )

        return constants

    @view_config(route_name="dynamic", renderer="fast_json")
    def dynamic(self):
        interfaces_names = [interface["name"] for interface in self.settings.get("interfaces")]
        default_interfaces_names = [
            interface["name"]
            for interface in self.settings.get("interfaces")
            if interface.get("default", False)
        ]
        assert len(default_interfaces_names) == 1, "More than one default interface in: " + json.dumps(
            self.settings.get("interfaces")
        )
        default_interface_name = default_interfaces_names[0]
        interface_name = self.request.params.get("interface")
        if interface_name not in interfaces_names:
            interface_name = default_interface_name
        interface_config = self.interfaces_config[interface_name]

        dynamic = {
            "interface": interface_name,
            "cache_version": get_cache_version(),
            "two_factor": self.request.registry.settings.get("authentication", {}).get("two_factor", False),
            "lang_urls": {
                lang: self.request.static_url(
                    "/etc/geomapfish/static/{lang}.json".format(lang=lang),
                    _query={"cache": get_cache_version()},
                )
                for lang in self.request.registry.settings["available_locale_names"]
            },
            "fulltextsearch_groups": self._fulltextsearch_groups(),
        }

        constants = self._interface(self.default, interface_name, dynamic, {})
        constants = self._interface(interface_config, interface_name, dynamic, constants)

        do_redirect = False
        url = None
        if "redirect_interface" in interface_config:
            no_redirect_query: Dict[str, Union[str, List[str]]] = {"no_redirect": "t"}
            if "query" in self.request.params:
                query = urllib.parse.parse_qs(self.request.params["query"][1:])
                no_redirect_query.update(query)
            else:
                query = {}
            theme = None
            if "path" in self.request.params:
                match = re.match(".*/theme/(.*)", self.request.params["path"])
                if match is not None:
                    theme = match.group(1)
            if theme is not None:
                no_redirect_url = self.request.route_url(
                    interface_config["redirect_interface"] + "theme", themes=theme, _query=no_redirect_query
                )
                url = self.request.route_url(
                    interface_config["redirect_interface"] + "theme", themes=theme, _query=query
                ).replace("+", "%20")
            else:
                no_redirect_url = self.request.route_url(
                    interface_config["redirect_interface"], _query=no_redirect_query
                )
                url = self.request.route_url(interface_config["redirect_interface"], _query=query).replace(
                    "+", "%20"
                )

            if "no_redirect" in query:
                constants["redirectUrl"] = ""
            else:
                if interface_config.get("do_redirect", False):
                    do_redirect = True
                else:
                    constants["redirectUrl"] = no_redirect_url

        set_common_headers(self.request, "dynamic", NO_CACHE)
        return {"constants": constants, "doRedirect": do_redirect, "redirectUrl": url}
