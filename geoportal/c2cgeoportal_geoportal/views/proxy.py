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


import logging
import sys
from typing import Dict, List, Union
import urllib.parse

from pyramid.httpexceptions import HTTPBadGateway, exception_response
from pyramid.response import Response
import requests

from c2cgeoportal_geoportal.lib.caching import (
    NO_CACHE,
    PRIVATE_CACHE,
    PUBLIC_CACHE,
    get_region,
    set_common_headers,
)

LOG = logging.getLogger(__name__)
CACHE_REGION = get_region("std")


class Proxy:
    def __init__(self, request):
        self.request = request
        self.host_forward_host = request.registry.settings["host_forward_host"]
        self.http_options = self.request.registry.settings.get("http_options", {})

    def _proxy(self, url, params=None, method=None, cache=False, body=None, headers=None):
        # get query string
        params = dict(self.request.params) if params is None else params
        parsed_url = urllib.parse.urlparse(url)
        url_params = urllib.parse.parse_qs(parsed_url.query)
        all_params: Dict[str, Union[str]] = {}
        all_params.update(params)
        all_params.update({k: ",".join(v) for k, v in url_params.items()})
        query_string = urllib.parse.urlencode(all_params)

        if parsed_url.port is None:
            url = "{}://{}{}?{}".format(parsed_url.scheme, parsed_url.hostname, parsed_url.path, query_string)
        else:  # pragma: no cover
            url = "{}://{}:{:d}{}?{}".format(
                parsed_url.scheme, parsed_url.hostname, parsed_url.port, parsed_url.path, query_string
            )

        LOG.debug("Send query to URL:\n%s.", url)

        if method is None:
            method = self.request.method

        if headers is None:  # pragma: no cover
            headers = dict(self.request.headers)

        # Forward request to target (without Host Header)
        if parsed_url.hostname not in self.host_forward_host and "Host" in headers:  # pragma: no cover
            headers.pop("Host")

        # Forward the request tracking ID to the other service. This will allow to follow the logs belonging
        # to a single request coming from the user
        headers.setdefault("X-Request-ID", self.request.c2c_request_id)
        # If we releay want to respect the specification, we should chain with the content of the previus
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

        if method in ("POST", "PUT") and body is None:  # pragma: no cover
            body = self.request.body

        try:
            if method in ("POST", "PUT"):
                response = requests.request(method, url, data=body, headers=headers, **self.http_options)
            else:
                response = requests.request(method, url, headers=headers, **self.http_options)
        except Exception:  # pragma: no cover
            errors = ["Error '%s' while getting the URL:", "%s", "Method: %s", "--- With headers ---", "%s"]
            args1 = [
                sys.exc_info()[0],
                url,
                method,
                "\n".join(["{}: {}".format(*h) for h in list(headers.items())]),
            ]
            if method in ("POST", "PUT"):
                errors += ["--- Query with body ---", "%s"]
                args1.append(body.decode("utf-8"))
            LOG.error("\n".join(errors), *args1, exc_info=True)

            raise HTTPBadGateway("Error on backend, See logs for detail")

        if not response.ok:  # pragma: no cover
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
                url,
                response.status_code,
                method,
                "\n".join(["{}: {}".format(*h) for h in list(headers.items())]),
            ]
            if method in ("POST", "PUT"):
                errors += ["--- Query with body ---", "%s"]
                args2.append(body.decode("utf-8"))
            errors += ["--- Return content ---", "%s"]
            args2.append(response.text)
            LOG.error("\n".join(errors), *args2)

            raise exception_response(response.status_code)

        return response

    @CACHE_REGION.cache_on_arguments()
    def _proxy_cache(self, method, *args, **kwargs):  # pragma: no cover
        # Method is only for the cache
        del method
        kwargs["cache"] = True
        return self._proxy(*args, **kwargs)

    def _proxy_response(
        self, service_name, url, headers_update=None, public=False, **kwargs
    ):  # pragma: no cover
        if headers_update is None:
            headers_update = {}
        cache = kwargs.get("cache", False)
        if cache is True:
            response = self._proxy_cache(url, self.request.method, **kwargs)
        else:
            response = self._proxy(url, **kwargs)

        cache_control = (PUBLIC_CACHE if public else PRIVATE_CACHE) if cache else NO_CACHE
        return self._build_response(
            response, response.content, cache_control, service_name, headers_update=headers_update
        )

    def _build_response(
        self,
        response,
        content,
        cache_control,
        service_name,
        headers=None,
        headers_update=None,
        content_type=None,
    ):
        if isinstance(content, str):
            content = content.encode("utf-8")
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
        ]:  # pragma: no cover
            if header in headers:
                del headers[header]
        # Other problematic headers
        for header in ["Content-Length", "Content-Location", "Content-Encoding"]:  # pragma: no cover
            if header in headers:
                del headers[header]

        headers.update(headers_update)

        response = Response(content, status=response.status_code, headers=headers)

        return set_common_headers(
            self.request, service_name, cache_control, response=response, content_type=content_type
        )

    @staticmethod
    def _get_lower_params(params):
        return dict((k.lower(), str(v).lower()) for k, v in params.items())

    def _get_headers(self):
        headers = self.request.headers
        if "Cookie" in headers:  # pragma: no cover
            headers.pop("Cookie")
        return headers
