# -*- coding: utf-8 -*-

# Copyright (c) 2015-2017, Camptocamp SA
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


# from unittest2 import TestCase
# from nose.plugins.attrib import attr
#
# from geoalchemy2 import WKTElement
# import transaction
#
# from tests import load_file, load_binfile
# from tests.functional import (  # noqa
#     tear_down_common as tearDownModule,
#     set_up_common as setUpModule,
#     create_dummy_request, create_default_ogcserver, cleanup_db)
#
#
# def _create_dummy_request(username=None):
#     from c2cgeoportal.models import DBSession, User
#
#     request = create_dummy_request({
#         "tinyowsproxy": {
#             "tinyows_url": "http://localhost/tinyows",
#             "online_resource": "http://domain.com/tinyows_proxy",
#             "proxy_online_resource": "http://domain.com/tinyows"
#         }
#     })
#     request.user = None if username is None else \
#         DBSession.query(User).filter_by(username=username).one()
#     return request
#
#
# @attr(functional=True)
# class TestTinyOWSProxyView(TestCase):
#     data_base = "tests/data/"
#     capabilities_response_file = \
#         data_base + "tinyows_getcapabilities_layer.xml"
#     capabilities_response_filtered_file1 = \
#         data_base + "tinyows_getcapabilities_layer_filtered_user1.xml"
#     capabilities_response_filtered_file2 = \
#         data_base + "tinyows_getcapabilities_layer_filtered_user2.xml"
#     capabilities_request_file = \
#         data_base + "tinyows_getcapabilities_request.xml"
#     describefeaturetype_request_file = \
#         data_base + "tinyows_describefeaturetype_request.xml"
#     describefeaturetype_request_multiple_file = \
#         data_base + "tinyows_describefeaturetype_request_multiple.xml"
#
#     def setUp(self):  # noqa
#         from c2cgeoportal.models import User, Role, LayerWMS, RestrictionArea, \
#             Interface, DBSession
#
#         # Always see the diff
#         # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
#         self.maxDiff = None
#
#         cleanup_db()
#
#         user1 = User(username="__test_user1", password="__test_user1")
#         role1 = Role(name="__test_role1", description="__test_role1")
#         user1.role_name = role1.name
#         user1.email = "Tarenpion"
#
#         user2 = User(username="__test_user2", password="__test_user2")
#         role2 = Role(name="__test_role2", description="__test_role2")
#         user2.role_name = role2.name
#         user2.email = "Tarenpion"
#
#         ogc_server_internal, _ = create_default_ogcserver()
#         main = Interface(name="main")
#
#         layer1 = LayerWMS("layer_1", public=False)
#         layer1.layer = "layer_1"
#         layer1.ogc_server = ogc_server_internal
#         layer1.interfaces = [main]
#
#         layer2 = LayerWMS("layer_2", public=False)
#         layer2.layer = "layer_2"
#         layer2.ogc_server = ogc_server_internal
#         layer2.interfaces = [main]
#
#         layer3 = LayerWMS("layer_3", public=False)
#         layer3.layer = "layer_3"
#         layer3.ogc_server = ogc_server_internal
#         layer3.interfaces = [main]
#
#         area = "POLYGON((-100 30, -100 50, 100 50, 100 30, -100 30))"
#         area = WKTElement(area, srid=21781)
#         restricted_area1 = RestrictionArea("__test_ra1", "", [layer1, layer2], [role1], area, readwrite=True)
#
#         area = "POLYGON((-100 0, -100 20, 100 20, 100 0, -100 0))"
#         area = WKTElement(area, srid=21781)
#         restricted_area2 = RestrictionArea("__test_ra2", "", [layer1, layer2, layer3], [role2], area)
#
#         DBSession.add_all([
#             user1, user2, role1, role2,
#             restricted_area1, restricted_area2
#         ])
#
#         transaction.commit()
#
#     @staticmethod
#     def tearDown():  # noqa
#         cleanup_db()
#
#     @staticmethod
#     def get_fake_proxy_(request, response_body, status):
#         from c2cgeoportal.views.tinyowsproxy import TinyOWSProxy
#         from types import MethodType
#
#         proxy = TinyOWSProxy(request)
#
#         def fake_proxy(self, url, params=None, method=None, cache=False, body=None, headers=None):
#             content = response_body
#
#             class FakeResponse(dict):
#                 pass
#             resp = FakeResponse()
#             resp.status = status
#             resp["content-type"] = "application/xml"
#
#             return resp, content
#
#         proxy._proxy = MethodType(fake_proxy, TinyOWSProxy)
#
#         return proxy
#
#     def test_proxy_not_auth(self):
#         from c2cgeoportal.views.tinyowsproxy import TinyOWSProxy
#         from pyramid.httpexceptions import HTTPUnauthorized
#
#         request = _create_dummy_request()
#         self.assertRaises(HTTPUnauthorized, TinyOWSProxy(request).proxy)
#
#     def test_proxy_get_capabilities_user1(self):
#         request = _create_dummy_request(username="__test_user1")
#         proxy = self.get_fake_proxy_(
#             request,
#             load_binfile(TestTinyOWSProxyView.capabilities_response_file),
#             200)
#
#         response = proxy.proxy()
#         filtered = load_file(TestTinyOWSProxyView.capabilities_response_filtered_file1)
#         body = response.body.decode("utf-8").replace("  \n", "")
#         self.assertEqual(
#             "\n".join(filtered.strip().split("\n")[2:]),
#             "\n".join(body.strip().split("\n")[2:]),
#         )
#         self.assertEqual("200 OK", response.status)
#
#     def test_proxy_get_capabilities_user2(self):
#         request = _create_dummy_request(username="__test_user2")
#         proxy = self.get_fake_proxy_(
#             request,
#             load_binfile(TestTinyOWSProxyView.capabilities_response_file),
#             200)
#
#         response = proxy.proxy()
#         filtered = load_file(TestTinyOWSProxyView.capabilities_response_filtered_file2)
#         body = response.body.decode("utf-8").replace("  \n", "")
#         self.assertEqual(
#             "\n".join(filtered.strip().split("\n")[2:]),
#             "\n".join(body.strip().split("\n")[2:]),
#         )
#         self.assertEqual("200 OK", response.status)
#
#     def test_proxy_get_capabilities_get(self):
#         request = _create_dummy_request(username="__test_user1")
#         request.params.update(dict(
#             service="wfs", version="1.1.0", request="GetCapabilities"
#         ))
#
#         proxy = self.get_fake_proxy_(
#             request,
#             load_binfile(TestTinyOWSProxyView.capabilities_response_file),
#             200)
#
#         response = proxy.proxy()
#         filtered = load_file(TestTinyOWSProxyView.capabilities_response_filtered_file1)
#         body = response.body.decode("utf-8").replace("  \n", "")
#         self.assertEqual(
#             "\n".join(filtered.strip().split("\n")[2:]),
#             "\n".join(body.strip().split("\n")[2:]),
#         )
#         self.assertEqual("200 OK", response.status)
#
#     def test_proxy_get_capabilities_post(self):
#         request = _create_dummy_request(username="__test_user1")
#         request.method = "POST"
#         request.body = load_file(
#             TestTinyOWSProxyView.capabilities_request_file)
#
#         proxy = self.get_fake_proxy_(
#             request,
#             load_binfile(TestTinyOWSProxyView.capabilities_response_file),
#             200)
#
#         response = proxy.proxy()
#         filtered = load_file(TestTinyOWSProxyView.capabilities_response_filtered_file1)
#         body = response.body.decode("utf-8").replace("  \n", "")
#         self.assertEqual(
#             "\n".join(filtered.strip().split("\n")[2:]),
#             "\n".join(body.strip().split("\n")[2:]),
#         )
#         self.assertEqual("200 OK", response.status)
#
#     def test_proxy_get_capabilities_post_invalid_body(self):
#         from pyramid.httpexceptions import HTTPBadRequest
#
#         request = _create_dummy_request(username="__test_user1")
#         request.method = "POST"
#         request.body = "This is not XML"
#
#         proxy = self.get_fake_proxy_(request, "".encode("utf-8"), None)
#         self.assertRaises(HTTPBadRequest, proxy.proxy)
#
#     def test_proxy_describe_feature_type_get(self):
#         request = _create_dummy_request(username="__test_user1")
#         request.registry.settings["tinyowsproxy"] = {
#             "tinyows_host": "demo.gmf.org",
#             "tinyows_url": "http://example.com",
#         }
#         request.params.update(dict(
#             service="wfs", version="1.1.0", request="DescribeFeatureType",
#             typename="tows:layer_1"
#         ))
#
#         proxy = self.get_fake_proxy_(request, "unfiltered response".encode("utf-8"), 200)
#
#         response = proxy.proxy()
#         self.assertEqual("200 OK", response.status)
#
#     def test_proxy_describe_feature_type_invalid_layer(self):
#         from pyramid.httpexceptions import HTTPForbidden
#
#         request = _create_dummy_request(username="__test_user1")
#         request.params.update(dict(
#             service="wfs", version="1.1.0", request="DescribeFeatureType",
#             typename="tows:layer_3"
#         ))
#
#         proxy = self.get_fake_proxy_(request, "".encode("utf-8"), None)
#         self.assertRaises(HTTPForbidden, proxy.proxy)
#
#     def test_proxy_describe_feature_type_post(self):
#         request = _create_dummy_request(username="__test_user1")
#         request.method = "POST"
#         request.body = load_binfile(TestTinyOWSProxyView.describefeaturetype_request_file)
#
#         proxy = self.get_fake_proxy_(request, "unfiltered response".encode("utf-8"), 200)
#
#         response = proxy.proxy()
#         self.assertEqual("200 OK", response.status)
#
#     def test_proxy_describe_feature_type_post_multiple_types(self):
#         from pyramid.httpexceptions import HTTPBadRequest
#
#         request = _create_dummy_request(username="__test_user1")
#         request.method = "POST"
#         request.body = load_binfile(TestTinyOWSProxyView.describefeaturetype_request_multiple_file)
#
#         proxy = self.get_fake_proxy_(request, "".encode("utf-8"), None)
#         self.assertRaises(HTTPBadRequest, proxy.proxy)
#
#
# @attr(functional=True)
# class TestTinyOWSProxyViewNoDb(TestCase):
#     data_base = "tests/data/"
#     capabilities_request_file = \
#         data_base + "tinyows_getcapabilities_request.xml"
#     describefeature_request_file = \
#         data_base + "tinyows_describefeaturetype_request.xml"
#     getfeature_request_file = \
#         data_base + "tinyows_getfeature_request.xml"
#     lockfeature_request_file = \
#         data_base + "tinyows_lockfeature_request.xml"
#     transaction_update_request_file = \
#         data_base + "tinyows_transaction_update_request.xml"
#     transaction_delete_request_file = \
#         data_base + "tinyows_transaction_delete_request.xml"
#     transaction_insert_request_file = \
#         data_base + "tinyows_transaction_insert_request.xml"
#
#     def setUp(self):  # noqa
#         # Always see the diff
#         # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
#         self.maxDiff = None
#
#         cleanup_db()
#         create_default_ogcserver()
#
#     @staticmethod
#     def tearDown():  # noqa
#         cleanup_db()
#
#     def test_parse_body_getcapabilities(self):
#         from c2cgeoportal.views.tinyowsproxy import TinyOWSProxy
#
#         request = _create_dummy_request()
#
#         capabilities_request = \
#             load_binfile(TestTinyOWSProxyViewNoDb.capabilities_request_file)
#         request.body = capabilities_request
#
#         proxy = TinyOWSProxy(request)
#         (operation, typename) = proxy._parse_body(request.body)
#         self.assertEqual("getcapabilities", operation)
#         self.assertEqual(set(), typename)
#
#     def test_parse_body_describefeaturetype(self):
#         from c2cgeoportal.views.tinyowsproxy import TinyOWSProxy
#
#         request = _create_dummy_request()
#
#         request.body = load_binfile(TestTinyOWSProxyViewNoDb.describefeature_request_file)
#
#         proxy = TinyOWSProxy(request)
#         (operation, typename) = proxy._parse_body(request.body)
#         self.assertEqual("describefeaturetype", operation)
#         self.assertEqual(set(["layer_1"]), typename)
#
#     def test_parse_body_getfeature(self):
#         from c2cgeoportal.views.tinyowsproxy import TinyOWSProxy
#
#         request = _create_dummy_request()
#
#         getfeature_request = load_binfile(TestTinyOWSProxyViewNoDb.getfeature_request_file)
#         request.body = getfeature_request
#
#         proxy = TinyOWSProxy(request)
#         (operation, typename) = proxy._parse_body(request.body)
#         self.assertEqual("getfeature", operation)
#         self.assertEqual({"parks"}, typename)
#
#     def test_parse_body_lockfeature(self):
#         from c2cgeoportal.views.tinyowsproxy import TinyOWSProxy
#
#         request = _create_dummy_request()
#
#         lockfeature_request = load_binfile(TestTinyOWSProxyViewNoDb.lockfeature_request_file)
#         request.body = lockfeature_request
#
#         proxy = TinyOWSProxy(request)
#         (operation, typename) = proxy._parse_body(request.body)
#         self.assertEqual("lockfeature", operation)
#         self.assertEqual({"parks"}, typename)
#
#     def test_parse_body_transaction_update(self):
#         from c2cgeoportal.views.tinyowsproxy import TinyOWSProxy
#
#         request = _create_dummy_request()
#
#         transaction_update_request = load_binfile(TestTinyOWSProxyViewNoDb.transaction_update_request_file)
#         request.body = transaction_update_request
#
#         proxy = TinyOWSProxy(request)
#         (operation, typename) = proxy._parse_body(request.body)
#         self.assertEqual("transaction", operation)
#         self.assertEqual({"parks"}, typename)
#
#     def test_parse_body_transaction_delete(self):
#         from c2cgeoportal.views.tinyowsproxy import TinyOWSProxy
#
#         request = _create_dummy_request()
#
#         transaction_delete_request = load_binfile(TestTinyOWSProxyViewNoDb.transaction_delete_request_file)
#         request.body = transaction_delete_request
#
#         proxy = TinyOWSProxy(request)
#         (operation, typename) = proxy._parse_body(request.body)
#         self.assertEqual("transaction", operation)
#         self.assertEqual({"parks"}, typename)
#
#     def test_parse_body_transaction_insert(self):
#         from c2cgeoportal.views.tinyowsproxy import TinyOWSProxy
#
#         request = _create_dummy_request()
#
#         transaction_insert_request = load_binfile(TestTinyOWSProxyViewNoDb.transaction_insert_request_file)
#         request.body = transaction_insert_request
#
#         proxy = TinyOWSProxy(request)
#         (operation, typename) = proxy._parse_body(request.body)
#         self.assertEqual("transaction", operation)
#         self.assertEqual({"parks"}, typename)
