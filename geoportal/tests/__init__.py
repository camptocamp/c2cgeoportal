# Copyright (c) 2011-2023, Camptocamp SA
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


"""
Pyramid application test package.
"""

import logging
import os
import urllib.parse
import warnings

import sqlalchemy.exc
from pyramid.testing import DummyRequest as PyramidDummyRequest

from c2cgeoportal_geoportal.lib import caching

with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=sqlalchemy.exc.SAWarning)


class DummyRequest(PyramidDummyRequest):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_addr = "1.1.1.1"
        self.referrer = None
        if self.registry.settings is None:
            self.registry.settings = {}


def setup_common():
    logging.getLogger("c2cgeoportal_geoportal").setLevel(logging.DEBUG)

    caching.init_region({"backend": "dogpile.cache.null"}, "std")
    caching.init_region({"backend": "dogpile.cache.null"}, "obj")
    caching.init_region({"backend": "dogpile.cache.null"}, "ogc-server")


def create_dummy_request(additional_settings=None, *args, **kargs):
    if additional_settings is None:
        additional_settings = {}
    request = DummyRequest(*args, **kargs)
    request.registry.settings = {
        "available_locale_names": ["en", "fr", "de"],
        "default_locale_name": "fr",
        "default_max_age": 1000,
        "package": "package_for_test",
    }
    request.registry.settings.update(additional_settings)
    request.is_valid_referer = True
    request.scheme = "https"
    request.static_url = lambda url: "http://example.com/dummy/static/url"
    request.route_url = (
        lambda name, **kwargs: "http://example.com/"
        + name
        + "/view?"
        + urllib.parse.urlencode(kwargs.get("_query", {}))
    )
    request.current_route_url = lambda **kwargs: "http://example.com/current/view?" + urllib.parse.urlencode(
        kwargs.get("_query", {})
    )
    request.get_organization_role = lambda role_type: role_type
    request.get_organization_interface = lambda interface: interface

    return request


def load_binfile(file_name):
    with open(os.path.join("/opt/c2cgeoportal/geoportal", file_name), "rb") as file_:
        return file_.read()


def load_file(file_name):
    with open(os.path.join("/opt/c2cgeoportal/geoportal", file_name)) as file_:
        return file_.read()
