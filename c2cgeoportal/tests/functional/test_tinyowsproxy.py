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


from unittest2 import TestCase
from nose.plugins.attrib import attr

from geoalchemy2 import WKTElement
import transaction
import sqlahelper

from c2cgeoportal.tests import load_file
from c2cgeoportal.tests.functional import (  # noqa
    tear_down_common as tearDownModule,
    set_up_common as setUpModule,
    create_dummy_request, mapserv_url)

Base = sqlahelper.get_base()


def _create_dummy_request(username=None):
    from c2cgeoportal.models import DBSession, User

    request = create_dummy_request({
        "tinyowsproxy": {
            "tinyows_url": "http://localhost/tinyows",
            "online_resource": "http://domain.com/tinyows_proxy",
            "proxy_online_resource": "http://domain.com/tinyows"
        }
    })
    request.user = None if username is None else \
        DBSession.query(User).filter_by(username=username).one()
    return request


@attr(functional=True)
class TestTinyOWSProxyView(TestCase):
    data_base = "c2cgeoportal/tests/data/"
    capabilities_response_file = \
        data_base + "tinyows_getcapabilities_layer.xml"
    capabilities_response_filtered_file1 = \
        data_base + "tinyows_getcapabilities_layer_filtered_user1.xml"
    capabilities_response_filtered_file2 = \
        data_base + "tinyows_getcapabilities_layer_filtered_user2.xml"
    capabilities_request_file = \
        data_base + "tinyows_getcapabilities_request.xml"
    describefeaturetype_request_file = \
        data_base + "tinyows_describefeaturetype_request.xml"
    describefeaturetype_request_multiple_file = \
        data_base + "tinyows_describefeaturetype_request_multiple.xml"

    @staticmethod
    def setUp():  # noqa
        from c2cgeoportal.models import User, Role, LayerV1, RestrictionArea, \
            Interface, DBSession

        user1 = User(username=u"__test_user1", password=u"__test_user1")
        role1 = Role(name=u"__test_role1", description=u"__test_role1")
        user1.role_name = role1.name
        user1.email = u"Tarenpion"

        user2 = User(username=u"__test_user2", password=u"__test_user2")
        role2 = Role(name=u"__test_role2", description=u"__test_role2")
        user2.role_name = role2.name
        user2.email = u"Tarenpion"

        main = Interface(name=u"main")

        layer1 = LayerV1(u"layer_1", public=False)
        layer1.interfaces = [main]
        layer2 = LayerV1(u"layer_2", public=False)
        layer2.interfaces = [main]
        layer3 = LayerV1(u"layer_3", public=False)
        layer3.interfaces = [main]

        area = "POLYGON((-100 30, -100 50, 100 50, 100 30, -100 30))"
        area = WKTElement(area, srid=21781)
        restricted_area1 = RestrictionArea(u"__test_ra1", u"", [layer1, layer2], [role1], area, readwrite=True)

        area = "POLYGON((-100 0, -100 20, 100 20, 100 0, -100 0))"
        area = WKTElement(area, srid=21781)
        restricted_area2 = RestrictionArea(u"__test_ra2", u"", [layer1, layer2, layer3], [role2], area)

        DBSession.add_all([
            user1, user2, role1, role2,
            restricted_area1, restricted_area2
        ])
        DBSession.flush()

        transaction.commit()

    @staticmethod
    def tearDown():  # noqa
        from c2cgeoportal.models import User, Role, LayerV1, RestrictionArea, \
            Interface, DBSession

        DBSession.query(User).filter(User.username == "__test_user1").delete()
        DBSession.query(User).filter(User.username == "__test_user2").delete()

        ra = DBSession.query(RestrictionArea).filter(
            RestrictionArea.name == "__test_ra1"
        ).one()
        ra.roles = []
        ra.layers = []
        DBSession.delete(ra)
        ra = DBSession.query(RestrictionArea).filter(
            RestrictionArea.name == "__test_ra2"
        ).one()
        ra.roles = []
        ra.layers = []
        DBSession.delete(ra)

        r = DBSession.query(Role).filter(Role.name == "__test_role1").one()
        r.functionalities = []
        DBSession.delete(r)
        r = DBSession.query(Role).filter(Role.name == "__test_role2").one()
        r.functionalities = []
        DBSession.delete(r)

        for layer in DBSession.query(LayerV1).filter(LayerV1.name == "layer_1").all():
            DBSession.delete(layer)  # pragma: no cover
        for layer in DBSession.query(LayerV1).filter(LayerV1.name == "layer_2").all():
            DBSession.delete(layer)
        for layer in DBSession.query(LayerV1).filter(LayerV1.name == "layer_3").all():
            DBSession.delete(layer)
        DBSession.query(Interface).filter(
            Interface.name == "main"
        ).delete()

        transaction.commit()

    @staticmethod
    def get_fake_proxy_(request, response_body, status):
        from c2cgeoportal.views.tinyowsproxy import TinyOWSProxy
        from types import MethodType

        proxy = TinyOWSProxy(request)

        def fake_proxy(self, url, params=None, method=None, cache=False, body=None, headers=None):
            content = response_body

            class FakeResponse(dict):
                pass
            resp = FakeResponse()
            resp.status = status
            resp["content-type"] = "application/xml"

            return resp, content

        proxy._proxy = MethodType(fake_proxy, proxy, TinyOWSProxy)

        return proxy

    def test_proxy_not_auth(self):
        from c2cgeoportal.views.tinyowsproxy import TinyOWSProxy
        from pyramid.httpexceptions import HTTPUnauthorized

        request = _create_dummy_request()
        self.assertRaises(HTTPUnauthorized, TinyOWSProxy(request).proxy)

    def test_proxy_get_capabilities_user1(self):
        request = _create_dummy_request(username=u"__test_user1")
        proxy = self.get_fake_proxy_(
            request,
            load_file(TestTinyOWSProxyView.capabilities_response_file),
            200)

        response = proxy.proxy()
        filtered = load_file(
            TestTinyOWSProxyView.capabilities_response_filtered_file1)
        response.body = response.body.replace("  \n", "")
        self.assertEquals(filtered, response.body)
        self.assertEquals("200 OK", response.status)

    def test_proxy_get_capabilities_user2(self):
        request = _create_dummy_request(username=u"__test_user2")
        proxy = self.get_fake_proxy_(
            request,
            load_file(TestTinyOWSProxyView.capabilities_response_file),
            200)

        response = proxy.proxy()
        filtered = load_file(
            TestTinyOWSProxyView.capabilities_response_filtered_file2)
        response.body = response.body.replace("  \n", "")
        self.assertEquals(filtered, response.body)
        self.assertEquals("200 OK", response.status)

    def test_proxy_get_capabilities_get(self):
        request = _create_dummy_request(username=u"__test_user1")
        request.params.update(dict(
            service="wfs", version="1.1.0", request="GetCapabilities"
        ))

        proxy = self.get_fake_proxy_(
            request,
            load_file(TestTinyOWSProxyView.capabilities_response_file),
            200)

        response = proxy.proxy()
        filtered = load_file(
            TestTinyOWSProxyView.capabilities_response_filtered_file1)
        response.body = response.body.replace("  \n", "")
        self.assertEquals(filtered, response.body)
        self.assertEquals("200 OK", response.status)

    def test_proxy_get_capabilities_post(self):
        request = _create_dummy_request(username=u"__test_user1")
        request.method = "POST"
        request.body = load_file(
            TestTinyOWSProxyView.capabilities_request_file)

        proxy = self.get_fake_proxy_(
            request,
            load_file(TestTinyOWSProxyView.capabilities_response_file),
            200)

        response = proxy.proxy()
        filtered = load_file(
            TestTinyOWSProxyView.capabilities_response_filtered_file1)
        response.body = response.body.replace("  \n", "")
        self.assertEquals(filtered, response.body)
        self.assertEquals("200 OK", response.status)

    def test_proxy_get_capabilities_post_invalid_body(self):
        from pyramid.httpexceptions import HTTPBadRequest

        request = _create_dummy_request(username=u"__test_user1")
        request.method = "POST"
        request.body = "This is not XML"

        proxy = self.get_fake_proxy_(request, "", None)
        self.assertRaises(HTTPBadRequest, proxy.proxy)

    def test_proxy_describe_feature_type_get(self):
        request = _create_dummy_request(username=u"__test_user1")
        request.registry.settings["tinyowsproxy"] = {
            "tinyows_host": "demo.gmf.org",
            "tinyows_url": "http://example.com",
        }
        request.params.update(dict(
            service="wfs", version="1.1.0", request="DescribeFeatureType",
            typename="tows:layer_1"
        ))

        proxy = self.get_fake_proxy_(request, "unfiltered response", 200)

        response = proxy.proxy()
        self.assertEquals("200 OK", response.status)

    def test_proxy_describe_feature_type_invalid_layer(self):
        from pyramid.httpexceptions import HTTPForbidden

        request = _create_dummy_request(username=u"__test_user1")
        request.params.update(dict(
            service="wfs", version="1.1.0", request="DescribeFeatureType",
            typename="tows:layer_3"
        ))

        proxy = self.get_fake_proxy_(request, "", None)
        self.assertRaises(HTTPForbidden, proxy.proxy)

    def test_proxy_describe_feature_type_post(self):
        request = _create_dummy_request(username=u"__test_user1")
        request.method = "POST"
        request.body = load_file(
            TestTinyOWSProxyView.describefeaturetype_request_file)

        proxy = self.get_fake_proxy_(request, "unfiltered response", 200)

        response = proxy.proxy()
        self.assertEquals("200 OK", response.status)

    def test_proxy_describe_feature_type_post_multiple_types(self):
        from pyramid.httpexceptions import HTTPBadRequest

        request = _create_dummy_request(username=u"__test_user1")
        request.method = "POST"
        request.body = load_file(
            TestTinyOWSProxyView.describefeaturetype_request_multiple_file)

        proxy = self.get_fake_proxy_(request, "", None)
        self.assertRaises(HTTPBadRequest, proxy.proxy)


@attr(functional=True)
class TestTinyOWSProxyViewNoDb(TestCase):
    data_base = "c2cgeoportal/tests/data/"
    capabilities_request_file = \
        data_base + "tinyows_getcapabilities_request.xml"
    describefeature_request_file = \
        data_base + "tinyows_describefeaturetype_request.xml"
    getfeature_request_file = \
        data_base + "tinyows_getfeature_request.xml"
    lockfeature_request_file = \
        data_base + "tinyows_lockfeature_request.xml"
    transaction_update_request_file = \
        data_base + "tinyows_transaction_update_request.xml"
    transaction_delete_request_file = \
        data_base + "tinyows_transaction_delete_request.xml"
    transaction_insert_request_file = \
        data_base + "tinyows_transaction_insert_request.xml"

    def test_parse_body_getcapabilities(self):
        from c2cgeoportal.views.tinyowsproxy import TinyOWSProxy

        request = _create_dummy_request()

        capabilities_request = \
            load_file(TestTinyOWSProxyViewNoDb.capabilities_request_file)
        request.body = capabilities_request

        proxy = TinyOWSProxy(request)
        (operation, typename) = proxy._parse_body(request.body)
        self.assertEquals("getcapabilities", operation)
        self.assertEquals(set(), typename)

    def test_parse_body_describefeaturetype(self):
        from c2cgeoportal.views.tinyowsproxy import TinyOWSProxy

        request = _create_dummy_request()

        describefeature_request = \
            load_file(TestTinyOWSProxyViewNoDb.describefeature_request_file)
        request.body = describefeature_request

        proxy = TinyOWSProxy(request)
        (operation, typename) = proxy._parse_body(request.body)
        self.assertEquals("describefeaturetype", operation)
        self.assertEquals(set(["layer_1"]), typename)

    def test_parse_body_getfeature(self):
        from c2cgeoportal.views.tinyowsproxy import TinyOWSProxy

        request = _create_dummy_request()

        getfeature_request = \
            load_file(TestTinyOWSProxyViewNoDb.getfeature_request_file)
        request.body = getfeature_request

        proxy = TinyOWSProxy(request)
        (operation, typename) = proxy._parse_body(request.body)
        self.assertEquals("getfeature", operation)
        self.assertEquals(set(["parks"]), typename)

    def test_parse_body_lockfeature(self):
        from c2cgeoportal.views.tinyowsproxy import TinyOWSProxy

        request = _create_dummy_request()

        lockfeature_request = \
            load_file(TestTinyOWSProxyViewNoDb.lockfeature_request_file)
        request.body = lockfeature_request

        proxy = TinyOWSProxy(request)
        (operation, typename) = proxy._parse_body(request.body)
        self.assertEquals("lockfeature", operation)
        self.assertEquals(set(["parks"]), typename)

    def test_parse_body_transaction_update(self):
        from c2cgeoportal.views.tinyowsproxy import TinyOWSProxy

        request = _create_dummy_request()

        transaction_update_request = \
            load_file(TestTinyOWSProxyViewNoDb.transaction_update_request_file)
        request.body = transaction_update_request

        proxy = TinyOWSProxy(request)
        (operation, typename) = proxy._parse_body(request.body)
        self.assertEquals("transaction", operation)
        self.assertEquals(set(["parks"]), typename)

    def test_parse_body_transaction_delete(self):
        from c2cgeoportal.views.tinyowsproxy import TinyOWSProxy

        request = _create_dummy_request()

        transaction_delete_request = \
            load_file(TestTinyOWSProxyViewNoDb.transaction_delete_request_file)
        request.body = transaction_delete_request

        proxy = TinyOWSProxy(request)
        (operation, typename) = proxy._parse_body(request.body)
        self.assertEquals("transaction", operation)
        self.assertEquals(set(["parks"]), typename)

    def test_parse_body_transaction_insert(self):
        from c2cgeoportal.views.tinyowsproxy import TinyOWSProxy

        request = _create_dummy_request()

        transaction_insert_request = \
            load_file(TestTinyOWSProxyViewNoDb.transaction_insert_request_file)
        request.body = transaction_insert_request

        proxy = TinyOWSProxy(request)
        (operation, typename) = proxy._parse_body(request.body)
        self.assertEquals("transaction", operation)
        self.assertEquals(set(["parks"]), typename)
