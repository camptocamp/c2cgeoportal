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


import codecs

from pyramid.httpexceptions import HTTPBadRequest
from pyramid.view import view_config

from c2cgeoportal.lib.caching import set_common_headers, NO_CACHE

DEFAULT_CSV_EXTENSION = "csv"
DEFAULT_CSV_ENCODING = "UTF-8"


@view_config(route_name="csvecho")
def exportcsv(request):
    csv = request.params.get("csv")
    if csv is None:
        return HTTPBadRequest("csv parameter is required")

    request.response.cache_control.no_cache = True

    csv_extension = request.params.get("csv_extension", DEFAULT_CSV_EXTENSION)
    csv_encoding = request.params.get("csv_encoding", DEFAULT_CSV_ENCODING)
    name = request.params.get("name", "export")

    response = request.response
    content = ""
    if csv_encoding == DEFAULT_CSV_ENCODING:
        content += codecs.BOM_UTF8
    content += csv.encode(csv_encoding)
    request.response.body = content
    response.charset = csv_encoding.encode(csv_encoding)
    response.content_disposition = "attachment; filename={0!s}.{1!s}".format(
        name.replace(" ", "_"), csv_extension
    )
    return set_common_headers(
        request, "csvecho", NO_CACHE,
        content_type="text/csv"
    )


_CONTENT_TYPES = {
    "gpx": "application/gpx",
    "kml": "application/vnd.google-earth.kml+xml",
}


@view_config(route_name="exportgpxkml")
def exportgpxkml(request):
    """
    View used to export a GPX or KML document.
    """

    fmt = request.params.get("format")
    if fmt is None:
        return HTTPBadRequest("format parameter is required")
    if fmt not in _CONTENT_TYPES:
        return HTTPBadRequest("format is not supported")

    name = request.params.get("name")
    if name is None:
        return HTTPBadRequest("name parameter is required")

    doc = request.params.get("doc")
    if doc is None:
        return HTTPBadRequest("doc parameter is required")

    charset = "utf-8"
    response = request.response
    response.body = doc.encode(charset)
    response.charset = charset
    response.content_disposition = ("attachment; filename={0!s}.{1!s}".format(name.replace(" ", "_"), fmt))
    return set_common_headers(
        request, "exportgpxkml", NO_CACHE,
        content_type=_CONTENT_TYPES[fmt]
    )
