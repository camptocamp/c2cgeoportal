# Copyright (c) 2011-2024, Camptocamp SA
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


import glob
import logging
import os
from typing import Any

import pyramid.request
from bs4 import BeautifulSoup
from pyramid.i18n import TranslationStringFactory
from pyramid.view import view_config

from c2cgeoportal_geoportal.lib.caching import get_region
from c2cgeoportal_geoportal.lib.common_headers import Cache, set_common_headers

_ = TranslationStringFactory("c2cgeoportal")
_LOG = logging.getLogger(__name__)
_CACHE_REGION = get_region("std")


class Entry:
    """All the entry points views."""

    def __init__(self, request: pyramid.request.Request):
        self.request = request

    @view_config(route_name="testi18n", renderer="testi18n.html")  # type: ignore[misc]
    def testi18n(self) -> dict[str, Any]:
        _ = self.request.translate
        return {"title": _("title i18n")}

    def get_ngeo_index_vars(self) -> dict[str, Any]:
        set_common_headers(self.request, "index", Cache.PUBLIC_NO, content_type="text/html")
        # Force urllogin to be converted to cookie when requesting the main HTML page
        self.request.user  # noqa
        return {}

    @staticmethod
    @_CACHE_REGION.cache_on_arguments()
    def get_apijs(api_filename: str, api_name: str | None) -> str:
        with open(api_filename, encoding="utf-8") as api_file:
            api = api_file.read().split("\n")
        sourcemap = api.pop(-1)
        if api_name:
            api += [
                f"if (window.{api_name} === undefined && window.geomapfishapp) {{",
                f"  window.{api_name} = window.geomapfishapp;",
                "}",
            ]
        api.append(sourcemap)

        return "\n".join(api)

    @view_config(route_name="apijs")  # type: ignore
    def apijs(self) -> pyramid.response.Response:
        self.request.response.text = self.get_apijs(
            self.request.registry.settings["static_files"]["api.js"],
            self.request.registry.settings["api"].get("name"),
        )
        set_common_headers(self.request, "api", Cache.PUBLIC, content_type="application/javascript")
        return self.request.response

    def favicon(self) -> dict[str, Any]:
        set_common_headers(self.request, "index", Cache.PUBLIC, content_type="image/vnd.microsoft.icon")
        return {}

    def robot_txt(self) -> dict[str, Any]:
        set_common_headers(self.request, "index", Cache.PUBLIC, content_type="text/plain")
        return {}

    def apijsmap(self) -> dict[str, Any]:
        set_common_headers(self.request, "api", Cache.PUBLIC, content_type="application/octet-stream")
        return {}

    def apicss(self) -> dict[str, Any]:
        set_common_headers(self.request, "api", Cache.PUBLIC, content_type="text/css")
        return {}

    def apihelp(self) -> dict[str, Any]:
        set_common_headers(self.request, "apihelp", Cache.PUBLIC)
        return {}


def _get_ngeo_resources(pattern: str) -> list[str]:
    """Return the list of ngeo dist files matching the pattern."""
    return glob.glob(f"/opt/c2cgeoportal/geoportal/node_modules/ngeo/dist/{pattern}")


def canvas_view(request: pyramid.request.Request, interface_config: dict[str, Any]) -> dict[str, Any]:
    """Get view used as entry point of a canvas interface."""

    js_files = _get_ngeo_resources(f"{interface_config.get('layout', interface_config['name'])}*.js")
    css_files = _get_ngeo_resources(f"{interface_config.get('layout', interface_config['name'])}*.css")
    css = "\n    ".join(
        [
            f'<link href="{request.static_url(css)}" rel="stylesheet" crossorigin="anonymous">'
            for css in css_files
        ]
    )

    set_common_headers(request, "index", Cache.PUBLIC_NO, content_type="text/html")

    spinner = ""
    spinner_filenames = _get_ngeo_resources("spinner*.svg")
    if spinner_filenames:
        with open(spinner_filenames[0], encoding="utf-8") as spinner_file:
            spinner = spinner_file.read()

    return {
        "request": request,
        "header": f"""
<meta name="dynamicUrl" content="{request.route_url("dynamic")}">
<meta name="interface" content="{interface_config['name']}">
{css}""",
        "footer": "\n    ".join(
            [f'<script src="{request.static_url(js)}" crossorigin="anonymous"></script>' for js in js_files]
        ),
        "spinner": spinner,
    }


def custom_view(
    request: pyramid.request.Request, interface_config: dict[str, Any]
) -> pyramid.response.Response:
    """Get view used as entry point of a canvas interface."""

    set_common_headers(request, "index", Cache.PUBLIC_NO, content_type="text/html")

    html_filename = interface_config.get("html_filename", f"{interface_config['name']}.html")
    if not html_filename.startswith("/"):
        html_filename = os.path.join("/etc/static-frontend/", html_filename)

    with open(html_filename, encoding="utf-8") as html_file:
        html = BeautifulSoup(html_file, "html.parser")

    meta = html.find("meta", attrs={"name": "interface"})
    if meta is not None:
        meta["content"] = interface_config["name"]
    meta = html.find("meta", attrs={"name": "dynamicUrl"})
    if meta is not None:
        meta["content"] = request.route_url("dynamic")

    if hasattr(request, "custom_interface_transformer"):
        request.custom_interface_transformer(html, interface_config)

    request.response.text = str(html)

    return request.response
