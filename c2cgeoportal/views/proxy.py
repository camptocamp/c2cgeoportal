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


import sys
import httplib2
import urllib
import logging

from cStringIO import StringIO
from urlparse import urlparse, parse_qs

from pyramid.response import Response
from pyramid.httpexceptions import HTTPBadGateway, HTTPInternalServerError

from c2cgeoportal.lib.caching import get_region, \
    set_common_headers, NO_CACHE, PUBLIC_CACHE, PRIVATE_CACHE

log = logging.getLogger(__name__)
cache_region = get_region()


class Proxy:

    def __init__(self, request):
        self.request = request
        self.host_forward_host = request.registry.settings["host_forward_host"]

    def _proxy(self, url, params=None, method=None, cache=False, body=None, headers=None):
        # get query string
        params = dict(self.request.params) if params is None else params
        parsed_url = urlparse(url)
        all_params = parse_qs(parsed_url.query)
        for p in all_params:  # pragma: no cover
            all_params[p] = ",".join(all_params[p])
        all_params.update(params)
        params_encoded = {}
        for k, v in all_params.iteritems():
            params_encoded[k] = unicode(v).encode("utf-8")
        query_string = urllib.urlencode(params_encoded)

        if parsed_url.port is None:
            url = "{0!s}://{1!s}{2!s}?{3!s}".format(
                parsed_url.scheme, parsed_url.hostname,
                parsed_url.path, query_string
            )
        else:  # pragma: no cover
            url = "{0!s}://{1!s}:{2:d}{3!s}?{4!s}".format(
                parsed_url.scheme, parsed_url.hostname, parsed_url.port,
                parsed_url.path, query_string
            )

        log.info("Send query to URL:\n{0!s}.".format(url))

        if method is None:
            method = self.request.method

        # forward request to target (without Host Header)
        http = httplib2.Http()

        if headers is None:  # pragma: no cover
            headers = dict(self.request.headers)

        if parsed_url.hostname not in self.host_forward_host and "Host" in headers:  # pragma: no cover
            headers.pop("Host")

        if not cache:
            headers["Cache-Control"] = "no-cache"

        if method in ("POST", "PUT") and body is None:  # pragma: no cover
            body = StringIO(self.request.body)

        try:
            # fix encoding issue with IE
            url = url.encode("UTF8")
            if method in ("POST", "PUT"):
                resp, content = http.request(
                    url, method=method, body=body, headers=headers
                )
            else:
                resp, content = http.request(
                    url, method=method, headers=headers
                )
        except Exception as e:  # pragma: no cover
            log.error("Error '{0!s}' while getting the URL:\n{1!s}\nMethod: {2!s}.".format(
                sys.exc_info()[0], url, method
            ))

            log.error(
                "--- With headers ---\n{0!s}".format("\n".join(
                    ["{0!s}: {1!s}".format(*h) for h in headers.items()]
                ))
            )

            log.error("--- Exception ---")
            log.exception(e)

            if method in ("POST", "PUT"):
                log.error("--- With body ---")
                if hasattr(body, "read"):
                    body.reset()
                    log.error(body.read())
                else:
                    log.error(body)

            raise HTTPBadGateway("Error on backend<hr>See logs for detail")

        if resp.status < 200 or resp.status >= 300:  # pragma: no cover
            log.error(
                "Error '{0!s}' in response of URL:\n{1!s}.".format(resp.reason, url)
            )

            log.error("Status: {0:d}".format(resp.status))
            log.error("Method: {0!s}".format(method))

            log.error(
                "--- With headers ---\n{0!s}".format("\n".join(
                    ["{0!s}: {1!s}".format(*h) for h in headers.items()]
                ))
            )

            if method == "POST":
                log.error("--- Query with body ---")
                if hasattr(body, "read"):
                    body.reset()
                    log.error(body.read())
                else:
                    log.error(body)

            log.error("--- Return content ---")
            log.error(content)

            raise HTTPInternalServerError("See logs for details")

        return resp, content

    @cache_region.cache_on_arguments()
    def _proxy_cache(self, method, *args, **kwargs):  # pragma: no cover
        return self._proxy(*args, cache=True, **kwargs)

    def _proxy_response(
        self, service_name, url,
        headers=None, headers_update=None, public=False, **kwargs
    ):  # pragma: no cover
        if headers_update is None:
            headers_update = {}
        cache = kwargs.get("cache", False)
        if cache is True:
            resp, content = self._proxy_cache(
                url,
                self.request.method,
                **kwargs
            )
        else:
            resp, content = self._proxy(url, **kwargs)

        cache_control = (PUBLIC_CACHE if public else PRIVATE_CACHE) if cache else NO_CACHE
        return self._build_response(
            resp, content, cache_control, service_name,
            headers_update=headers_update
        )

    def _build_response(
        self, resp, content, cache_control, service_name,
        headers=None, headers_update=None, content_type=None
    ):
        if headers_update is None:
            headers_update = {}
        headers = dict(resp) if headers is None else headers

        # Hop-by-hop Headers are not supported by WSGI
        # See:
        # https://www.python.org/dev/peps/pep-3333/#other-http-features
        # chapter 13.5.1 at http://www.faqs.org/rfcs/rfc2616.html
        for header in [
                "connection",
                "keep-alive",
                "proxy-authenticate",
                "proxy-authorization",
                "te",
                "trailers",
                "transfer-encoding",
                "upgrade"
        ]:  # pragma: no cover
            if header in headers:
                del headers[header]
        # Other problematic headers
        for header in ["content-length", "content-location"]:  # pragma: no cover
            if header in headers:
                del headers[header]

        headers.update(headers_update)

        response = Response(content, status=resp.status, headers=headers)

        return set_common_headers(
            self.request, service_name, cache_control,
            response=response,
            content_type=content_type,
        )

    @staticmethod
    def _get_lower_params(params):
        return dict(
            (k.lower(), unicode(v).lower()) for k, v in params.iteritems()
        )

    def _get_headers(self):
        headers = self.request.headers
        if "Cookie" in headers:  # pragma: no cover
            headers.pop("Cookie")
        return headers
