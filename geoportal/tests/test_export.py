# -*- coding: utf-8 -*-

# Copyright (c) 2013-2019, Camptocamp SA
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
import codecs


class TestExportCSVView(TestCase):

    def test_exportcsv(self):
        from pyramid.testing import DummyRequest
        from pyramid.httpexceptions import HTTPBadRequest
        from c2cgeoportal_geoportal.views.export import exportcsv

        request = DummyRequest()

        response = exportcsv(request)
        request.params = {
            "csv": "12,34"
        }
        self.assertEqual(type(response), HTTPBadRequest)

        request.method = "POST"
        request.params = {}
        response = exportcsv(request)
        self.assertEqual(type(response), HTTPBadRequest)

        request.params = {
            "csv": "éà,èç"
        }
        response = exportcsv(request)
        self.assertEqual(response.body, codecs.BOM_UTF8 + "éà,èç".encode("UTF-8"))


class TestExportGpxKmlView(TestCase):

    def test_no_format_param(self):
        from pyramid.testing import DummyRequest
        from pyramid.httpexceptions import HTTPBadRequest
        from c2cgeoportal_geoportal.views.export import exportgpxkml

        request = DummyRequest()
        request.method = "POST"
        request.params = {
            "name": "foo",
            "doc": "<gpx>éç</gpx>",
        }
        response = exportgpxkml(request)
        self.assertEqual(type(response), HTTPBadRequest)

    def test_unknown_format_param(self):
        from pyramid.testing import DummyRequest
        from pyramid.httpexceptions import HTTPBadRequest
        from c2cgeoportal_geoportal.views.export import exportgpxkml

        request = DummyRequest()
        request.method = "POST"
        request.params = {
            "format": "unknown",
            "name": "foo",
            "doc": "<gpx>éç</gpx>",
        }
        response = exportgpxkml(request)
        self.assertEqual(type(response), HTTPBadRequest)

    def test_no_name_param(self):
        from pyramid.testing import DummyRequest
        from pyramid.httpexceptions import HTTPBadRequest
        from c2cgeoportal_geoportal.views.export import exportgpxkml

        request = DummyRequest()
        request.method = "POST"
        request.params = {
            "format": "gpx",
            "doc": "<gpx>éç</gpx>",
        }
        response = exportgpxkml(request)
        self.assertEqual(type(response), HTTPBadRequest)

    def test_no_doc_param(self):
        from pyramid.testing import DummyRequest
        from pyramid.httpexceptions import HTTPBadRequest
        from c2cgeoportal_geoportal.views.export import exportgpxkml

        request = DummyRequest()
        request.method = "POST"
        request.params = {
            "format": "gpx",
            "name": "foo",
        }
        response = exportgpxkml(request)
        self.assertEqual(type(response), HTTPBadRequest)

    def test_gpx(self):
        from pyramid.testing import DummyRequest
        from c2cgeoportal_geoportal.views.export import exportgpxkml

        request = DummyRequest()
        request.method = "POST"
        request.params = {
            "format": "gpx",
            "name": "foo",
            "doc": "<gpx>éç</gpx>",
        }
        response = exportgpxkml(request)
        self.assertEqual(response.content_disposition,
                         "attachment; filename=foo.gpx")
        self.assertEqual(response.content_type,
                         "application/gpx")
        self.assertEqual(response.body, "<gpx>éç</gpx>".encode("UTF-8"))

    def test_kml(self):
        from pyramid.testing import DummyRequest
        from c2cgeoportal_geoportal.views.export import exportgpxkml

        request = DummyRequest()
        request.method = "POST"
        request.params = {
            "format": "kml",
            "name": "foo",
            "doc": "<kml>éç</kml>",
        }
        response = exportgpxkml(request)
        self.assertEqual(response.content_disposition,
                         "attachment; filename=foo.kml")
        self.assertEqual(response.content_type,
                         "application/vnd.google-earth.kml+xml")
        self.assertEqual(response.body, "<kml>éç</kml>".encode("UTF-8"))
