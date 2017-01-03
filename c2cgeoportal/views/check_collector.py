# -*- coding: utf-8 -*-

# Copyright (c) 2012-2017, Camptocamp SA
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
import httplib
from httplib2 import Http
from time import time

from pyramid.view import view_config
from pyramid.response import Response

from c2cgeoportal.views.checker import build_url

log = logging.getLogger(__name__)


class CheckerCollector:  # pragma: no cover

    def __init__(self, request):
        self.status_int = httplib.OK
        self.request = request
        self.settings = request.registry.settings["check_collector"]

    # Method called by the sysadmins to make sure that our app work well.
    # Then this name must not change.
    @view_config(route_name="check_collector")
    def check_collector(self):
        body = ""
        disabled = self.settings["disabled"]
        start0 = time()

        for host in self.settings["hosts"]:
            params = self.request.params
            if "host" not in params or host["display"] == params["host"]:
                check_type = params["type"] if "type" in params else \
                    host["type"] if "type" in host else "default"
                checks = self.settings["check_type"][check_type]
                body += "<h2>{0!s}</h2>".format(host["display"])

                start1 = time()
                for check in checks:
                    if check["name"] in disabled:
                        continue
                    start2 = time()
                    res, err = self._testurl("{}/{}?type={}".format(
                        host["url"], check["name"], check_type
                    ))
                    body += "<p>{0!s}: {1!s} ({2:0.4f}s)</p>".format(check["display"], res, time() - start2)
                    if err:
                        body += "{0!s}<hr/>".format(err)
                body += "<p>Elapsed: {0:0.4f}</p>".format((time() - start1))
        body += "<p>Elapsed all: {0:0.4f}</p>".format((time() - start0))
        return Response(
            body=body, status_int=self.status_int, cache_control="no-cache"
        )

    def _testurl(self, url):
        url, headers = build_url("Collect", url, self.request)

        h = Http()
        resp, content = h.request(url, headers=headers)

        if resp.status != httplib.OK:
            self.status_int = max(self.status_int, resp.status)
            return '<span style="color: red;">{0:d} - {1!s}</span>'.format(
                resp.status, resp.reason
            ), content

        return '<span style="color: green;">{0!s}</span>'.format(content), None
