# -*- coding: utf-8 -*-
from unittest import TestCase
from nose.plugins.attrib import attr

from papyrus_ogcproxy.views import ogcproxy
from pyramid import testing

@attr(functional=True)
class TestOgcproxyView(TestCase):

    def test_nourl(self):
        request = testing.DummyRequest()
        request.scheme = 'http'
        response = ogcproxy(request)
        self.assertEqual(response.status_int, 400)

    def test_badurl(self):
        request = testing.DummyRequest()
        request.scheme = 'http'
        request.params['url'] = 'http:/toto'
        response = ogcproxy(request)
        self.assertEqual(response.status_int, 400)

        request.params['url'] = 'ftp://toto'
        response = ogcproxy(request)
        self.assertEqual(response.status_int, 400)

