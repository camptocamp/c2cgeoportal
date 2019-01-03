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


import os
import urllib
import httplib
import logging
from json import dumps, loads
from time import sleep
from urlparse import urlsplit, urlunsplit
from subprocess import check_output, CalledProcessError

from pyramid.view import view_config
from pyramid.response import Response

from c2cgeoportal.lib import add_url_params, get_http

log = logging.getLogger(__name__)


def build_url(name, url, request, headers=None):
    if headers is None:
        headers = {}
    headers["Cache-Control"] = "no-cache"

    settings = request.registry.settings.get("checker", {})
    rewrite_as_http_localhost = settings.get("rewrite_as_http_localhost", True)
    log.info("build_url rewrite_as_http_localhost: {}".format(rewrite_as_http_localhost))

    url_ = url
    if rewrite_as_http_localhost:
        urlfragments = urlsplit(url)
        if urlfragments.netloc == request.environ.get("SERVER_NAME") or \
           urlfragments.netloc.startswith("localhost:"):
            url_ = urlunsplit((
                "http", "localhost", urlfragments.path, urlfragments.query, urlfragments.fragment
            ))
            headers["Host"] = urlfragments.netloc

    for header in settings.get("forward_headers", []):
        value = request.headers.get(header)
        if value is not None:
            headers[header] = value

    log.info("{0!s}, URL: {1!s} => {2!s}".format(name, url, url_))
    return url_, headers


class Checker:  # pragma: no cover

    status_int = httplib.OK
    status = httplib.responses[httplib.OK]

    def __init__(self, request):
        self.request = request
        self.settings = self.request.registry.settings["checker"].get("defaults", {})
        type_ = request.params.get("type")
        if type_ is not None:
            self.settings.update(self.request.registry.settings["checker"].get(type_, {}))

    def set_status(self, code, text):
        if int(code) >= self.status_int:
            self.status_int = int(code)
            self.status = text

    def make_response(self, msg):
        return Response(
            body=msg, status="{0:d} {1!s}".format(self.status_int, self.status), cache_control="no-cache"
        )

    def testurl(self, url):
        url, headers = build_url("Check", url, self.request)

        h = get_http(self.request)
        resp, content = h.request(url, headers=headers)

        if resp.status != httplib.OK:
            print(resp.items())
            self.set_status(resp.status, resp.reason)
            return url + "<br/>" + content

        return "OK"

    def testurls(self, named_urls):
        results = [
            "{}: {}".format(name, self.testurl(url))
            for name, url in named_urls
        ]
        return self.make_response(
            "OK" if len(results) == 0 else "\n\n".join(results)
        )

    @view_config(route_name="checker_routes")
    def routes(self):
        named_urls = [
            (
                route["name"],
                add_url_params(
                    self.request.route_url(route["name"]),
                    route.get("params", {}),
                ),
            )
            for route in self.settings["routes"]
            if route["name"] not in self.settings["routes_disable"]
        ]
        return self.testurls(named_urls)

    @view_config(route_name="checker_pdf3")
    def pdf3(self):
        return self.make_response(self._pdf3())

    def _pdf3(self):
        body = dumps(self.settings["print_spec"])

        url = self.request.route_url("printproxy_report_create", format="pdf")
        url, headers = build_url("Check the printproxy request (create)", url, self.request, {
            "Content-Type": "application/json;charset=utf-8",
        })

        h = get_http(self.request)
        resp, content = h.request(url, "POST", headers=headers, body=body)

        if resp.status != httplib.OK:
            self.set_status(resp.status, resp.reason)
            return "Failed creating the print job: " + content

        job = loads(content)
        url = self.request.route_url("printproxy_status", ref=job["ref"])
        url, headers = build_url("Check the printproxy pdf statur", url, self.request)
        done = False
        while not done:
            sleep(1)
            resp, content = h.request(url, headers=headers)
            if resp.status != httplib.OK:
                self.set_status(resp.status, resp.reason)
                return "Failed get the status: " + content

            status = loads(content)
            if "error" in status:
                self.set_status(500, status["error"])
                return "Failed to do the printing: {0!s}".format(status["error"])
            done = status["done"]

        url = self.request.route_url("printproxy_report_get", ref=job["ref"])
        url, headers = build_url("Check the printproxy pdf retrieve", url, self.request)
        resp, content = h.request(url, headers=headers)

        if resp.status != httplib.OK:
            self.set_status(resp.status, resp.reason)
            return "Failed to get the PDF: " + content

        return "OK"

    @view_config(route_name="checker_fts")
    def fts(self):
        return self.make_response(self._fts())

    def _fts(self):
        url = add_url_params(self.request.route_url("fulltextsearch"), {
            "query": self.settings["fulltextsearch"],
            "limit": "1",
        })
        url, headers = build_url("Check the fulltextsearch", url, self.request)

        h = get_http(self.request)
        resp, content = h.request(url, headers=headers)

        if resp.status != httplib.OK:
            self.set_status(resp.status, resp.reason)
            return content

        result = loads(content)

        if len(result["features"]) == 0:
            self.set_status(httplib.BAD_REQUEST, httplib.responses[httplib.BAD_REQUEST])
            return "No result"

        return "OK"

    @view_config(route_name="checker_theme_errors")
    def themes_errors(self):
        from c2cgeoportal.models import DBSession, Interface

        settings = self.settings.get("themes", {})

        url = self.request.route_url("themes")
        h = get_http(self.request)
        default_params = settings.get("default", {}).get("params", {})
        results = []
        for interface, in DBSession.query(Interface.name).all():
            params = {}
            params.update(default_params)
            params.update(settings.get(interface, {}).get("params", {}))
            params["interface"] = interface
            interface_url = add_url_params(url, params)

            interface_url, headers = build_url("Check the theme", interface_url, self.request)

            resp, content = h.request(interface_url, headers=headers)

            if resp.status != httplib.OK:
                self.set_status(resp.status, resp.reason)
                results.append("{}: {}".format(interface, content))

            result = loads(content)

            if len(result["errors"]) != 0:
                self.set_status(500, "Theme with error")

                results.append("Interface '{}': Theme with error\n{}".format(
                    interface,
                    "\n".join(result["errors"])
                ))

        return self.make_response(
            "OK" if len(results) == 0 else urllib.unquote("\n\n".join(results))
        )

    @view_config(route_name="checker_lang_files")
    def checker_lang_files(self):
        available_locale_names = self.request.registry.settings["available_locale_names"]

        if self.request.registry.settings["default_locale_name"] not in available_locale_names:
            self.set_status(500, "default_locale_name not in available_locale_names")

            return self.make_response((
                "Your `default_locale_names` '%s' is not in your "
                "`available_locale_names` '%s'" % (
                    self.request.registry.settings["default_locale_name"],
                    ", ".join(available_locale_names)
                )
            ))

        named_urls = []
        for _type in self.settings.get("lang_files", []):
            for lang in available_locale_names:
                if _type == "cgxp":
                    named_urls.append((
                        "{0!s}-{1!s}".format(_type, lang),
                        self.request.static_url(
                            "{package}:static/build/lang-{lang}.js".format(
                                package=self.request.registry.settings["package"], lang=lang
                            )
                        )
                    ))
                elif _type == "cgxp-api":
                    named_urls.append((
                        "{0!s}-{1!s}".format(_type, lang),
                        self.request.static_url(
                            "{package}:static/build/api-lang-{lang}.js".format(
                                package=self.request.registry.settings["package"], lang=lang
                            )
                        )
                    ))
                elif _type == "ngeo":
                    named_urls.append((
                        "{0!s}-{1!s}".format(_type, lang),
                        self.request.static_url(
                            "{package}:static-ngeo/build/{lang}.json".format(
                                package=self.request.registry.settings["package"], lang=lang
                            )
                        )
                    ))
                else:
                    self.set_status(500, "Unknown lang_files")
                    return self.make_response((
                        "Your language type value '%s' is not valid, "
                        "available values [cgxp, cgxp-api, ngeo]" % (
                            _type
                        )
                    ))
        return self.testurls(named_urls)

    @view_config(route_name="checker_phantomjs")
    def checker_phantomjs(self):
        package = self.request.registry.settings["package"]

        base_path = os.path.dirname(os.path.dirname(
            os.path.abspath(__import__(package).__file__)))

        phantomjs_base_path = "node_modules/.bin/phantomjs"
        executable_path = os.path.join(base_path, phantomjs_base_path)

        checker_config_base_path = "node_modules/ngeo/buildtools/check-example.js"
        checker_config_path = os.path.join(base_path, checker_config_base_path)

        results = []
        for route in self.settings["phantomjs_routes"]:
            url = self.request.route_url(route["name"], _query=route.get("params", {}))
            if urlsplit(url).netloc.startswith("localhost:"):
                # For Docker
                url, _ = build_url("Check", url, self.request)

            cmd = [executable_path, "--local-to-remote-url-access=true", checker_config_path, url]

            # check_output throws a CalledProcessError if return code is > 0
            try:
                check_output(cmd)
                results.append("{}: OK".format(route))
            except CalledProcessError as e:
                results.append("{}: {}".format(route, e.output.replace("\n", "<br/>")))
                self.set_status(500, "{}: JS error".format(route))

        return self.make_response(
            "-" if len(results) == 0 else "<br/><br/>".join(results)
        )
