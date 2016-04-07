# -*- coding: utf-8 -*-

# Copyright (c) 2011-2016, Camptocamp SA
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


import httplib
import logging
from httplib2 import Http
from json import dumps, loads
from time import sleep
from urlparse import urlsplit, urlunsplit

from pyramid.view import view_config
from pyramid.response import Response

from c2cgeoportal.lib import add_url_params

log = logging.getLogger(__name__)


def build_url(name, url, request, headers=None):
    if headers is None:
        headers = {}
    headers["Cache-Control"] = "no-cache"

    urlfragments = urlsplit(url)
    if urlfragments.netloc == request.environ.get("SERVER_NAME"):
        url_ = urlunsplit((
            "http", "localhost", urlfragments.path, urlfragments.query, urlfragments.fragment
        ))
        headers["Host"] = urlfragments.netloc
    else:
        url_ = url

    settings = request.registry.settings.get("checker", {})
    for header in settings.get("forward_headers", []):
        value = request.headers.get(header)
        if value is not None:
            headers[header] = value

    log.info("%s, URL: %s => %s" % (name, url, url_))
    return url_, headers


class Checker(object):  # pragma: no cover

    status_int = httplib.OK
    status = httplib.responses[httplib.OK]

    def __init__(self, request):
        self.request = request
        self.settings = self.request.registry.settings["checker"]

    def set_status(self, code, text):
        if int(code) >= self.status_int:
            self.status_int = int(code)
            self.status = text

    def make_response(self, msg):
        return Response(
            body=msg, status="%i %s" % (self.status_int, self.status), cache_control="no-cache"
        )

    def testurl(self, url):
        url, headers = build_url("Check", url, self.request)

        h = Http()
        resp, content = h.request(url, headers=headers)

        if resp.status != httplib.OK:
            print(resp.items())
            self.set_status(resp.status, resp.reason)
            return url + "<br/>" + content

        return "OK"

    @view_config(route_name="checker_main")
    def main(self):
        url = self.request.route_url("home")
        return self.make_response(self.testurl(url))

    @view_config(route_name="checker_viewer")
    def viewer(self):
        url = self.request.route_url("viewer")
        return self.make_response(self.testurl(url))

    @view_config(route_name="checker_edit")
    def edit(self):
        url = self.request.route_url("edit")
        return self.make_response(self.testurl(url))

    @view_config(route_name="checker_edit_js")
    def edit_js(self):
        url = self.request.route_url("edit.js")
        return self.make_response(self.testurl(url))

    @view_config(route_name="checker_api")
    def api_js(self):
        url = self.request.route_url("apijs")
        return self.make_response(self.testurl(url))

    @view_config(route_name="checker_xapi")
    def xapi_js(self):
        url = self.request.route_url("xapijs")
        return self.make_response(self.testurl(url))

    @view_config(route_name="checker_printcapabilities")
    def printcapabilities(self):
        url = self.request.route_url("printproxy_info")
        return self.make_response(self.testurl(url))

    @view_config(route_name="checker_print3capabilities")
    def print3capabilities(self):
        url = self.request.route_url("printproxy_capabilities")
        return self.make_response(self.testurl(url))

    @view_config(route_name="checker_pdf")
    def pdf(self):
        return self.make_response(self._pdf())

    def _pdf(self):
        body = {
            "comment": "Foobar",
            "title": "Bouchon",
            "units": "m",
            "srs": "EPSG:%i" % self.request.registry.settings["srid"],
            "dpi": 254,
            "layers": [],
            "layout": self.settings["print_template"],
            "pages": [{
                "center": [self.settings["print_center_lon"], self.settings["print_center_lat"]],
                "col0": "",
                "rotation": 0,
                "scale": self.settings["print_scale"],
                "table": {
                    "columns": ["col0"],
                    "data": [{
                        "col0": ""
                    }]
                }
            }]
        }
        body = dumps(body)

        url = add_url_params(self.request.route_url("printproxy_create"), {
            "url": self.request.route_url("printproxy"),
        })
        url, headers = build_url("Check the printproxy request (create)", url, self.request, {
            "Content-Type": "application/json;charset=utf-8",
        })

        h = Http()
        resp, content = h.request(url, "POST", headers=headers, body=body)

        if resp.status != httplib.OK:
            self.set_status(resp.status, resp.reason)
            return "Failed creating PDF: " + content

        json = loads(content)
        url, headers = build_url(
            "Check the printproxy pdf (retrieve)", json["getURL"], self.request
        )

        resp, content = h.request(url, headers=headers)

        if resp.status != httplib.OK:
            self.set_status(resp.status, resp.reason)
            return "Failed retrieving PDF: " + content

        return "OK"

    @view_config(route_name="checker_pdf3")
    def pdf3(self):
        return self.make_response(self._pdf3())

    def _pdf3(self):
        body = dumps(self.settings["print_spec"])

        url = self.request.route_url("printproxy_report_create", format="pdf")
        url, headers = build_url("Check the printproxy request (create)", url, self.request, {
            "Content-Type": "application/json;charset=utf-8",
        })

        h = Http()
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
                return "Failed to do the printing: %s" % status["error"]
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

        h = Http()
        resp, content = h.request(url, headers=headers)

        if resp.status != httplib.OK:
            self.set_status(resp.status, resp.reason)
            return content

        result = loads(content)

        if len(result["features"]) == 0:
            self.set_status(httplib.BAD_REQUEST, httplib.responses[httplib.BAD_REQUEST])
            return "No result"

        return "OK"

    @view_config(route_name="checker_wmscapabilities")
    def wmscapabilities(self):
        url = add_url_params(self.request.route_url("mapserverproxy"), {
            "SERVICE": "WMS",
            "VERSION": "1.1.1",
            "REQUEST": "GetCapabilities",
        })
        return self.make_response(self.testurl(url))

    @view_config(route_name="checker_wfscapabilities")
    def wfscapabilities(self):
        url = add_url_params(self.request.route_url("mapserverproxy"), {
            "SERVICE": "WFS",
            "VERSION": "1.1.0",
            "REQUEST": "GetCapabilities",
        })
        return self.make_response(self.testurl(url))

    @view_config(route_name="checker_theme_errors")
    def themes_errors(self):
        from c2cgeoportal.models import DBSession, Interface

        settings = self.settings.get("themes", {})

        url = self.request.route_url("themes")
        h = Http()
        default_params = settings.get("default", {}).get("params", {})
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
                return self.make_response(content)

            result = loads(content)

            if len(result["errors"]) != 0:
                self.set_status(500, "Theme with error")

                return self.make_response("Theme with error for interface '%s'\n%s" % (
                    Interface.name,
                    "\n".join(result["errors"])
                ))

        return self.make_response("OK")

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

        result = []
        for _type in self.settings.get("lang_files", []):
            for lang in available_locale_names:
                if _type == "cgxp":
                    url = self.request.static_url(
                        "{package}:static/build/lang-{lang}.js".format(
                            package=self.request.registry.settings["package"], lang=lang
                        )
                    )
                elif _type == "cgxp-api":
                    url = self.request.static_url(
                        "{package}:static/build/api-lang-{lang}.js".format(
                            package=self.request.registry.settings["package"], lang=lang
                        )
                    )
                elif _type == "ngeo":
                    url = self.request.static_url(
                        "{package}:static-ngeo/build/{lang}.json".format(
                            package=self.request.registry.settings["package"], lang=lang
                        )
                    )
                else:
                    self.set_status(500, "Unknown lang_files")
                    return self.make_response((
                        "Your language type value '%s' isn't valid, "
                        "available values [cgxp, cgxp-api, ngeo]" % (
                            _type
                        )
                    ))
                result.append(self.testurl(url))
        return self.make_response(
            "OK" if len(result) == 0 else "\n\n".join(result)
        )

    @view_config(route_name="checker_js_generic")
    def js_generic(self):
        from subprocess import check_output, CalledProcessError
        import os
        import urllib

        package = self.request.registry.settings["package"]

        base_path = os.path.dirname(os.path.dirname(
            os.path.abspath(__import__(package).__file__)))

        phantomjs_base_path = "node_modules/.bin/phantomjs"
        executable_path = os.path.join(base_path, phantomjs_base_path)

        checker_config_base_path = "node_modules/ngeo/buildtools/check-example.js"
        checker_config_path = os.path.join(base_path, checker_config_base_path)

        url = self.request.route_url("mobile")

        args = [executable_path, "--local-to-remote-url-access=true", checker_config_path, url]

        log_message = ""
        # check_output throws a CalledProcessError if return code is > 0
        try:
            check_output(args)
        except CalledProcessError as e:
            log_message = e.output

        return self.make_response(
            "OK" if len(log_message) == 0 else urllib.unquote(log_message)
        )
