# -*- coding: utf-8 -*-

# Copyright (c) 2013-2016, Camptocamp SA
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


import random
import string
import logging
from datetime import datetime
from urlparse import urlparse

from pyramid.httpexceptions import HTTPFound, HTTPBadRequest, \
    HTTPNotFound, HTTPInternalServerError
from pyramid.view import view_config

from c2cgeoportal.models import DBSession, Shorturl
from c2cgeoportal.lib.email_ import send_email
from c2cgeoportal.lib.caching import set_common_headers, NO_CACHE


logger = logging.getLogger(__name__)


class Shortener(object):

    def __init__(self, request):
        self.request = request
        self.settings = request.registry.settings.get("shortener", {})

    @view_config(route_name="shortener_get")
    def get(self):
        ref = self.request.matchdict["ref"]
        short_urls = DBSession.query(Shorturl).filter(Shorturl.ref == ref).all()

        if len(short_urls) != 1:
            raise HTTPNotFound("Ref '%s' not found" % ref)

        short_urls[0].nb_hits += 1
        short_urls[0].last_hit = datetime.now()

        set_common_headers(
            self.request, "shortner", NO_CACHE
        )
        return HTTPFound(location=short_urls[0].url)

    @view_config(route_name="shortener_create", renderer="json")
    def create(self):

        if "url" not in self.request.params:
            raise HTTPBadRequest("The parameter url is required")

        url = self.request.params["url"]

        # Check that it is an internal URL...
        uri_parts = urlparse(url)
        hostname = uri_parts.hostname
        paths = uri_parts.path.split("/")
        if hostname != self.request.server_name:
            raise HTTPBadRequest("The requested host '%s' should be '%s'" % (
                hostname, self.request.host
            ))

        shortened = False
        if (len(paths) > 1 and paths[-2] == "short"):
            ref = paths[-1]
            shortened = True

        tries = 0
        while not shortened:
            ref = "".join(
                random.choice(string.ascii_letters + string.digits)
                for i in range(self.settings.get("length", 4))
            )
            test_url = DBSession.query(Shorturl).filter(Shorturl.ref == ref).all()
            if len(test_url) == 0:
                break
            tries += 1  # pragma: no cover
            if tries > 20:  # pragma: no cover
                message = "No free ref found, considere to increase the length"
                logging.error(message)
                raise HTTPInternalServerError(message)

        user_email = self.request.user.email \
            if self.request.user is not None else None
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

        email = email or user_email

        if \
                email is not None and \
                "email_from" in self.settings and \
                "email_subject" in self.settings and \
                "email_body" in self.settings and \
                "smtp_server" in self.settings:  # pragma: no cover
            text = self.settings["email_body"] % {
                "full_url": url,
                "short_url": s_url,
            }
            send_email(
                self.settings["email_from"],
                [email],
                text.encode("utf-8"),
                self.settings["email_subject"],
                self.settings["smtp_server"],
            )

        set_common_headers(
            self.request, "shortner", NO_CACHE
        )
        return {"short_url": s_url}
