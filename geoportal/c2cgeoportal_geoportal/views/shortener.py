# -*- coding: utf-8 -*-

# Copyright (c) 2013-2019, Camptocamp SA
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


from datetime import datetime
import logging
import random
import string
from urllib.parse import urlparse

from pyramid.httpexceptions import HTTPBadRequest, HTTPFound, HTTPInternalServerError, HTTPNotFound
from pyramid.view import view_config

from c2cgeoportal_commons.lib.email_ import send_email_config
from c2cgeoportal_commons.models import DBSession
from c2cgeoportal_commons.models.static import Shorturl
from c2cgeoportal_geoportal.lib.caching import NO_CACHE, set_common_headers

logger = logging.getLogger(__name__)


class Shortener:
    def __init__(self, request):
        self.request = request
        self.settings = request.registry.settings.get("shortener", {})
        self.short_bases = [self.request.route_url("shortener_get", ref="")]
        if "base_url" in self.settings:
            self.short_bases.append(self.settings["base_url"])

    @view_config(route_name="shortener_get")
    def get(self):
        ref = self.request.matchdict["ref"]
        short_urls = DBSession.query(Shorturl).filter(Shorturl.ref == ref).all()

        if len(short_urls) != 1:
            raise HTTPNotFound("Ref '{0!s}' not found".format(ref))

        short_urls[0].nb_hits += 1
        short_urls[0].last_hit = datetime.now()

        set_common_headers(self.request, "shortener", NO_CACHE)
        return HTTPFound(location=short_urls[0].url)

    @view_config(route_name="shortener_create", renderer="json")
    def create(self):

        if "url" not in self.request.params:
            raise HTTPBadRequest("The parameter url is required")

        url = self.request.params["url"]

        # see: https://httpd.apache.org/docs/2.2/mod/core.html#limitrequestline
        if len(url) > 8190:  # pragma: no cover
            raise HTTPBadRequest("The parameter url is too long ({} > {})".format(len(url), 8190))

        # Check that it is an internal URL...
        uri_parts = urlparse(url)
        hostname = uri_parts.hostname
        if "allowed_hosts" in self.settings:
            if hostname not in self.settings["allowed_hosts"]:  # pragma: no cover
                raise HTTPBadRequest("The requested host is not allowed.")
        else:
            if hostname != self.request.server_name:
                raise HTTPBadRequest(
                    "The requested host '{0!s}' should be '{1!s}'".format(hostname, self.request.server_name)
                )

        shortened = False

        for base in self.short_bases:
            base_parts = urlparse(base)
            if uri_parts.path.startswith(base_parts.path):
                shortened = True
                ref = uri_parts.path.split("/")[-1]

        tries = 0
        while not shortened:
            ref = "".join(
                random.choice(string.ascii_letters + string.digits)
                for i in range(self.settings.get("length", 4))
            )
            test_url = DBSession.query(Shorturl).filter(Shorturl.ref == ref).all()
            if not test_url:
                break
            tries += 1  # pragma: no cover
            if tries > 20:  # pragma: no cover
                message = "No free ref found, considered to increase the length"
                logging.error(message)
                raise HTTPInternalServerError(message)

        user_email = self.request.user.email if self.request.user is not None else None
        email = self.request.params.get("email")
        if not shortened:
            short_url = Shorturl()
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

        if email is not None:  # pragma: no cover
            send_email_config(
                self.request.registry.settings,
                "shortener",
                email,
                full_url=url,
                short_url=s_url,
                message=self.request.params.get("message", ""),
            )

        set_common_headers(self.request, "shortener", NO_CACHE)
        return {"short_url": s_url}
