# -*- coding: utf-8 -*-

# Copyright (c) 2015-2019, Camptocamp SA
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

# pylint: disable=missing-docstring,attribute-defined-outside-init,protected-access


from unittest import TestCase

from pyramid.request import Request, Response

from c2cgeoportal_geoportal.lib.caching import set_cors_headers, CORS_METHODS


class TestSetCorsHeaders(TestCase):
    ORIGIN1 = "http://www.example.com"
    ORIGIN2 = "http://www.friend.com"
    MAX_AGE = "1234"
    SETTINGS = {
        "access_control_allow_origin": [ORIGIN1, ORIGIN2],
        "access_control_max_age": MAX_AGE
    }

    @staticmethod
    def _do(method, headers, credentials=False, settings=SETTINGS):
        req = Request({}, method=method, headers=headers)
        req.response = Response()
        set_cors_headers(settings, req, "foo", credentials, req.response)
        return req.response.headers

    def _assert_headers(self, actual, expected):
        # need to add the headers automatically added by Request
        base_headers = {
            "Content-Type": "text/html; charset=UTF-8",
            "Content-Length": "0"
        }
        expected = expected.copy()
        expected.update(base_headers)
        self.assertEqual(actual, expected)

    def test_simple(self):
        """
        Tests specified in http://www.w3.org/TR/cors/#resource-requests
        """
        # 1. If the Origin header is not present terminate this set of steps.
        #    The request is outside the scope of this specification.
        self._assert_headers(self._do("POST", {}), {})

        # 2. If the value of the Origin header is not a case-sensitive match for
        #    any of the values in list of origins, do not set any additional
        #    headers and terminate this set of steps.
        self._assert_headers(self._do("POST", {"Origin": "http://foe.com"}), {})

        # 3. If the resource supports credentials add a single
        #    Access-Control-Allow-Origin header, with the value of the Origin
        #    header as value, and add a single Access-Control-Allow-Credentials
        #    header with the case-sensitive string "true" as value.
        self._assert_headers(self._do("POST", {
            "Origin": self. ORIGIN2
        }, credentials=True), {
            "Access-Control-Allow-Origin": self.ORIGIN2,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": CORS_METHODS,
            "Vary": set(["Origin"]),
        })

        # 3. Otherwise, add a single Access-Control-Allow-Origin header, with
        #    either the value of the Origin header or the string "*" as value.
        self._assert_headers(self._do("POST", {"Origin": self. ORIGIN2}), {
            "Access-Control-Allow-Origin": self.ORIGIN2,
            "Access-Control-Allow-Methods": CORS_METHODS,
            "Vary": set(["Origin"]),
        })

        # 4. If the list of exposed headers is not empty add one or more
        #    Access-Control-Expose-Headers headers, with as values the header
        #    field names given in the list of exposed headers.
        # Not implemented

    def test_preflight(self):
        """
        Tests specified in
        http://www.w3.org/TR/cors/#resource-preflight-requests
        """
        # 1. If the Origin header is not present terminate this set of steps.
        #    The request is outside the scope of this specification.
        self._assert_headers(self._do("OPTIONS", {}), {})

        # 2. If the value of the Origin header is not a case-sensitive match for
        #    any of the values in list of origins do not set any additional
        #    headers and terminate this set of steps.
        self._assert_headers(self._do("OPTIONS", {"Origin": "http://foe.com"}),
                             {})

        # 3. If there is no Access-Control-Request-Method header or if parsing
        #    failed, do not set any additional headers and terminate this set
        #    of steps. The request is outside the scope of this specification.
        self._assert_headers(self._do("OPTIONS", {
            "Origin": self.ORIGIN1}), {})

        # 4. If there are no Access-Control-Request-Headers headers let header
        #    field-names be the empty list.
        self._assert_headers(self._do("OPTIONS", {
            "Origin": self.ORIGIN1,
            "Access-Control-Request-Method": "GET"
        }), {
            "Access-Control-Allow-Origin": self.ORIGIN1,
            "Access-Control-Max-Age": self.MAX_AGE,
            "Access-Control-Allow-Methods": CORS_METHODS,
            "Vary": set(["Origin"]),
        })

        # 5. If method is not a case-sensitive match for any of the values in
        #    list of methods do not set any additional headers and terminate
        #    this set of steps.
        # Not implemented

        # 6. If any of the header field-names is not a ASCII case-insensitive
        #    match for any of the values in list of headers do not set any
        #    additional headers and terminate this set of steps.
        # Not implemented

        # 7. If the resource supports credentials add a single
        #    Access-Control-Allow-Origin header, with the value of the Origin
        #    header as value, and add a single Access-Control-Allow-Credentials
        #    header with the case-sensitive string "true" as value.
        self._assert_headers(self._do("OPTIONS", {
            "Origin": self.ORIGIN1,
            "Access-Control-Request-Method": "GET"
        }, credentials=True), {
            "Access-Control-Allow-Origin": self.ORIGIN1,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": self.MAX_AGE,
            "Access-Control-Allow-Methods": CORS_METHODS,
            "Vary": set(["Origin"]),
        })

        # 8. Optionally add a single Access-Control-Max-Age header with as value
        #    the amount of seconds the user agent is allowed to cache the result
        #    of the request.
        # Already tested

        # 9. Add one or more Access-Control-Allow-Methods headers consisting of
        #    (a subset of) the list of methods.
        # Already tested

        # 10. Add one or more Access-Control-Allow-Headers headers consisting of
        #     (a subset of) the list of headers.
        self._assert_headers(self._do("OPTIONS", {
            "Origin": self.ORIGIN1,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-Foo, X-Bar"
        }), {
            "Access-Control-Allow-Origin": self.ORIGIN1,
            "Access-Control-Max-Age": self.MAX_AGE,
            "Access-Control-Allow-Methods": CORS_METHODS,
            "Access-Control-Allow-Headers": "X-Foo, X-Bar",
            "Vary": set(["Origin"]),
        })

    def test_not_configured(self):
        # If the service is not configured, then no CORS head.
        self._assert_headers(
            self._do("GET", {"Origin": self. ORIGIN1}, settings=None), {})

    def test_match_all(self):
        settings = {
            "access_control_allow_origin": [self.ORIGIN1, "*"],
            "access_control_max_age": self.MAX_AGE
        }

        # An origin included in the access_control_allow_origin list is OK with
        # credentials
        self._assert_headers(self._do("POST", {
            "Origin": self.ORIGIN1
        }, credentials=True, settings=settings), {
            "Access-Control-Allow-Origin": self.ORIGIN1,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": CORS_METHODS,
            "Vary": set(["Origin"]),
        })

        # An origin not included in the access_control_allow_origin is allowed,
        # but without credentials
        self._assert_headers(self._do("POST", {
            "Origin": "http://guest.com"
        }, credentials=True, settings=settings), {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": CORS_METHODS,
            "Vary": set(["Origin"]),
        })
