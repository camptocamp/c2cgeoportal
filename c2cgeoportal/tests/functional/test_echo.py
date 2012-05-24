# -*- coding: utf-8 -*-
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
        request.method = 'POST'

        response = echo.echo(request)
        self.assertEquals(response.status_int, 400)

    def test_echo(self):
        from c2cgeoportal.views import echo
        from webob import Request

        request = Request.blank('/')
        request.method = 'POST'
        request.content_type = 'multipart/form-data; boundary="foobar"'
        request.body = '''\
--foobar
Content-Disposition: form-data; name="file"; filename="a file name"
Content-Type: text/html

some content with non-ASCII chars ç à é
--foobar--
'''

        response = echo.echo(request)
        self.assertEquals(response.status_int, 200)
        self.assertEquals(response.content_type, 'text/html')
        self.assertEquals(response.body, '{"filename":"a file name","data":"c29tZSBjb250ZW50IHdpdGggbm9uLUFTQ0lJIGNoYXJzIMOnIMOgIMOp","success":true}')  # NOQA
