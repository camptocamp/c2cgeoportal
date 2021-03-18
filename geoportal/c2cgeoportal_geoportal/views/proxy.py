# -*- coding: utf-8 -*-

# Copyright (c) 2011-2021, Camptocamp SA
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
import sys
from typing import Any, Dict, List, Union

import pyramid.request
import pyramid.response
import requests
from pyramid.httpexceptions import HTTPBadGateway, exception_response

from c2cgeoportal_commons.lib.url import Url
from c2cgeoportal_geoportal.lib.caching import Cache, get_region, set_common_headers

LOG = logging.getLogger(__name__)
CACHE_REGION = get_region("std")


class Proxy:
    def __init__(self, request: pyramid.request.Request):
        self.request = request
        self.host_forward_host = request.registry.settings["host_forward_host"]
        self.http_options = self.request.registry.settings.get("http_options", {})

    def _proxy(
        self,
        url: Url,
        params: Dict[str, str] = None,
        method: str = None,
        cache: bool = False,
        body: bytes = None,
        headers: Dict[str, str] = None,
    ) -> pyramid.response.Response:
        # Get query string
        params = dict(self.request.params) if params is None else params
        url = url.clone().add_query(params, True)

        LOG.debug("Send query to URL:\n%s.", url)

        if method is None:
            method = self.request.method

        if headers is None:
            headers = dict(self.request.headers)

        # Forward request to target (without Host Header)
        if url.hostname not in self.host_forward_host and "Host" in headers:
            headers.pop("Host")

        # Forward the request tracking ID to the other service. This will allow to follow the logs belonging
        # to a single request coming from the user
        headers.setdefault("X-Request-ID", self.request.c2c_request_id)
        # If we releay want to respect the specification, we should chain with the content of the previous
        # proxy, see also:
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Forwarded
        forwarded = {"for": self.request.client_addr, "proto": self.request.scheme}
        if "Host" in self.request.headers:
            forwarded["host"] = self.request.headers["Host"]
        forwarded_str = ";".join(["=".join(e) for e in forwarded.items()])
        if "Forwarded" in headers:
            headers["Forwarded"] = ",".join([headers["Forwarded"], forwarded_str])
        else:
            headers["Forwarded"] = forwarded_str

        if not cache:
            headers["Cache-Control"] = "no-cache"

        if method in ("POST", "PUT") and body is None:
            body = self.request.body

        try:
            if method in ("POST", "PUT"):
                response = requests.request(
                    method, url.url(), data=body, headers=headers, **self.http_options
                )
            else:
                response = requests.request(method, url.url(), headers=headers, **self.http_options)
        except Exception:
            errors = ["Error '%s' while getting the URL:", "%s", "Method: %s", "--- With headers ---", "%s"]
            args1 = [
                sys.exc_info()[0],
                url,
                method,
                "\n".join(
                    [
                        "{}: {}".format(h, v if h not in ("Authorization", "Cookies") else "***")
                        for h, v in list(headers.items())
                    ]
                ),
            ]
            if method in ("POST", "PUT") and body is not None:
                errors += ["--- Query with body ---", "%s"]
                args1.append(body.decode("utf-8"))
            LOG.error("\n".join(errors), *args1, exc_info=True)

            raise HTTPBadGateway("Error on backend, See logs for detail")

        if not response.ok:
            errors = [
                "Error '%s' in response of URL:",
                "%s",
                "Status: %d",
                "Method: %s",
                "--- With headers ---",
                "%s",
            ]
            args2: List[Union[str, int]] = [
                response.reason,
                url.url(),
                response.status_code,
                method,
                "\n".join(
                    [
                        "{}: {}".format(h, v if h not in ("Authorization", "Cookies") else "***")
                        for h, v in list(headers.items())
                    ]
                ),
            ]
            if method in ("POST", "PUT") and body is not None:
                errors += ["--- Query with body ---", "%s"]
                args2.append(body.decode("utf-8"))
            errors += ["--- Return content ---", "%s"]
            args2.append(response.text)
            LOG.error("\n".join(errors), *args2)

            raise exception_response(response.status_code)

        return response

    @CACHE_REGION.cache_on_arguments()
    def _proxy_cache(
        self, method: str, *args: Any, **kwargs: Any
    ) -> pyramid.response.Response:
        # Method is only for the cache
        del method
        kwargs["cache"] = True
        return self._proxy(*args, **kwargs)

    def _proxy_response(
        self,
        service_name: str,
        url: Url,
        headers_update: Dict[str, str] = None,
        public: bool = False,
        **kwargs: Any,
    ) -> pyramid.response.Response:
        if headers_update is None:
            headers_update = {}
        cache = kwargs.get("cache", False)
        if cache is True:
            response = self._proxy_cache(url, self.request.method, **kwargs)
        else:
            response = self._proxy(url, **kwargs)

        cache_control = (Cache.PUBLIC if public else Cache.PRIVATE) if cache else Cache.NO
        return self._build_response(
            response, response.content, cache_control, service_name, headers_update=headers_update
        )

    def _build_response(
        self,
        response: pyramid.response.Response,
        content: str,
        cache_control: Cache,
        service_name: str,
        headers: Dict[str, str] = None,
        headers_update: Dict[str, str] = None,
        content_type: str = None,
    ) -> pyramid.response.Response:
        if headers_update is None:
            headers_update = {}
        headers = response.headers if headers is None else headers

        # Hop-by-hop Headers are not supported by WSGI
        # See:
        # https://www.python.org/dev/peps/pep-3333/#other-http-features
        # chapter 13.5.1 at https://www.faqs.org/rfcs/rfc2616.html
        for header in [
            "Connection",
            "Keep-Alive",
            "Proxy-Authenticate",
            "Proxy-Authorization",
            "te",
            "Trailers",
            "Transfer-Encoding",
            "Upgrade",
        ]:
            if header in headers:
                del headers[header]
        # Other problematic headers
        for header in ["Content-Length", "Content-Location", "Content-Encoding"]:
            if header in headers:
                del headers[header]

        headers.update(headers_update)

        response = pyramid.response.Response(content, status=response.status_code, headers=headers)

        return set_common_headers(
            self.request, service_name, cache_control, response=response, content_type=content_type
        )

    @staticmethod
    def _get_lower_params(params: Dict[str, str]) -> Dict[str, str]:
        return dict((k.lower(), str(v).lower()) for k, v in params.items())

    def _get_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = self.request.headers
        if "Cookie" in headers:
            headers.pop("Cookie")
        return headers
