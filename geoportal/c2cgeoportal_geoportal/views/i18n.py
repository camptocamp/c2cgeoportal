# Copyright (c) 2019-2021, Camptocamp SA
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
from lingua.extract import (
    ExtractorOptions,
    POEntry,
    create_catalog,
    find_file,
    list_files,
    no_duplicates,
    read_config,
    strip_linenumbers,
)
from lingua.extractors import get_extractor, register_extractors
from lingua.extractors.babel import register_babel_plugins
from pyramid.httpexceptions import HTTPInternalServerError
from pyramid.view import view_config

from c2cgeoportal_geoportal.lib import lingua_extractor
from c2cgeoportal_geoportal.lib.caching import Cache, set_common_headers

LOG = logging.getLogger(__name__)


@view_config(route_name="localepot")  # type: ignore
def localepot(request: pyramid.request.Request) -> pyramid.response.Response:
    """Get the pot from an HTTP request."""
    # Build the list of files to be process
    package = request.registry.settings["package"]
    sources = ["/etc/geomapfish/config.yaml", "/app/development.ini"]
    sources += glob.glob(f"geoportal/{package}_geoportal/static-ngeo/js/apps/**/*.html.ejs")
    sources += glob.glob(f"geoportal/{package}_geoportal/static-ngeo/js/**/*.js")
    sources += glob.glob(f"geoportal/{package}_geoportal/static-ngeo/js/**/*.html")
    sources += glob.glob("/usr/local/tomcat/webapps/ROOT/**/config.yaml")

    # Convert the request argument into a config of our lingua extractor
    lingua_extractor.CONFIG.clear()
    for arg, value in request.params.items():
        lingua_extractor.CONFIG[arg.upper()] = value[0]

    # The following code is a modified version of the main function of this file:
    # https://github.com/wichert/lingua/blob/master/src/lingua/extract.py

    register_extractors()
    register_babel_plugins()

    with open("/app/lingua-client.cfg", encoding="utf-8") as config_file:
        read_config(config_file)

    catalog = create_catalog(110, "© (copyright)", "GeoMapFish-project", "1.0", None)

    for filename in no_duplicates(list_files(None, sources)):
        real_filename = find_file(filename)
        if real_filename is None:
            LOG.error("Can not find file %s", filename)
            raise HTTPInternalServerError(f"Can not find file {filename}")
        extractor = get_extractor(real_filename)
        if extractor is None:
            LOG.error("No extractor available for file %s", filename)
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

    for entry in catalog:
        strip_linenumbers(entry)

    # Build the response
    request.response.text = catalog.__unicode__()
    set_common_headers(request, "api", Cache.PUBLIC, content_type="text/x-gettext-translation")
    return request.response
