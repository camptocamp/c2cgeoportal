# Copyright (c) 2015-2025, Camptocamp SA
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

# pylint: disable=missing-docstring,attribute-defined-outside-init,protected-access

from unittest import TestCase

import pytest
import responses
import transaction
from geoalchemy2 import WKTElement

from tests import load_file
from tests.functional import (
    cleanup_db,
    create_default_ogcserver,
    create_dummy_request,
    setup_db,
)
from tests.functional import setup_common as setup_module  # noqa
from tests.functional import teardown_common as teardown_module  # noqa


def _create_dummy_request(username=None):
    from c2cgeoportal_commons.models import DBSession
    from c2cgeoportal_commons.models.static import User

    request = create_dummy_request(
        {
            "tinyowsproxy": {
                "tinyows_url": "http://localhost/tinyows",
                "ogc_server": "__test_ogc_server",
                # "online_resource": "http://domain.com/tinyows_proxy",
                # "proxy_online_resource": "http://domain.com/tinyows"
            },
        },
    )
    request.user = None if username is None else DBSession.query(User).filter_by(username=username).one()
    return request


class TestTinyOWSProxyView(TestCase):
    data_base = "tests/data/"
    capabilities_response_file = data_base + "tinyows_getcapabilities_layer.xml"
    capabilities_response_filtered_file1 = data_base + "tinyows_getcapabilities_layer_filtered_user1.xml"
    capabilities_response_filtered_file2 = data_base + "tinyows_getcapabilities_layer_filtered_user2.xml"
    capabilities_request_file = data_base + "tinyows_getcapabilities_request.xml"
    describefeaturetype_request_file = data_base + "tinyows_describefeaturetype_request.xml"
    describefeaturetype_request_multiple_file = data_base + "tinyows_describefeaturetype_request_multiple.xml"

    def setup_method(self, _) -> None:
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import (
            Interface,
            LayerWMS,
            RestrictionArea,
            Role,
        )
        from c2cgeoportal_commons.models.static import User

        setup_db()

        user1 = User(username="__test_user1", password="__test_user1")
        role1 = Role(name="__test_role1", description="__test_role1")
        user1.roles = [role1]
        user1.email = "Tarenpion"

        user2 = User(username="__test_user2", password="__test_user2")
        role2 = Role(name="__test_role2", description="__test_role2")
        user2.roles = [role2]
        user2.email = "Tarenpion"

        ogc_server_internal = create_default_ogcserver(DBSession)

        main = Interface(name="main")

        layer1 = LayerWMS("layer_1", public=False)
        layer1.layer = "layer_1"
        layer1.ogc_server = ogc_server_internal
        layer1.interfaces = [main]

        layer2 = LayerWMS("layer_2", public=False)
        layer2.layer = "layer_2"
        layer2.ogc_server = ogc_server_internal
        layer2.interfaces = [main]

        layer3 = LayerWMS("layer_3", public=False)
        layer3.layer = "layer_3"
        layer3.ogc_server = ogc_server_internal
        layer3.interfaces = [main]

        area = "POLYGON((-100 30, -100 50, 100 50, 100 30, -100 30))"
        area = WKTElement(area, srid=21781)
        restricted_area1 = RestrictionArea("__test_ra1", "", [layer1, layer2], [role1], area, readwrite=True)

        area = "POLYGON((-100 0, -100 20, 100 20, 100 0, -100 0))"
        area = WKTElement(area, srid=21781)
        restricted_area2 = RestrictionArea("__test_ra2", "", [layer1, layer2, layer3], [role2], area)

        DBSession.add_all([user1, user2, role1, role2, restricted_area1, restricted_area2])

        transaction.commit()

    def teardown_method(self, _) -> None:
        cleanup_db()

    def test_proxy_not_auth(self) -> None:
        from c2cgeoportal_geoportal.views.tinyowsproxy import TinyOWSProxy
        from pyramid.httpexceptions import HTTPUnauthorized

        request = _create_dummy_request()

        with pytest.raises(HTTPUnauthorized):
            TinyOWSProxy(request).proxy()

    @responses.activate
    def test_proxy_get_capabilities_user1(self) -> None:
        from c2cgeoportal_geoportal.views.tinyowsproxy import TinyOWSProxy

        request = _create_dummy_request(username="__test_user1")

        responses.get(
            url="http://localhost/tinyows",
            body=load_file(self.capabilities_response_file),
        )

        response = TinyOWSProxy(request).proxy()

        assert (
            load_file(self.capabilities_response_filtered_file1).strip()
            == response.body.decode().replace("  \n", "").strip()
        )
        assert response.status == "200 OK"

    @responses.activate
    def test_proxy_get_capabilities_user2(self) -> None:
        from c2cgeoportal_geoportal.views.tinyowsproxy import TinyOWSProxy

        request = _create_dummy_request(username="__test_user2")

        responses.get(
            url="http://localhost/tinyows",
            body=load_file(self.capabilities_response_file),
        )

        response = TinyOWSProxy(request).proxy()

        assert (
            load_file(self.capabilities_response_filtered_file2).strip()
            == response.body.decode().replace("  \n", "").strip()
        )
        assert response.status == "200 OK"

    @responses.activate
    def test_proxy_get_capabilities_get(self) -> None:
        from c2cgeoportal_geoportal.views.tinyowsproxy import TinyOWSProxy

        request = _create_dummy_request(username="__test_user1")
        request.params.update(dict(service="wfs", version="1.1.0", request="GetCapabilities"))

        responses.get(
            url="http://localhost/tinyows",
            body=load_file(self.capabilities_response_file),
        )

        response = TinyOWSProxy(request).proxy()

        assert (
            load_file(self.capabilities_response_filtered_file1).strip()
            == response.body.decode().replace("  \n", "").strip()
        )
        assert response.status == "200 OK"

    @responses.activate
    def test_proxy_get_capabilities_post(self) -> None:
        from c2cgeoportal_geoportal.views.tinyowsproxy import TinyOWSProxy

        request = _create_dummy_request(username="__test_user1")
        request.method = "POST"
        request.body = load_file(TestTinyOWSProxyView.capabilities_request_file)

        responses.post(
            url="http://localhost/tinyows",
            body=load_file(self.capabilities_response_file),
        )

        response = TinyOWSProxy(request).proxy()

        assert (
            load_file(self.capabilities_response_filtered_file1).strip()
            == response.body.decode().replace("  \n", "").strip()
        )

        assert response.status == "200 OK"

    def test_proxy_get_capabilities_post_invalid_body(self) -> None:
        from c2cgeoportal_geoportal.views.tinyowsproxy import TinyOWSProxy
        from pyramid.httpexceptions import HTTPBadRequest

        request = _create_dummy_request(username="__test_user1")
        request.method = "POST"
        request.body = "This is not XML"

        # proxy = self.get_fake_proxy_(request, "", None)
        with pytest.raises(HTTPBadRequest):
            TinyOWSProxy(request).proxy()

    @responses.activate
    def test_proxy_describe_feature_type_get(self) -> None:
        from c2cgeoportal_geoportal.views.tinyowsproxy import TinyOWSProxy

        request = _create_dummy_request(username="__test_user1")
        request.registry.settings["tinyowsproxy"].update(
            {
                "tinyows_host": "demo.gmf.org",
                "tinyows_url": "http://example.com",
            },
        )
        request.params.update(
            dict(service="wfs", version="1.1.0", request="DescribeFeatureType", typename="tows:layer_1"),
        )

        responses.get(
            url="http://example.com/",
            body="unfiltered response",
        )

        response = TinyOWSProxy(request).proxy()

        assert response.status == "200 OK"

    def test_proxy_describe_feature_type_invalid_layer(self) -> None:
        from c2cgeoportal_geoportal.views.tinyowsproxy import TinyOWSProxy
        from pyramid.httpexceptions import HTTPForbidden

        request = _create_dummy_request(username="__test_user1")
        request.params.update(
            dict(service="wfs", version="1.1.0", request="DescribeFeatureType", typename="tows:layer_3"),
        )

        with pytest.raises(HTTPForbidden):
            TinyOWSProxy(request).proxy()

    @responses.activate
    def test_proxy_describe_feature_type_post(self) -> None:
        from c2cgeoportal_geoportal.views.tinyowsproxy import TinyOWSProxy

        request = _create_dummy_request(username="__test_user1")
        request.method = "POST"
        request.body = load_file(TestTinyOWSProxyView.describefeaturetype_request_file)

        responses.post(
            url="http://localhost/tinyows",
            body="unfiltered response",
        )

        response = TinyOWSProxy(request).proxy()

        assert response.status == "200 OK"

    def test_proxy_describe_feature_type_post_multiple_types(self) -> None:
        from c2cgeoportal_geoportal.views.tinyowsproxy import TinyOWSProxy
        from pyramid.httpexceptions import HTTPBadRequest

        request = _create_dummy_request(username="__test_user1")
        request.method = "POST"
        request.body = load_file(TestTinyOWSProxyView.describefeaturetype_request_multiple_file)

        with pytest.raises(HTTPBadRequest):
            TinyOWSProxy(request).proxy()


class TestTinyOWSProxyViewNoDb(TestCase):
    data_base = "tests/data/"
    capabilities_request_file = data_base + "tinyows_getcapabilities_request.xml"
    describefeature_request_file = data_base + "tinyows_describefeaturetype_request.xml"
    getfeature_request_file = data_base + "tinyows_getfeature_request.xml"
    lockfeature_request_file = data_base + "tinyows_lockfeature_request.xml"
    transaction_update_request_file = data_base + "tinyows_transaction_update_request.xml"
    transaction_delete_request_file = data_base + "tinyows_transaction_delete_request.xml"
    transaction_insert_request_file = data_base + "tinyows_transaction_insert_request.xml"

    def setup_method(self, _) -> None:
        from c2cgeoportal_commons.models import DBSession

        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None

        cleanup_db()
        create_default_ogcserver(DBSession)

    def teardown_method(self, _) -> None:
        cleanup_db()

    def test_parse_body_getcapabilities(self) -> None:
        from c2cgeoportal_geoportal.views.tinyowsproxy import TinyOWSProxy

        request = _create_dummy_request()
        request.body = load_file(TestTinyOWSProxyViewNoDb.capabilities_request_file)

        (operation, typename) = TinyOWSProxy(request)._parse_body(request.body)

        assert operation == "getcapabilities"
        assert set() == typename

    def test_parse_body_describefeaturetype(self) -> None:
        from c2cgeoportal_geoportal.views.tinyowsproxy import TinyOWSProxy

        request = _create_dummy_request()
        request.body = load_file(TestTinyOWSProxyViewNoDb.describefeature_request_file)

        (operation, typename) = TinyOWSProxy(request)._parse_body(request.body)

        assert operation == "describefeaturetype"
        assert {"layer_1"} == typename

    def test_parse_body_getfeature(self) -> None:
        from c2cgeoportal_geoportal.views.tinyowsproxy import TinyOWSProxy

        request = _create_dummy_request()
        request.body = load_file(TestTinyOWSProxyViewNoDb.getfeature_request_file)

        (operation, typename) = TinyOWSProxy(request)._parse_body(request.body)

        assert operation == "getfeature"
        assert {"parks"} == typename

    def test_parse_body_lockfeature(self) -> None:
        from c2cgeoportal_geoportal.views.tinyowsproxy import TinyOWSProxy

        request = _create_dummy_request()
        request.body = load_file(TestTinyOWSProxyViewNoDb.lockfeature_request_file)

        (operation, typename) = TinyOWSProxy(request)._parse_body(request.body)

        assert operation == "lockfeature"
        assert {"parks"} == typename

    def test_parse_body_transaction_update(self) -> None:
        from c2cgeoportal_geoportal.views.tinyowsproxy import TinyOWSProxy

        request = _create_dummy_request()
        request.body = load_file(TestTinyOWSProxyViewNoDb.transaction_update_request_file)

        (operation, typename) = TinyOWSProxy(request)._parse_body(request.body)

        assert operation == "transaction"
        assert {"parks"} == typename

    def test_parse_body_transaction_delete(self) -> None:
        from c2cgeoportal_geoportal.views.tinyowsproxy import TinyOWSProxy

        request = _create_dummy_request()
        request.body = load_file(TestTinyOWSProxyViewNoDb.transaction_delete_request_file)

        (operation, typename) = TinyOWSProxy(request)._parse_body(request.body)

        assert operation == "transaction"
        assert {"parks"} == typename

    def test_parse_body_transaction_insert(self) -> None:
        from c2cgeoportal_geoportal.views.tinyowsproxy import TinyOWSProxy

        request = _create_dummy_request()
        request.body = load_file(TestTinyOWSProxyViewNoDb.transaction_insert_request_file)

        (operation, typename) = TinyOWSProxy(request)._parse_body(request.body)

        assert operation == "transaction"
        assert {"parks"} == typename
