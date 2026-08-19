# Copyright (c) 2025-2026, Camptocamp SA
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

from pyramid.events import BeforeRender, NewRequest, subscriber
from pyramid.i18n import TranslationStringFactory, get_localizer

# use two translator to translate each strings in Make
tsf_server = TranslationStringFactory("{{cookiecutter.package}}-server")
tsf_geoportal = TranslationStringFactory("c2cgeoportal")
tsf_admin = TranslationStringFactory("c2cgeoportal_admin")
tsf_c2cgeoform = TranslationStringFactory("c2cgeoform")
tsf_getitfixed = TranslationStringFactory("getitfixed")


@subscriber(NewRequest)
def add_localizer(event) -> None:
    request = event.request
    localizer = get_localizer(request)

    def auto_translate(string):
        if request.path_info.startswith("/admin/"):
            tsf_list = [tsf_admin, tsf_c2cgeoform]
        elif request.path_info.startswith("/getitfixed"):
            tsf_list = [tsf_getitfixed, tsf_c2cgeoform]
        else:
            tsf_list = [tsf_server, tsf_geoportal]
        for tsf in tsf_list:
            result = localizer.translate(tsf(string))
            if result != string:
                break
        return result

    request.localizer = localizer
    request.translate = auto_translate


@subscriber(BeforeRender)
def add_renderer_globals(event) -> None:
    request = event.get("request")
    if request:
        event["_"] = request.translate
        event["localizer"] = request.localizer
