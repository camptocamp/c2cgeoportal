# -*- coding: utf-8 -*-

# Copyright (c) 2011-2020, Camptocamp SA
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
import logging
import os
import subprocess
from time import sleep
from typing import Dict
from urllib.parse import urljoin

import c2cwsgiutils.health_check
import requests

LOG = logging.getLogger(__name__)


def build_url(name, path, request, headers=None):
    """ Build an URL and headers for the checkers """
    base_internal_url = request.registry.settings["checker"]["base_internal_url"]
    url = urljoin(base_internal_url, path)

    forward_host = request.registry.settings["checker"].get("forward_host", False)
    headers = _build_headers(request, headers)
    if forward_host:
        headers["Host"] = request.host

    LOG.debug("%s, URL: %s", name, url)
    return {"url": url, "headers": headers}


def _build_headers(request, headers=None):
    if headers is None:
        headers = {}
    headers["Cache-Control"] = "no-cache"
    settings = request.registry.settings.get("checker", {})
    for header in settings.get("forward_headers", []):
        value = request.headers.get(header)
        if value is not None:
            headers[header] = value
    return headers


def _routes(settings, health_check):
    routes_settings = settings["routes"]
    for route in routes_settings["routes"]:
        if route.get("checker_name", route["name"]) not in routes_settings["disable"]:
            name = "checker_routes_" + route.get("checker_name", route["name"])

            class GetRequest:
                """
                Get the request information about the current route name
                """

                def __init__(self, route_name, type_):
                    self.route_name = route_name
                    self.type = type_

                def __call__(self, request):
                    return build_url("route", request.route_path(self.route_name), request)[self.type]

            health_check.add_url_check(
                url=GetRequest(route["name"], "url"),
                name=name,
                params=route.get("params", None),
                headers=GetRequest(route["name"], "headers"),
                level=route["level"],
                timeout=30,
            )


def _pdf3(settings, health_check):
    print_settings = settings["print"]
    if "spec" not in print_settings:
        return

    def check(request):
        path = request.route_path("printproxy_report_create", format="pdf")
        url_headers = build_url("Check the printproxy request (create)", path, request)

        session = requests.session()
        resp = session.post(json=print_settings["spec"], timeout=30, **url_headers)
        resp.raise_for_status()

        job = resp.json()

        path = request.route_path("printproxy_status", ref=job["ref"])
        url_headers = build_url("Check the printproxy pdf status", path, request)
        done = False
        while not done:
            sleep(1)
            resp = session.get(timeout=30, **url_headers)
            resp.raise_for_status()

            status = resp.json()
            if "error" in status:
                raise Exception("Failed to do the printing: {0!s}".format(status["error"]))
            done = status["done"]

        path = request.route_path("printproxy_report_get", ref=job["ref"])
        url_headers = build_url("Check the printproxy pdf retrieve", path, request)
        resp = session.get(timeout=30, **url_headers)
        resp.raise_for_status()

    health_check.add_custom_check(name="checker_print", check_cb=check, level=print_settings["level"])


def _fts(settings, health_check):
    fts_settings = settings["fulltextsearch"]
    if fts_settings.get("disable", False):
        return

    def get_both(request):
        return build_url("Check the fulltextsearch", request.route_path("fulltextsearch"), request)

    def check(_request, response):
        assert response.json()["features"], "No result"

    health_check.add_url_check(
        name="checker_fulltextsearch",
        url=lambda r: get_both(r)["url"],
        headers=lambda r: get_both(r)["headers"],
        params={"query": fts_settings["search"], "limit": "1"},
        check_cb=check,
        level=fts_settings["level"],
    )


def _themes_errors(settings, health_check):
    from c2cgeoportal_commons.models import DBSession  # pylint: disable=import-outside-toplevel
    from c2cgeoportal_commons.models.main import Interface  # pylint: disable=import-outside-toplevel

    themes_settings = settings["themes"]
    default_params = themes_settings.get("params", {})
    interfaces_settings = themes_settings["interfaces"]

    def check(request):
        path = request.route_path("themes")
        session = requests.session()
        for (interface,) in DBSession.query(Interface.name).all():
            params: Dict[str, str] = {}
            params.update(default_params)
            params.update(interfaces_settings.get(interface, {}).get("params", {}))
            params["interface"] = interface

            interface_url_headers = build_url("checker_themes " + interface, path, request)

            response = session.get(params=params, timeout=120, **interface_url_headers)
            response.raise_for_status()

            result = response.json()
            if result["errors"]:
                raise c2cwsgiutils.health_check.JsonCheckException(
                    "Interface '{}' has error in Theme.".format(interface), result["errors"]
                )

    health_check.add_custom_check(name="checker_themes", check_cb=check, level=themes_settings["level"])


def _lang_files(global_settings, settings, health_check):
    lang_settings = settings["lang"]
    available_locale_names = global_settings["available_locale_names"]

    default_name = global_settings["default_locale_name"]
    assert (
        default_name in available_locale_names
    ), "default_locale_name '{}' not in available_locale_names: {}".format(
        default_name, ", ".join(available_locale_names)
    )

    for type_ in lang_settings.get("files", []):
        for lang in available_locale_names:
            if type_ == "ngeo":
                url = "/etc/geomapfish/static/{lang}.json"
            else:
                raise Exception(
                    "Your language type value '%s' is not valid, " "available values [ngeo]" % type_
                )

            name = "checker_lang_{}_{}".format(type_, lang)

            class GetRequest:
                """
                Get the request information about the current route name
                """

                def __init__(self, name, url, lang, type_):
                    self.name = name
                    self.url = url
                    self.lang = lang
                    self.type = type_

                def __call__(self, request):
                    return build_url(
                        self.name,
                        request.static_path(
                            self.url.format(package=global_settings["package"], lang=self.lang)
                        ),
                        request,
                    )[self.type]

            health_check.add_url_check(
                name=name,
                url=GetRequest(name, url, lang, "url"),
                headers=GetRequest(name, url, lang, "headers"),
                level=lang_settings["level"],
            )


def _phantomjs(settings, health_check):
    phantomjs_settings = settings["phantomjs"]
    for route in phantomjs_settings["routes"]:
        if route.get("checker_name", route["name"]) in phantomjs_settings["disable"]:
            continue

        class _Check:
            def __init__(self, route):
                self.route = route

            def __call__(self, request):
                path = request.route_path(self.route["name"], _query=self.route.get("params", {}))
                url = build_url("Check", path, request)["url"]

                cmd = ["node", "/usr/bin/check-example.js", url]
                env = dict(os.environ)
                for name, value in self.route.get("environment", {}).items():
                    if isinstance(value, (list, dict)):
                        value = json.dumps(value)
                    elif not isinstance(value, str):
                        value = str(value)
                    env[name] = value

                try:
                    subprocess.check_output(cmd, env=env, timeout=70)
                except subprocess.CalledProcessError as exception:
                    raise Exception(
                        "{} exit with code: {}\n{}".format(
                            " ".join(exception.cmd), exception.returncode, exception.output.decode("utf-8")
                        )
                    )
                except subprocess.TimeoutExpired as exception:
                    raise Exception(
                        """Timeout:
command: {}
output:
{}""".format(
                            " ".join(exception.cmd), exception.output.decode("utf-8")
                        )
                    )

        name = "checker_phantomjs_" + route.get("checker_name", route["name"])
        health_check.add_custom_check(name=name, check_cb=_Check(route), level=route["level"])


def init(config, health_check):
    """ Init the ckeckers """
    global_settings = config.get_settings()
    if "checker" not in global_settings:
        return
    settings = global_settings["checker"]
    _routes(settings, health_check)
    _pdf3(settings, health_check)
    _fts(settings, health_check)
    _themes_errors(settings, health_check)
    _lang_files(global_settings, settings, health_check)
    _phantomjs(settings, health_check)
