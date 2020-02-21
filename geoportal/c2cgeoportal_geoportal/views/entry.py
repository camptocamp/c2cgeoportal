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
from typing import Dict, Set, Tuple  # noqa # pylint: disable=unused-import
import xml.dom.minidom  # noqa # pylint: disable=unused-import

from pyramid.i18n import TranslationStringFactory
from pyramid.view import view_config

from c2cgeoportal_geoportal.lib.caching import NO_CACHE, PUBLIC_CACHE, set_common_headers

_ = TranslationStringFactory("c2cgeoportal")
LOG = logging.getLogger(__name__)


class Entry:
    def __init__(self, request):
        self.request = request

    @view_config(route_name="testi18n", renderer="testi18n.html")
    def testi18n(self):  # pragma: no cover
        _ = self.request.translate
        return {"title": _("title i18n")}

    def get_ngeo_index_vars(self):
        set_common_headers(self.request, "index", NO_CACHE, content_type="text/html")
        return {}

    def apijs(self):
        set_common_headers(self.request, "api", PUBLIC_CACHE, content_type="application/javascript")
        return {}

    def favicon(self):
        set_common_headers(self.request, "index", NO_CACHE, content_type="image/vnd.microsoft.icon")
        return {}

    def robot_txt(self):
        set_common_headers(self.request, "index", NO_CACHE, content_type="text/plain")
        return {}

    def apijsmap(self):
        set_common_headers(self.request, "api", NO_CACHE, content_type="application/octet-stream")
        return {}

    def apicss(self):
        set_common_headers(self.request, "api", PUBLIC_CACHE, content_type="text/css")
        return {}

    def apihelp(self):
        set_common_headers(self.request, "apihelp", NO_CACHE)
        return {}
