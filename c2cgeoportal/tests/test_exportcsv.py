# -*- coding: utf-8 -*-
from unittest import TestCase

class TestEntryView(TestCase):

    def test_echo(self):
        from pyramid.testing import DummyRequest
        from pyramid.httpexceptions import HTTPBadRequest
        from c2cgeoportal.views.exportcsv import echo

        request = DummyRequest()

        responce = echo(request)
        request.params = {
            'csv': '12,34'
        }
        self.assertEqual(type(responce), HTTPBadRequest)

        request.method = 'POST'
        request.params = {}
        responce = echo(request)
        self.assertEqual(type(responce), HTTPBadRequest)

        request.params = {
            'csv': 'éà,èç'
        }
        responce = echo(request)
        self.assertEqual(responce.body, 'éà,èç')
