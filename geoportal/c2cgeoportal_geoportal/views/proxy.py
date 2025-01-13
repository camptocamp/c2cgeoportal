# Copyright (c) 2011-2025, Camptocamp SA
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
from typing import Any

import pyramid.request
import pyramid.response
import requests
from pyramid.httpexceptions import HTTPBadGateway, exception_response

from c2cgeoportal_commons.lib.url import Url
from c2cgeoportal_geoportal.lib.caching import get_region
from c2cgeoportal_geoportal.lib.common_headers import Cache, set_common_headers
from c2cgeoportal_geoportal.views import restrict_headers

_LOG = logging.getLogger(__name__)
_CACHE_REGION = get_region("std")


class Proxy:
    """Some methods used by all the proxy."""

    def __init__(self, request: pyramid.request.Request):
        self.request = request
        self.host_forward_host = request.registry.settings.get("host_forward_host", [])
        self.headers_whitelist = request.registry.settings.get("headers_whitelist", [])
        self.headers_blacklist = request.registry.settings.get("headers_blacklist", [])
        self.http_options = self.request.registry.settings.get("http_options", {})

    def _proxy(
        self,
        url: Url,
        params: dict[str, str] | None = None,
        method: str | None = None,
        cache: bool = False,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> requests.models.Response:
        # Get query string
        params = dict(self.request.params) if params is None else params
        url = url.clone().add_query(params, True)

        _LOG.debug("Send query to URL:\n%s.", url)

        if method is None:
            method = self.request.method

        headers = dict(self.request.headers if headers is None else headers)

        # Forward request to target (without Host Header).
        # The original Host will be added back by pyramid.
        if url.hostname not in self.host_forward_host and "Host" in headers:
            headers.pop("Host")

        # Forward the request tracking ID to the other service. This will allow to follow the logs belonging
        # to a single request coming from the user
        headers.setdefault("X-Request-ID", self.request.c2c_request_id)
        # If we really want to respect the specification, we should chain with the content of the previous
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
        # Set alternative "X-Forwarded" headers
        for forwarded_elements in reversed(headers["Forwarded"].split(",")):
            for element in forwarded_elements.split(";"):
                key, value = element.split("=")
                header_key = f"X-Forwarded-{key.capitalize()}"
                header_value = headers.get(header_key)
                headers[header_key] = value if header_value is None else ", ".join([header_value, value])

        if not cache:
            headers["Cache-Control"] = "no-cache"

        if method in ("POST", "PUT") and body is None:
            body = self.request.body

        headers = restrict_headers(headers, self.headers_whitelist, self.headers_blacklist)

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
                        f"{h}: {v if h not in ('Authorization', 'Cookie') else '***'}"
                        for h, v in list(headers.items())
                    ]
                ),
            ]
            if method in ("POST", "PUT") and body is not None:
                errors += ["--- Query with body ---", "%s"]
                args1.append(body.decode("utf-8"))
            _LOG.exception("\n".join(errors), *args1)

            raise HTTPBadGateway(  # pylint: disable=raise-missing-from
                "Error on backend, See logs for detail"
            )

        if not response.ok:
            errors = [
                "Error '%s' in response of URL:",
                "%s",
                "Status: %d",
                "Method: %s",
                "--- With headers ---",
                "%s",
            ]
            args2: list[str | int] = [
                response.reason,
                url.url(),
                response.status_code,
                method,
                "\n".join(
                    [
                        f"{h}: {v if h not in ('Authorization', 'Cookie') else '***'}"
                        for h, v in list(headers.items())
                    ]
                ),
            ]
            if method in ("POST", "PUT") and body is not None:
                errors += ["--- Query with body ---", "%s"]
                args2.append(body.decode("utf-8"))
            errors += ["--- Return content ---", "%s"]
            args2.append(response.text)
            _LOG.error("\n".join(errors), *args2)

            raise exception_response(response.status_code)
        if not response.headers.get("Content-Type", "").startswith("image/"):
            _LOG.debug("Get result for URL: %s:\n%s.", url, body)

        return response

    @_CACHE_REGION.cache_on_arguments()
    def _proxy_cache(self, host: str, method: str, *args: Any, **kwargs: Any) -> pyramid.response.Response:
        # Method is only for the cache
        del host, method

        kwargs["cache"] = True
        return self._proxy(*args, **kwargs)

    def _proxy_response(
        self,
        service_name: str,
        url: Url,
        headers_update: dict[str, str] | None = None,
        public: bool = False,
        **kwargs: Any,
    ) -> pyramid.response.Response:
        if headers_update is None:
            headers_update = {}
        cache = kwargs.get("cache", False)
        if cache is True:
            response = self._proxy_cache(url, self.request.host, self.request.method, **kwargs)
        else:
            response = self._proxy(url, **kwargs)

        cache_control = (
            (Cache.PUBLIC if public else Cache.PRIVATE)
            if cache
            else (Cache.PUBLIC_NO if public else Cache.PRIVATE_NO)
        )
        return self._build_response(
            response, response.content, cache_control, service_name, headers_update=headers_update
        )

    def _build_response(
        self,
        response: pyramid.response.Response,
        content: bytes,
        cache_control: Cache,
        service_name: str,
        headers: dict[str, str] | None = None,
        headers_update: dict[str, str] | None = None,
        content_type: str | None = None,
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
    def _get_lower_params(params: dict[str, str]) -> dict[str, str]:
        return {k.lower(): str(v).lower() for k, v in params.items()}

    def get_headers(self) -> dict[str, str]:
        headers: dict[str, str] = self.request.headers
        if "Cookie" in headers:
            headers.pop("Cookie")
        if "Authorization" in headers:
            headers.pop("Authorization")
        return headers
