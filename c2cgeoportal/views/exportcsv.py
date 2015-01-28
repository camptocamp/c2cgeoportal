# -*- coding: utf-8 -*-

# Copyright (c) 2011-2015, Camptocamp SA
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


from pyramid.httpexceptions import HTTPBadRequest
from pyramid.view import view_config
import codecs

default_csv_extension = 'csv'

default_csv_encoding = 'UTF-8'


@view_config(route_name='csvecho')
def echo(request):
    if request.method != 'POST':
        return HTTPBadRequest('Wrong method')

    csv = request.params.get('csv', None)
    if csv is None:
        return HTTPBadRequest('csv parameter is required')

    request.response.cache_control.no_cache = True

    csv_extension = request.params.get('csv_extension', default_csv_extension)
    csv_encoding = request.params.get('csv_encoding', default_csv_encoding)
    name = request.params.get('name', 'export')

    res = request.response
    content = ''
    if csv_encoding == default_csv_encoding:
        content += codecs.BOM_UTF8
    content += csv.encode(csv_encoding)
    res.body = content
    res.headerlist = [('Content-type', 'text/csv')]
    res.charset = csv_encoding.encode(csv_encoding)
    res.content_disposition = 'attachment; filename=%s.%s' % \
        (name.replace(' ', '_'), csv_extension)
    return res
