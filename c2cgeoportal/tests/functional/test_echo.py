# -*- coding: utf-8 -*-

# Copyright (c) 2013-2018, Camptocamp SA
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


from unittest import TestCase
from nose.plugins.attrib import attr

from pyramid import testing


@attr(functional=True)
class TestEchoView(TestCase):

    def test_echo_bad_method(self):
        from c2cgeoportal.views import echo

        request = testing.DummyRequest()

        response = echo.echo(request)
        self.assertEquals(response.status_int, 400)

    def test_echo_bad_request(self):
        from c2cgeoportal.views import echo

        request = testing.DummyRequest()
        request.method = "POST"

        response = echo.echo(request)
        self.assertEquals(response.status_int, 400)

    def test_echo(self):
        from c2cgeoportal.views import echo
        from webob import Request

        request = Request.blank("/")
        request.method = "POST"
        request.content_type = 'multipart/form-data; boundary="foobar"'
        request.body = """
--foobar
Content-Disposition: form-data; name="file"; filename="a file name"
Content-Type: text/html

some content with non-ASCII chars ç à é
--foobar--
"""

        response = echo.echo(request)
        self.assertEquals(response.status_int, 200)
        self.assertEquals(response.content_type, "text/html")
        self.assertEquals(response.body, '{"filename":"a file name","data":"c29tZSBjb250ZW50IHdpdGggbm9uLUFTQ0lJIGNoYXJzIMOnIMOgIMOp","success":true}')  # noqa
