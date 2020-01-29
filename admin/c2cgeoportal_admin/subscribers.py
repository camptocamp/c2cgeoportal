# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020, Camptocamp SA
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


from pyramid.i18n import TranslationStringFactory, get_localizer

# see https://docs.pylonsproject.org/projects/pyramid-cookbook/en/latest/templates/mako_i18n.html*


def add_renderer_globals(event):
    request = event["request"]
    event["_"] = request.translate
    event["localizer"] = request.localizer


tsf1 = TranslationStringFactory("c2cgeoportal_admin")
tsf2 = TranslationStringFactory("c2cgeoform")


def add_localizer(event):
    request = event.request
    localizer = get_localizer(request)

    def auto_translate(*args, **kwargs):
        result = localizer.translate(tsf1(*args, **kwargs))
        return localizer.translate(tsf2(*args, **kwargs)) if result == args[0] else result

    request.localizer = localizer
    request.translate = auto_translate
