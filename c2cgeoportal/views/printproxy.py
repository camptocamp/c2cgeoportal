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


import urllib
import logging

import simplejson as json
from simplejson.decoder import JSONDecodeError

from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPBadGateway

from c2cgeoportal.lib.caching import get_region, \
    set_common_headers, NO_CACHE, PRIVATE_CACHE
from c2cgeoportal.lib.functionality import get_functionality
from c2cgeoportal.views.proxy import Proxy

log = logging.getLogger(__name__)
cache_region = get_region()


class PrintProxy(Proxy):  # pragma: no cover

    def __init__(self, request):
        Proxy.__init__(self, request)
        self.config = self.request.registry.settings

    def _get_capabilities_proxy(self, filter_, *args, **kwargs):
        resp, content = self._proxy(*args, **kwargs)

        if self.request.method == "GET":
            if resp.status == 200:
                try:
                    capabilities = json.loads(content)
                except JSONDecodeError as e:
                    # log and raise
                    log.error("Unable to parse capabilities.")
                    log.exception(e)
                    log.error(content)
                    return HTTPBadGateway(content)

                pretty = self.request.params.get("pretty", "false") == "true"
                content = json.dumps(
                    filter_(capabilities), separators=None if pretty else (",", ":"),
                    indent=4 if pretty else None
                )
        else:
            content = ""

        return self._build_response(
            resp, content, PRIVATE_CACHE, "print",
        )

    ##########
    # # V2 # #
    ##########

    @view_config(route_name="printproxy_info")
    def info(self):
        """ Get print capabilities. """

        templates = get_functionality(
            "print_template", self.request
        )

        # get query string
        params = dict(self.request.params)
        query_string = urllib.urlencode(params)

        return self._info(
            templates,
            query_string,
            self.request.method,
        )

    @cache_region.cache_on_arguments()
    def _info(self, templates, query_string, method):
        # get URL
        _url = self.config["print_url"] + "info.json"

        def _filter(capabilities):
            capabilities["layouts"] = list(
                layout for layout in capabilities["layouts"] if
                layout["name"] in templates)
            return capabilities

        return self._get_capabilities_proxy(_filter, _url)

    @view_config(route_name="printproxy_create")
    def create(self):
        """ Create PDF. """
        return self._proxy_response(
            "print",
            "{0!s}create.json".format((
                self.config["print_url"]
            ))
        )

    @view_config(route_name="printproxy_get")
    def get(self):
        """ Get created PDF. """

        resp, content = self._proxy("{0!s}{1!s}.printout".format(
            self.config["print_url"],
            self.request.matchdict.get("file")
        ))

        headers = {}
        if "content-type" in resp:
            headers["content-type"] = resp["content-type"]
        if "content-disposition" in resp:
            headers["content-disposition"] = resp["content-disposition"]

        return set_common_headers(
            self.request, "print", NO_CACHE,
            response=Response(
                content, status=resp.status, headers=headers
            ),
        )

    ##########
    # # V3 # #
    ##########

    @view_config(route_name="printproxy_capabilities")
    def capabilities(self):
        """ Get print capabilities. """

        templates = get_functionality(
            "print_template", self.request
        )

        # get query string
        params = dict(self.request.params)
        query_string = urllib.urlencode(params)

        resp, content = self._capabilities(
            templates,
            query_string,
            self.request.method,
        )

        return self._build_response(
            resp, content, PRIVATE_CACHE, "print",
        )

    @cache_region.cache_on_arguments()
    def _capabilities(self, templates, query_string, method):
        # get URL
        _url = self.config["print_url"] + "/capabilities.json"

        resp, content = self._proxy(_url)

        if self.request.method == "GET":
            if resp.status == 200:
                try:
                    capabilities = json.loads(content)
                except JSONDecodeError as e:
                    # log and raise
                    log.error("Unable to parse capabilities.")
                    log.exception(e)
                    log.error(content)
                    raise HTTPBadGateway(content)

                capabilities["layouts"] = list(
                    layout for layout in capabilities["layouts"] if
                    layout["name"] in templates)

                pretty = self.request.params.get("pretty", "false") == "true"
                content = json.dumps(
                    capabilities, separators=None if pretty else (",", ":"),
                    indent=4 if pretty else None
                )
        else:
            content = ""

        return resp, content

    @view_config(route_name="printproxy_report_create")
    def report_create(self):
        """ Create PDF. """
        return self._proxy_response(
            "print",
            "{0!s}/report.{1!s}".format(
                self.config["print_url"],
                self.request.matchdict.get("format")
            ),
        )

    @view_config(route_name="printproxy_status")
    def status(self):
        """ PDF status. """
        return self._proxy_response(
            "print",
            "{0!s}/status/{1!s}.json".format(
                self.config["print_url"],
                self.request.matchdict.get("ref")
            ),
        )

    @view_config(route_name="printproxy_cancel")
    def cancel(self):
        """ PDF cancel. """
        return self._proxy_response(
            "print",
            "{0!s}/cancel/{1!s}".format(
                self.config["print_url"],
                self.request.matchdict.get("ref")
            ),
        )

    @view_config(route_name="printproxy_report_get")
    def report_get(self):
        """ Get the PDF. """
        return self._proxy_response(
            "print",
            "{0!s}/report/{1!s}".format(
                self.config["print_url"],
                self.request.matchdict.get("ref")
            ),
        )
