# Copyright (c) 2019-2024, Camptocamp SA
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


import glob
import logging

import pyramid.request
import pyramid.response
from lingva.extract import (  # strip_linenumbers,
    ExtractorOptions,
    POEntry,
    create_catalog,
    find_file,
    list_files,
    no_duplicates,
    read_config,
)
from lingva.extractors import get_extractor, register_extractors
from lingva.extractors.babel import register_babel_plugins
from pyramid.httpexceptions import HTTPFound, HTTPInternalServerError
from pyramid.view import view_config

from c2cgeoportal_geoportal.lib.cacheversion import get_cache_version
from c2cgeoportal_geoportal.lib.common_headers import Cache, set_common_headers

_LOG = logging.getLogger(__name__)
_INITIALIZED = False


@view_config(route_name="localejson")  # type: ignore[misc]
def locale(request: pyramid.request.Request) -> pyramid.response.Response:
    """Get the locale json file for the API."""
    response = HTTPFound(
        request.static_url(
            f"/etc/geomapfish/static/{request.locale_name}.json",
            _query={"cache": get_cache_version()},
        )
    )
    set_common_headers(request, "api", Cache.PUBLIC_NO, response=response)
    return response


@view_config(route_name="localepot")  # type: ignore[misc]
def localepot(request: pyramid.request.Request) -> pyramid.response.Response:
    """Get the pot from an HTTP request."""

    # Build the list of files to be processed
    sources = []
    sources += glob.glob(f"/app/{request.registry.package_name}/static-ngeo/js/apps/*.html.ejs")
    sources += glob.glob(f"/app/{request.registry.package_name}/static-ngeo/js/**/*.js", recursive=True)
    sources += glob.glob(f"/app/{request.registry.package_name}/static-ngeo/js/**/*.html", recursive=True)
    sources += glob.glob("/usr/local/tomcat/webapps/ROOT/**/config.yaml", recursive=True)
    sources += ["/etc/geomapfish/config.yaml", "/app/development.ini"]

    # The following code is a modified version of the main function of this file:
    # https://github.com/wichert/lingva/blob/master/src/lingva/extract.py

    global _INITIALIZED  # pylint: disable=global-statement
    if not _INITIALIZED:
        register_extractors()
        register_babel_plugins()
        _INITIALIZED = True

        with open("/app/lingva-client.cfg", encoding="utf-8") as config_file:
            read_config(config_file)
        _INITIALIZED = True

    catalog = create_catalog(
        width=110,
        copyright_holder="",
        package_name="GeoMapFish-project",
        package_version="1.0",
        msgid_bugs_address=None,
    )

    for filename in no_duplicates(list_files(None, sources)):
        real_filename = find_file(filename)
        if real_filename is None:
            _LOG.error("Can not find file %s", filename)
            raise HTTPInternalServerError(f"Can not find file {filename}")
        extractor = get_extractor(real_filename)
        if extractor is None:
            _LOG.error("No extractor available for file %s", filename)
            raise HTTPInternalServerError(f"No extractor available for file {filename}")

        extractor_options = ExtractorOptions(
            comment_tag=True,
            domain=None,
            keywords=None,
        )
        for message in extractor(real_filename, extractor_options):
            entry = catalog.find(message.msgid, msgctxt=message.msgctxt)
            if entry is None:
                entry = POEntry(msgctxt=message.msgctxt, msgid=message.msgid)
                catalog.append(entry)
            entry.update(message)

    # for entry in catalog:
    #     strip_linenumbers(entry)

    # Build the response
    request.response.text = catalog.__unicode__()
    set_common_headers(request, "api", Cache.PUBLIC, content_type="text/x-gettext-translation")
    return request.response
