# -*- coding: utf-8 -*-

# Copyright (c) 2012-2018, Camptocamp SA
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
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

from c2cgeoportal_geoportal.lib.caching import set_common_headers, NO_CACHE

log = logging.getLogger(__name__)


def add_ending_slash(request):
    return HTTPFound(location=request.path + '/')


@view_config(context=Exception, renderer="json", http_cache=0)
def other_error(exception, request):  # pragma: no cover
    set_common_headers(request, "index", NO_CACHE)
    return _do_error(request, 500, exception)


def _do_error(request, status, exception):  # pragma: no cover
    log.error(
        "%s %s returned status code %s: %s",
        request.method, request.url, status, str(exception),
        extra={"referer": request.referer}, exc_info=True)
    request.response.status_code = status
    response = {"message": str(exception), "status": status}
    return response
