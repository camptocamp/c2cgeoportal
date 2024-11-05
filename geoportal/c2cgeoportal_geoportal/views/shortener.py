# Copyright (c) 2013-2024, Camptocamp SA
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
import random
import string
from datetime import datetime
from typing import cast
from urllib.parse import urlparse

import pyramid.request
from pyramid.httpexceptions import HTTPBadRequest, HTTPFound, HTTPInternalServerError, HTTPNotFound
from pyramid.view import view_config

from c2cgeoportal_commons.lib.email_ import send_email_config
from c2cgeoportal_commons.models import DBSession, static
from c2cgeoportal_geoportal import is_allowed_url
from c2cgeoportal_geoportal.lib.common_headers import Cache, set_common_headers

logger = logging.getLogger(__name__)


class Shortener:
    """All the views conserne the shortener."""

    def __init__(self, request: pyramid.request.Request):
        self.request = request
        self.settings = request.registry.settings.get("shortener", {})
        self.short_bases = [self.request.route_url("shortener_get", ref="")]
        if "base_url" in self.settings:
            self.short_bases.append(self.settings["base_url"])

    @view_config(route_name="shortener_get")  # type: ignore
    def get(self) -> HTTPFound:
        assert DBSession is not None

        ref = self.request.matchdict["ref"]
        short_urls = DBSession.query(static.Shorturl).filter(static.Shorturl.ref == ref).all()

        if len(short_urls) != 1:
            raise HTTPNotFound(f"Ref '{ref!s}' not found")

        short_urls[0].nb_hits += 1
        short_urls[0].last_hit = datetime.now()

        set_common_headers(self.request, "shortener", Cache.PUBLIC_NO)
        return HTTPFound(location=short_urls[0].url)

    @view_config(route_name="shortener_create", renderer="json")  # type: ignore
    def create(self) -> dict[str, str]:
        assert DBSession is not None

        if "url" not in self.request.params:
            raise HTTPBadRequest("The parameter url is required")

        url = self.request.params["url"]

        # see: https://httpd.apache.org/docs/2.2/mod/core.html#limitrequestline
        if len(url) > 8190:
            raise HTTPBadRequest(f"The parameter url is too long ({len(url)} > {8190})")

        allowed_hosts = self.settings.get("allowed_hosts", [])
        url_hostname, ok = is_allowed_url(self.request, url, allowed_hosts)
        if not ok:
            message = (
                f"Invalid requested host '{url_hostname}', "
                f"is not the current host '{self.request.host}' "
                f"or part of allowed hosts: {', '.join(allowed_hosts)}"
            )
            logging.debug(message)
            raise HTTPBadRequest(message)

        shortened = False

        uri_parts = urlparse(url)
        for base in self.short_bases:
            base_parts = urlparse(base)
            if uri_parts.path.startswith(base_parts.path):
                shortened = True
                ref = uri_parts.path.split("/")[-1]

        tries = 0
        while not shortened:
            ref = "".join(
                random.choice(string.ascii_letters + string.digits)  # nosec
                for i in range(self.settings.get("length", 4))
            )
            test_url = DBSession.query(static.Shorturl).filter(static.Shorturl.ref == ref).all()
            if not test_url:
                break
            tries += 1
            if tries > 20:
                message = "No free ref found, considered to increase the length"
                logger.error(message)
                raise HTTPInternalServerError(message)

        user_email = cast(static.User, self.request.user).email if self.request.user is not None else None
        email = self.request.params.get("email")
        if not shortened:
            short_url = static.Shorturl()
            short_url.url = url
            short_url.ref = ref
            short_url.creator_email = user_email
            short_url.creation = datetime.now()
            short_url.nb_hits = 0

            DBSession.add(short_url)

        if "base_url" in self.settings:
            s_url = self.settings["base_url"] + ref
        else:
            s_url = self.request.route_url("shortener_get", ref=ref)

        if email is not None:
            send_email_config(
                self.request.registry.settings,
                "shortener",
                email,
                full_url=url,
                short_url=s_url,
                message=self.request.params.get("message", ""),
                application_url=self.request.route_url("base"),
                current_url=self.request.current_route_url(),
            )

        set_common_headers(self.request, "shortener", Cache.PRIVATE_NO)
        return {"short_url": s_url}
