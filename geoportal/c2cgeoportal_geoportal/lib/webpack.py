# -*- coding: utf-8 -*-

# Copyright (c) 2018-2019, Camptocamp SA
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


import re


class WebpackTween:
    _RE_RESOURCES = re.compile(r'.+\.(js|css|png|ico|cur)$')

    def __init__(self, handler, registry):
        del registry
        self.handler = handler

    def __call__(self, request):
        interfaces = request.registry.settings['interfaces']
        default_interface = request.registry.settings['default_interface']
        default = False

        path_info = request.path_info.split('/')
        # Dynamic.js
        if request.path_info in ('/dynamic.js', '/theme/dynamic.js'):
            request.path_info = '/dynamic.js'
        # Default interface root
        # e.-g.: /
        # e.-g.: /theme/OSM
        elif request.path_info in ('', '/') or (
            len(path_info) == 3 and
            path_info[1] == 'theme' and
            not self._RE_RESOURCES.match(path_info[2])
        ):
            request.path_info = '/static-ngeo/unused-cache-buster/build/{}.html'.format(default_interface)
            default = True
        # Other interfaces
        elif path_info[1] in interfaces:
            # Root
            # e.-g.: /mobile
            # e.-g.: /mobile/
            # e.-g.: /mobile/theme/OSM
            if len(path_info) == 2 or (
                len(path_info) == 3 and path_info[2] == ''
            ) or (
                len(path_info) == 4 and
                path_info[2] == 'theme' and
                not self._RE_RESOURCES.match(path_info[3])
            ):
                request.path_info = '/static-ngeo/unused-cache-buster/build/{}.html'.format(path_info[1])
                default = True

        response = self.handler(request)

        if default:
            response.cache_control.no_cache = True
            response.cache_control.max_age = 0

        return response
