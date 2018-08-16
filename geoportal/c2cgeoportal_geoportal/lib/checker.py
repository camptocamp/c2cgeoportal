# -*- coding: utf-8 -*-

# Copyright (c) 2011-2017, Camptocamp SA
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

import requests
import logging
import subprocess
from time import sleep
from urllib.parse import urlsplit, urlunsplit

log = logging.getLogger(__name__)


def build_url(name, url, request, headers=None):
    url_fragments = urlsplit(url)
    headers = _build_headers(request, headers)
    if url_fragments.netloc == request.environ.get("SERVER_NAME") or \
            url_fragments.netloc.startswith("localhost:"):
        url_ = urlunsplit((
            "http", "localhost", url_fragments.path, url_fragments.query, url_fragments.fragment
        ))
        headers["Host"] = url_fragments.netloc
    else:
        url_ = url

    log.debug("%s, URL: %s => %s", name, url, url_)
    return {"url": url_, "headers": headers}


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
        if route["name"] not in routes_settings["disable"]:
            name = "checker_routes_" + route.get("display_name", route["name"])

            def get_both(request):
                return build_url("route", request.route_url(route["name"]), request)

            health_check.add_url_check(
                url=lambda r: get_both(r)["url"],
                name=name,
                params=route.get("params", None),
                headers=lambda r: get_both(r)["headers"],
                level=route["level"],
                timeout=30,
            )


def _pdf3(settings, health_check):
    print_settings = settings["print"]

    def check(request):
        url = request.route_url("printproxy_report_create", format="pdf")
        url_headers = build_url("Check the printproxy request (create)", url, request)

        session = requests.session()
        resp = session.post(
            json=print_settings["spec"],
            timeout=30,
            **url_headers
        )
        resp.raise_for_status()

        job = resp.json()

        url = request.route_url("printproxy_status", ref=job["ref"])
        url_headers = build_url("Check the printproxy pdf status", url, request)
        done = False
        while not done:
            sleep(1)
            resp = session.get(
                timeout=30,
                **url_headers
            )
            resp.raise_for_status()

            status = resp.json()
            if "error" in status:
                raise Exception("Failed to do the printing: {0!s}".format(status["error"]))
            done = status["done"]

        url = request.route_url("printproxy_report_get", ref=job["ref"])
        url_headers = build_url("Check the printproxy pdf retrieve", url, request)
        resp = session.get(
            timeout=30,
            **url_headers
        )
        resp.raise_for_status()

    health_check.add_custom_check(name="checker_print", check_cb=check, level=print_settings["level"])


def _fts(settings, health_check):
    fts_settings = settings["fulltextsearch"]

    def get_both(request):
        return build_url("Check the fulltextsearch", request.route_url("fulltextsearch"), request)

    def check(_request, response):
        if response.json()["features"] == 0:
            raise Exception("No result")

    health_check.add_url_check(
        name="checker_fulltextsearch",
        url=lambda r: get_both(r)["url"],
        headers=lambda r: get_both(r)["headers"],
        params={
            "query": fts_settings["search"],
            "limit": "1",
        },
        check_cb=check,
    )


def _themes_errors(settings, health_check):
    from c2cgeoportal_commons.models import DBSession
    from c2cgeoportal_commons.models.main import Interface

    themes_settings = settings["themes"]
    default_params = themes_settings.get("params", {})
    interfaces_settings = themes_settings["interfaces"]

    def check(request):
        url = request.route_url("themes")
        session = requests.session()
        for interface, in DBSession.query(Interface.name).all():
            params = {}
            params.update(default_params)
            params.update(interfaces_settings.get(interface, {}).get("params", {}))
            params["interface"] = interface

            interface_url_headers = build_url("checker_themes " + interface, url, request)

            response = session.get(
                params=params,
                timeout=120,
                **interface_url_headers
            )
            response.raise_for_status()

            result = response.json()
            if len(result["errors"]) != 0:
                raise Exception("Interface '{}': Theme with error\n{}".format(
                    interface, "\n".join(result["errors"])))

    health_check.add_custom_check(name="checker_themes", check_cb=check, level=themes_settings["level"])


def _lang_files(global_settings, settings, health_check):
    lang_settings = settings["lang"]
    available_locale_names = global_settings["available_locale_names"]

    default_name = global_settings["default_locale_name"]
    if default_name not in available_locale_names:
        raise Exception("default_locale_name '%s' not in available_locale_names: %s" %
                        (default_name, ", ".join(available_locale_names)))

    for type_ in lang_settings.get("files", []):
        for lang in available_locale_names:
            if type_ == "cgxp":
                url = "{package}_geoportal:static/build/lang-{lang}.js"
            elif type_ == "cgxp-api":
                url = "{package}_geoportal:static/build/api-lang-{lang}.js"
            elif type_ == "ngeo":
                url = "{package}_geoportal:static-ngeo/build/{lang}.json"
            else:
                raise Exception("Your language type value '%s' is not valid, "
                                "available values [cgxp, cgxp-api, ngeo]" % type_)
            name = "checker_lang_{}_{}".format(type_, lang)

            def get_both(request):
                return build_url(
                    name,
                    request.static_url(url.format(package=global_settings["package"], lang=lang)),
                    request)

            health_check.add_url_check(
                name=name,
                url=lambda r: get_both(r)["url"],
                headers=lambda r: get_both(r)["headers"],
                level=lang_settings["level"],
            )


def _phantomjs(settings, health_check):
    phantomjs_settings = settings["phantomjs"]
    for route in phantomjs_settings["routes"]:
        if route["name"] in phantomjs_settings["disable"]:
            continue

        def check(request):
            url = request.route_url(route["name"], _query=route.get("params", {}))
            if urlsplit(url).netloc.startswith("localhost:"):
                # For Docker
                url = build_url("Check", url, request)["url"]

            cmd = [
                "phantomjs", "--local-to-remote-url-access=true",
                "/usr/lib/node_modules/ngeo/buildtools/check-example.js", url
            ]

            try:
                subprocess.check_output(cmd, timeout=10)
            except subprocess.CalledProcessError as e:
                raise Exception(e.output.decode("utf-8"))
            except subprocess.TimeoutExpired as e:
                raise Exception("""Timeout:
command: {}
output:
{}""".format(" ".join(e.cmd), e.output.decode("utf-8")))
        name = "checker_phantomjs_" + route.get("display_name", route["name"])
        health_check.add_custom_check(name=name, check_cb=check, level=route["level"])


def init(config, health_check):
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
