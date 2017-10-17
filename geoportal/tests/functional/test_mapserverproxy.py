# -*- coding: utf-8 -*-

# Copyright (c) 2013-2017, Camptocamp SA
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


#
#
#                                       ^
#                                       |
#                                       |
#                                       |
#        +--------------------------------------------------------------+ area1
#        |  +--------------------------------------------------------+  |
#        |  |   p2       area3          |200045                 p3   |  |
#        |  +--------------------------------------------------------+  |
#        |               area1          |                               |
#        +--------------------------------------------------------------+
#                                       |
#        +--------------------------------------------------------------+
#        |               area2          |                               |
#    +---+--------------------------------------------------------------+-------->
#       599900   599910                 |               600090    600100)
#                                       |
#                                       |
#                                       |
#                                       |
#                                       |
#               p1                      |199955                    p4
#                                       |
#                                       |
#                                       +
#
#

import hashlib
from unittest2 import TestCase

from sqlalchemy import Column, types
import sqlalchemy.ext.declarative
from geoalchemy2 import Geometry, WKTElement
import transaction

from c2cgeoportal_geoportal.lib import functionality
from tests.functional import (  # noqa
    teardown_common as teardown_module,
    setup_common as setup_module,
    create_dummy_request, mapserv_url, create_default_ogcserver, cleanup_db
)

# GetMap hash for MapServer 6.0 and 7.0
FOUR_POINTS = ["61cbb0a6d18b72e4a28c1087019de245", "e2fe30a8085b0db4040c9ad0d331b6b8"]
TWO_POINTS = ["0a4fac2209d06c6fa36048c125b1679a", "0469e20ee04f22ab7ccdfebaa125f203"]
NO_POINT = ["ef33223235b26c782736c88933b35331", "aaa27d9450664d34fd8f53b6e76af1e1"]

Base = sqlalchemy.ext.declarative.declarative_base()


class PointTest(Base):
    __tablename__ = "testpoint"
    __table_args__ = {"schema": "geodata"}
    id = Column(types.Integer, primary_key=True)
    geom = Column(Geometry("POINT", srid=21781))
    name = Column(types.Unicode)
    city = Column(types.Unicode)
    country = Column(types.Unicode)


GETFEATURE_REQUEST = """<?xml version='1.0' encoding="UTF-8" ?>
<wfs:GetFeature xmlns:wfs="http://www.opengis.net/wfs" service="WFS" version="1.1.0" xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/1.1.0/wfs.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<wfs:Query typeName="feature:%(feature)s" srsName="EPSG:21781" xmlns:feature="http://mapserver.gis.umn.edu/mapserver">
<ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
<ogc:PropertyIs%(function)s matchCase="false" %(arguments)s>
<ogc:PropertyName>%(property)s</ogc:PropertyName>
<ogc:Literal>%(value)s</ogc:Literal>
</ogc:PropertyIs%(function)s>
</ogc:Filter>
</wfs:Query>
</wfs:GetFeature>"""

SUBSTITUTION_GETFEATURE_REQUEST = (GETFEATURE_REQUEST % {
    "feature": "testpoint_substitution",
    "function": "NotEqualTo",
    "arguments": "",
    "property": "name",
    "value": "toto",
}).encode("utf-8")

COLUMN_RESTRICTION_GETFEATURE_REQUEST = (GETFEATURE_REQUEST % {
    "feature": "testpoint_column_restriction",
    "function": "NotEqualTo",
    "arguments": "",
    "property": "name",
    "value": "bar",
}).encode("utf-8")


class TestMapserverproxyView(TestCase):

    def setup_method(self, _):
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import Role, LayerWMS, RestrictionArea, \
            Functionality, Interface, OGCServer, OGCSERVER_TYPE_GEOSERVER, OGCSERVER_AUTH_GEOSERVER
        from c2cgeoportal_commons.models.static import User

        cleanup_db()

        ogc_server_internal, _ = create_default_ogcserver()
        ogcserver_geoserver = OGCServer(name="__test_ogc_server_geoserver")
        ogcserver_geoserver.url = mapserv_url
        ogcserver_geoserver.type = OGCSERVER_TYPE_GEOSERVER
        ogcserver_geoserver.auth = OGCSERVER_AUTH_GEOSERVER

        PointTest.__table__.create(bind=DBSession.bind, checkfirst=True)

        geom = WKTElement("POINT(599910 199955)", srid=21781)
        p1 = PointTest(geom=geom, name="foo", city="Lausanne", country="Swiss")
        geom = WKTElement("POINT(599910 200045)", srid=21781)
        p2 = PointTest(geom=geom, name="bar", city="Chambéry", country="France")
        geom = WKTElement("POINT(600090 200045)", srid=21781)
        p3 = PointTest(geom=geom, name="éàè", city="Paris", country="France")
        geom = WKTElement("POINT(600090 199955)", srid=21781)
        p4 = PointTest(geom=geom, name="123", city="Londre", country="UK")

        pt1 = Functionality(name="print_template", value="1 Wohlen A4 portrait")
        pt2 = Functionality(name="print_template", value="2 Wohlen A3 landscape")
        user1 = User(username="__test_user1", password="__test_user1")
        role1 = Role(name="__test_role1", description="__test_role1", functionalities=[pt1, pt2])
        user1.role_name = role1.name
        user1.email = "Tarenpion"

        user2 = User(username="__test_user2", password="__test_user2")
        role2 = Role(name="__test_role2", description="__test_role2", functionalities=[pt1, pt2])
        user2.role_name = role2.name
        user2.email = "Tarenpion"

        user3 = User(username="__test_user3", password="__test_user3")
        role3 = Role(name="__test_role3", description="__test_role3", functionalities=[pt1, pt2])
        user3.role_name = role3.name

        main = Interface(name="main")

        layer2 = LayerWMS("testpoint_protected", public=False)
        layer2.layer = "testpoint_protected"
        layer2.ogc_server = ogc_server_internal
        layer2.interfaces = [main]

        layer3 = LayerWMS("testpoint_protected_query_with_collect", public=False)
        layer3.layer = "testpoint_protected_query_with_collect"
        layer3.ogc_server = ogc_server_internal
        layer3.interfaces = [main]

        area = "POLYGON((599900 200030, 599900 200050, 600100 200050, 600100 200030, 599900 200030))"
        area = WKTElement(area, srid=21781)
        restricted_area1 = RestrictionArea("__test_ra1", "", [layer2, layer3], [role1], area)

        area = "POLYGON((599900 200000, 599900 200020, 600100 200020, 600100 200000, 599900 200000))"
        area = WKTElement(area, srid=21781)
        restricted_area2 = RestrictionArea("__test_ra2", "", [layer2, layer3], [role2, role3], area)

        area = "POLYGON((599905 200043, 599905 200047, 600095 200047, 600095 200043, 599905 200043))"
        area = WKTElement(area, srid=21781)
        restricted_area3 = RestrictionArea("__test_ra3", "", [layer3], [role3], area, readwrite=True)

        DBSession.add_all([
            p1, p2, p3, p4, user1, user2, user3, role1, role2, role3,
            restricted_area1, restricted_area2, restricted_area3, ogcserver_geoserver
        ])
        DBSession.flush()

        self.id_lausanne = p1.id
        self.id_paris = p3.id
        self.ogc_server_id = ogc_server_internal.id
        self.role1_id = role1.id
        self.role2_id = role2.id
        self.role3_id = role3.id

        transaction.commit()

    def teardown_method(self, _):
        from c2cgeoportal_commons.models import DBSession

        functionality.FUNCTIONALITIES_TYPES = None

        cleanup_db()

        PointTest.__table__.drop(bind=DBSession.bind, checkfirst=True)

    @staticmethod
    def _create_dummy_request(username=None):
        request = create_dummy_request({
            "admin_interface": {
                "available_functionalities": [
                    "mapserver_substitution",
                    "print_template",
                ]
            }
        }, user=username)
        return request

    def test_no_params(self):
        from c2cgeoportal_geoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request()
        response = MapservProxy(request).proxy()
        self.assertEqual(response.status_code, 200)

    def test_get_legend_graphic(self):
        from c2cgeoportal_geoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request()
        request.params.update(dict(
            service="wms", version="1.1.1",
            request="getlegendgraphic",
            layer="testpoint_unprotected",
            srs="EPSG:21781",
            format="image/png",
            extraparam="with spéciàl chârs"
        ))
        response = MapservProxy(request).proxy()
        self.assertTrue(response.cache_control.public)
        self.assertEqual(response.cache_control.max_age, 3600)

    def test_getlegendgraphic_custom_nocache(self):
        from c2cgeoportal_geoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request()
        request.registry.settings.update({
            "headers": {
                "mapserver": {
                    "cache_control_max_age": 0,
                    "access_control_allow_origin": "*"
                }
            }
        })
        request.params.update(dict(
            service="wms", version="1.1.1",
            request="getlegendgraphic",
            layer="testpoint_unprotected",
            srs="EPSG:21781",
            format="image/png",
            extraparam="with spéciàl chârs"
        ))
        response = MapservProxy(request).proxy()
        self.assertTrue(response.cache_control.public)
        self.assertTrue(response.cache_control.no_cache)

    def test_get_feature_info(self):
        from c2cgeoportal_geoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request()
        request.params.update(dict(
            service="wms", version="1.1.1",
            request="getfeatureinfo", bbox="599910,199955,600090,200000",
            layers="testpoint_unprotected",
            query_layers="testpoint_unprotected",
            srs="EPSG:21781", format="image/png",
            info_format="application/vnd.ogc.gml",
            width="600", height="400", x="0", y="400"
        ))
        response = MapservProxy(request).proxy()

        expected_response = """
        <?xmlversion="1.0"encoding="UTF-8"?>
        <msGMLOutput
         xmlns:gml="http://www.opengis.net/gml"
         xmlns:xlink="http://www.w3.org/1999/xlink"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <testpoint_unprotected_layer>
        <gml:name>countries</gml:name>
                <testpoint_unprotected_feature>
                        <gml:boundedBy>
                                <gml:Box srsName="EPSG:21781">
                                        <gml:coordinates>599910.000000,199955.000000 599910.000000,199955.000000</gml:coordinates>
                                </gml:Box>
                        </gml:boundedBy>
                        <geom>
                        <gml:Point srsName="EPSG:21781">
                          <gml:coordinates>599910.000000,199955.000000</gml:coordinates>
                        </gml:Point>
                        </geom>
                        <name>foo</name>
                        <city>Lausanne</city>
                        <country>Swiss</country>
                </testpoint_unprotected_feature>
        </testpoint_unprotected_layer>
        </msGMLOutput>
        """
        import re
        pattern = re.compile(r"\s+")
        expected_response = "".join(
            re.sub(pattern, "", l) for l in expected_response.splitlines()
        )
        response_body = "".join(
            re.sub(pattern, "", l) for l in response.body.decode("utf-8").splitlines()
        ).encode("utf-8")
        self.assertEqual(response_body.decode("utf-8"), expected_response)
        self.assertEqual(str(response.cache_control), "max-age=0, no-cache")

    def test_get_feature_info_jsonp(self):
        from c2cgeoportal_geoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request()
        request.params.update(dict(
            service="wms", version="1.1.1",
            request="getfeatureinfo", bbox="599910,199955,600090,200000",
            layers="testpoint_unprotected",
            query_layers="testpoint_unprotected",
            srs="EPSG:21781", format="image/png",
            info_format="application/vnd.ogc.gml",
            width="600", height="400", x="0", y="400",
            callback="cb"
        ))
        response = MapservProxy(request).proxy()

        expected_response = """
        <?xmlversion="1.0"encoding="UTF-8"?>
        <msGMLOutput
         xmlns:gml="http://www.opengis.net/gml"
         xmlns:xlink="http://www.w3.org/1999/xlink"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <testpoint_unprotected_layer>
        <gml:name>countries</gml:name>
                <testpoint_unprotected_feature>
                        <gml:boundedBy>
                                <gml:Box srsName="EPSG:21781">
                                        <gml:coordinates>599910.000000,199955.000000 599910.000000,199955.000000</gml:coordinates>
                                </gml:Box>
                        </gml:boundedBy>
                        <geom>
                        <gml:Point srsName="EPSG:21781">
                          <gml:coordinates>599910.000000,199955.000000</gml:coordinates>
                        </gml:Point>
                        </geom>
                        <name>foo</name>
                        <city>Lausanne</city>
                        <country>Swiss</country>
                </testpoint_unprotected_feature>
        </testpoint_unprotected_layer>
        </msGMLOutput>
        """
        import re
        pattern = re.compile(r"\s+")
        expected_response = "".join(
            re.sub(pattern, "", l) for l in expected_response.splitlines()
        )
        expected_response = "{0!s}('{1!s}');".format("cb", expected_response)
        response_body = "".join(
            re.sub(pattern, "", l) for l in response.body.decode("utf-8").splitlines()
        )
        self.assertEqual(response_body, expected_response)
        self.assertFalse(response.cache_control.public)
        self.assertEqual(str(response.cache_control), "max-age=0, no-cache")

    def test_get_map_unprotected_layer_anonymous(self):
        from c2cgeoportal_geoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request()
        request.params.update(dict(
            service="wms", version="1.1.1", request="getmap",
            bbox="599820,199910,600180,200090", layers="testpoint_unprotected",
            width="600", height="400", srs="EPSG:21781", format="image/png"
        ))
        response = MapservProxy(request).proxy()

        self.assertTrue(response.status_int, 200)
        self.assertEqual(str(response.cache_control), "max-age=0, no-cache")
        # 4 points
        md5sum = hashlib.md5(response.body).hexdigest()
        self.assertIn(md5sum, FOUR_POINTS)

    def test_get_map_unprotected_layer_user1(self):
        from c2cgeoportal_geoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request(username="__test_user1")
        request.params.update(dict(
            service="wms", version="1.1.1", request="getmap",
            bbox="599820,199910,600180,200090", layers="testpoint_unprotected",
            width="600", height="400", srs="EPSG:21781", format="image/png"
        ))
        response = MapservProxy(request).proxy()

        self.assertTrue(response.status_int, 200)
        self.assertEqual(str(response.cache_control), "max-age=0, no-cache")
        # 4 points
        md5sum = hashlib.md5(response.body).hexdigest()
        self.assertIn(md5sum, FOUR_POINTS)

    def test_get_map_unprotected_layer_user2(self):
        from c2cgeoportal_geoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request(username="__test_user2")
        request.params.update(dict(
            service="wms", version="1.1.1", request="getmap",
            bbox="599820,199910,600180,200090", layers="testpoint_unprotected",
            width="600", height="400", srs="EPSG:21781", format="image/png"
        ))
        response = MapservProxy(request).proxy()

        self.assertTrue(response.status_int, 200)
        self.assertEqual(str(response.cache_control), "max-age=0, no-cache")
        # 4 points
        md5sum = hashlib.md5(response.body).hexdigest()
        self.assertIn(md5sum, FOUR_POINTS)

    def test_get_map_protected_layer_anonymous(self):
        from c2cgeoportal_geoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request()
        request.params.update(dict(
            service="wms", version="1.1.1", request="getmap",
            bbox="599820,199910,600180,200090", layers="testpoint_protected",
            width="600", height="400", srs="EPSG:21781", format="image/png"
        ))
        response = MapservProxy(request).proxy()

        self.assertTrue(response.status_int, 200)
        self.assertEqual(str(response.cache_control), "max-age=0, no-cache")
        # empty
        md5sum = hashlib.md5(response.body).hexdigest()
        self.assertIn(md5sum, NO_POINT)

    def test_get_map_protected_layer_user1(self):
        from c2cgeoportal_geoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request(username="__test_user1")
        request.params.update(dict(
            service="wms", version="1.1.1", request="getmap",
            bbox="599820,199910,600180,200090", layers="testpoint_protected",
            width="600", height="400", srs="EPSG:21781", format="image/png"
        ))
        response = MapservProxy(request).proxy()

        self.assertTrue(response.status_int, 200)
        self.assertEqual(str(response.cache_control), "max-age=0, no-cache")
        # two points
        md5sum = hashlib.md5(response.body).hexdigest()
        self.assertIn(md5sum, TWO_POINTS)

    def test_get_map_protected_layer_user2(self):
        from c2cgeoportal_geoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request(username="__test_user2")
        request.params.update(dict(
            service="wms", version="1.1.1", request="getmap",
            bbox="599820,199910,600180,200090", layers="testpoint_protected",
            width="600", height="400", srs="EPSG:21781", format="image/png"
        ))
        response = MapservProxy(request).proxy()

        self.assertEqual(str(response.cache_control), "max-age=0, no-cache")
        # empty
        md5sum = hashlib.md5(response.body).hexdigest()
        self.assertIn(md5sum, NO_POINT)

    def test_get_map_protected_layer_collect_query_user1(self):
        from c2cgeoportal_geoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request(username="__test_user1")
        request.params.update(dict(
            service="wms", version="1.1.1", request="getmap",
            bbox="599820,199910,600180,200090", layers="testpoint_protected_query_with_collect",
            width="600", height="400", srs="EPSG:21781", format="image/png"
        ))
        response = MapservProxy(request).proxy()

        self.assertTrue(response.status_int, 200)
        self.assertEqual(str(response.cache_control), "max-age=0, no-cache")
        # two points
        md5sum = hashlib.md5(response.body).hexdigest()
        self.assertIn(md5sum, TWO_POINTS)

    def test_get_map_protected_layer_collect_query_user2(self):
        from c2cgeoportal_geoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request(username="__test_user2")
        request.params.update(dict(
            service="wms", version="1.1.1", request="getmap",
            bbox="599820,199910,600180,200090", layers="testpoint_protected_query_with_collect",
            width="600", height="400", srs="EPSG:21781", format="image/png"
        ))
        response = MapservProxy(request).proxy()

        self.assertTrue(response.status_int, 200)
        self.assertEqual(str(response.cache_control), "max-age=0, no-cache")
        # empty
        md5sum = hashlib.md5(response.body).hexdigest()
        self.assertIn(md5sum, NO_POINT)

    def test_get_map_protected_layer_collect_query_user3(self):
        from c2cgeoportal_geoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request(username="__test_user3")
        request.params.update(dict(
            service="wms", version="1.1.1", request="getmap",
            bbox="599820,199910,600180,200090", layers="testpoint_protected_query_with_collect",
            width="600", height="400", srs="EPSG:21781", format="image/png"
        ))
        response = MapservProxy(request).proxy()

        self.assertTrue(response.status_int, 200)
        self.assertEqual(str(response.cache_control), "max-age=0, no-cache")
        # two points
        md5sum = hashlib.md5(response.body).hexdigest()
        self.assertIn(md5sum, TWO_POINTS)

    @staticmethod
    def _create_getcap_request(username=None, additional_settings=None):
        if additional_settings is None:
            additional_settings = {}
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User

        request = create_dummy_request(additional_settings)
        request.user = None if username is None else \
            DBSession.query(User).filter_by(username=username).one()
        return request

    def test_private_layer(self):
        from c2cgeoportal_geoportal.lib.filter_capabilities import get_private_layers

        pl = get_private_layers([self.ogc_server_id])
        self.assertEqual(
            {pl[l].name for l in pl},
            {"testpoint_protected", "testpoint_protected_query_with_collect"}
        )

    def test_protected_layers1(self):
        from c2cgeoportal_geoportal.lib.filter_capabilities import get_protected_layers

        pl = get_protected_layers(self.role1_id, [self.ogc_server_id])
        self.assertEqual(
            {pl[l].name for l in pl},
            {"testpoint_protected", "testpoint_protected_query_with_collect"}
        )

    def test_protected_layers2(self):
        from c2cgeoportal_geoportal.lib.filter_capabilities import get_protected_layers

        pl = get_protected_layers(self.role2_id, [self.ogc_server_id])
        self.assertEqual(
            {pl[l].name for l in pl},
            {"testpoint_protected", "testpoint_protected_query_with_collect"}
        )

    def test_protected_layers3(self):
        from c2cgeoportal_geoportal.lib.filter_capabilities import get_protected_layers

        pl = get_protected_layers(self.role3_id, [self.ogc_server_id])
        self.assertEqual(
            {pl[l].name for l in pl},
            {"testpoint_protected", "testpoint_protected_query_with_collect"}
        )

    def test_writable_layers1(self):
        from c2cgeoportal_geoportal.lib.filter_capabilities import get_writable_layers

        pl = get_writable_layers(self.role1_id, [self.ogc_server_id])
        self.assertEqual(
            {pl[l].name for l in pl}, set()
        )

    def test_writable_layers2(self):
        from c2cgeoportal_geoportal.lib.filter_capabilities import get_writable_layers

        pl = get_writable_layers(self.role2_id, [self.ogc_server_id])
        self.assertEqual(
            {pl[l].name for l in pl}, set()
        )

    def test_writable_layers3(self):
        from c2cgeoportal_geoportal.lib.filter_capabilities import get_writable_layers

        pl = get_writable_layers(self.role3_id, [self.ogc_server_id])
        self.assertEqual(
            {pl[l].name for l in pl},
            {"testpoint_protected_query_with_collect"}
        )

    def test_wms_get_capabilities(self):
        from c2cgeoportal_geoportal.views.mapserverproxy import MapservProxy

        request = self._create_getcap_request()
        request.params.update(dict(
            service="wms", version="1.1.1", request="getcapabilities",
        ))
        response = MapservProxy(request).proxy()
        assert "<Name>testpoint_protected</Name>" not in response.body.decode("utf-8")

        request = self._create_getcap_request(username="__test_user1")
        request.params.update(dict(
            service="wms", version="1.1.1", request="getcapabilities",
        ))
        response = MapservProxy(request).proxy()
        assert "<Name>testpoint_protected</Name>" in response.body.decode("utf-8")

    def test_wfs_get_capabilities(self):
        from c2cgeoportal_geoportal.views.mapserverproxy import MapservProxy

        request = self._create_getcap_request()
        request.params.update(dict(
            service="wfs", version="1.1.1", request="getcapabilities",
        ))
        response = MapservProxy(request).proxy()
        assert "<Name>testpoint_protected</Name>" not in response.body.decode("utf-8")

        request = self._create_getcap_request(username="__test_user1")
        request.params.update(dict(
            service="wfs", version="1.1.1", request="getcapabilities",
        ))
        response = MapservProxy(request).proxy()
        assert "<Name>testpoint_protected</Name>" in response.body.decode("utf-8")

    def _get_feature_is_equal_to(self, value):
        from c2cgeoportal_geoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request()

        request.method = "POST"
        request.body = (GETFEATURE_REQUEST % {
            "feature": "testpoint_unprotected",
            "function": "EqualTo",
            "arguments": "",
            "property": "name",
            "value": value,
        }).encode("utf-8")
        return MapservProxy(request).proxy()

    def test_get_feature_is_equal_to(self):
        response = self._get_feature_is_equal_to("foo")
        self.assertTrue(response.status_int, 200)
        assert "foo" in response.body.decode("utf-8")
        assert "bar" not in response.body.decode("utf-8")
        assert "éàè" not in response.body.decode("utf-8")
        assert "123" not in response.body.decode("utf-8")

        response = self._get_feature_is_equal_to("éàè")
        self.assertTrue(response.status_int, 200)  # 500)
        assert "foo" not in response.body.decode("utf-8")
        assert "bar" not in response.body.decode("utf-8")
        assert "éàè" in response.body.decode("utf-8")
        assert "123" not in response.body.decode("utf-8")

        response = self._get_feature_is_equal_to("123")
        self.assertTrue(response.status_int, 200)
        assert "foo" not in response.body.decode("utf-8")
        assert "bar" not in response.body.decode("utf-8")
        assert "éàè" not in response.body.decode("utf-8")
        assert "123" in response.body.decode("utf-8")

    def _get_feature_is_not_equal_to(self, value):
        from c2cgeoportal_geoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request()
        request.headers["Content-Type"] = "application/xml; charset=UTF-8"

        request.method = "POST"
        request.body = (GETFEATURE_REQUEST % {
            "feature": "testpoint_unprotected",
            "function": "NotEqualTo",
            "arguments": "",
            "property": "name",
            "value": value,
        }).encode("utf-8")
        return MapservProxy(request).proxy()

    def test_get_feature_is_not_equal_to(self):
        response = self._get_feature_is_not_equal_to("foo")
        self.assertTrue(response.status_int, 200)
        assert "foo" not in response.body.decode("utf-8")
        assert "bar" in response.body.decode("utf-8")
        assert "éàè" in response.body.decode("utf-8")
        assert "123" in response.body.decode("utf-8")

        response = self._get_feature_is_not_equal_to("éàè")
        self.assertTrue(response.status_int, 200)
        assert "foo" in response.body.decode("utf-8")
        assert "bar" in response.body.decode("utf-8")
        assert "éàè" not in response.body.decode("utf-8")
        assert "123" in response.body.decode("utf-8")

        response = self._get_feature_is_not_equal_to("123")
        self.assertTrue(response.status_int, 200)
        assert "foo" in response.body.decode("utf-8")
        assert "bar" in response.body.decode("utf-8")
        assert "éàè" in response.body.decode("utf-8")
        assert "123" not in response.body.decode("utf-8")

    def _get_feature_is_like(self, value):
        from c2cgeoportal_geoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request()

        request.method = "POST"
        request.body = (GETFEATURE_REQUEST % {
            "feature": "testpoint_unprotected",
            "function": "Like",
            "arguments": 'wildCard="*" singleChar="." escapeChar="!"',
            "property": "name",
            "value": value,
        }).encode("utf-8")
        return MapservProxy(request).proxy()

    def test_get_feature_is_like(self):
        response = self._get_feature_is_like("*o*")
        self.assertTrue(response.status_int, 200)
        assert "foo" in response.body.decode("utf-8")
        assert "bar" not in response.body.decode("utf-8")
        assert "éàè" not in response.body.decode("utf-8")
        assert "123" not in response.body.decode("utf-8")

        response = self._get_feature_is_like("*à*")
        self.assertTrue(response.status_int, 200)
        assert "foo" not in response.body.decode("utf-8")
        assert "bar" not in response.body.decode("utf-8")
        assert "éàè" in response.body.decode("utf-8")
        assert "123" not in response.body.decode("utf-8")

        response = self._get_feature_is_like("*2*")
        self.assertTrue(response.status_int, 200)
        assert "foo" not in response.body.decode("utf-8")
        assert "bar" not in response.body.decode("utf-8")
        assert "éàè" not in response.body.decode("utf-8")
        assert "123" in response.body.decode("utf-8")

    def test_get_feature_feature_id_get(self):
        from c2cgeoportal_geoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request()

        featureid = "{typename!s}.{fid1!s},{typename!s}.{fid2!s}".format(
            typename="testpoint_unprotected",
            fid1=self.id_lausanne,
            fid2=self.id_paris
        )
        request.params.update(dict(
            service="wfs", version="1.0.0",
            request="getfeature", typename="testpoint_unprotected",
            featureid=featureid
        ))
        response = MapservProxy(request).proxy()
        assert "Lausanne" in response.body.decode("utf-8")
        assert "Paris" in response.body.decode("utf-8")
        assert "Londre" not in response.body.decode("utf-8")
        assert "Chambéry" not in response.body.decode("utf-8")
        self.assertEqual(response.content_type, "text/xml")

    def test_get_feature_feature_id_get_jsonp(self):
        from c2cgeoportal_geoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request()

        featureid = "{typename!s}.{fid1!s},{typename!s}.{fid2!s}".format(
            typename="testpoint_unprotected",
            fid1=self.id_lausanne,
            fid2=self.id_paris
        )
        request.params.update(dict(
            service="wfs", version="1.0.0",
            request="getfeature", typename="testpoint_unprotected",
            featureid=featureid, callback="cb"
        ))
        response = MapservProxy(request).proxy()
        assert "Lausanne" in response.body.decode("utf-8")
        assert "Paris" in response.body.decode("utf-8")
        assert "Londre" not in response.body.decode("utf-8")
        assert "Chambéry" not in response.body.decode("utf-8")
        self.assertEqual(response.content_type, "application/javascript")

    def test_get_feature_wfs_url(self):
        from c2cgeoportal_geoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request()

        featureid = "{typename!s}.{fid1!s},{typename!s}.{fid2!s}".format(
            typename="testpoint_unprotected",
            fid1=self.id_lausanne,
            fid2=self.id_paris
        )
        request.params.update(dict(
            service="wfs", version="1.0.0",
            request="getfeature", typename="testpoint_unprotected",
            featureid=featureid, callback="cb"
        ))
        response = MapservProxy(request).proxy()

        self.assertTrue(response.body != "")
        self.assertEqual(str(response.cache_control), "max-age=0, no-cache")

    def test_get_feature_external_url(self):
        from c2cgeoportal_geoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request()

        featureid = "{typename!s}.{fid1!s},{typename!s}.{fid2!s}".format(
            typename="testpoint_unprotected",
            fid1=self.id_lausanne,
            fid2=self.id_paris
        )
        request.params.update(dict(
            service="wfs", version="1.0.0",
            request="getfeature", typename="testpoint_unprotected",
            featureid=featureid, callback="cb", EXTERNAL=1
        ))
        response = MapservProxy(request).proxy()

        self.assertTrue(response.body != "")
        self.assertEqual(str(response.cache_control), "max-age=0, no-cache")

    def test_get_feature_external_wfs_url(self):
        from c2cgeoportal_geoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request()

        featureid = "{typename!s}.{fid1!s},{typename!s}.{fid2!s}".format(
            typename="testpoint_unprotected",
            fid1=self.id_lausanne,
            fid2=self.id_paris
        )
        request.params.update(dict(
            service="wfs", version="1.0.0",
            request="getfeature", typename="testpoint_unprotected",
            featureid=featureid, callback="cb", EXTERNAL=1
        ))
        response = MapservProxy(request).proxy()

        self.assertTrue(response.body != "")
        self.assertEqual(str(response.cache_control), "max-age=0, no-cache")

    def test_substitution(self):
        from c2cgeoportal_geoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request()
        request.method = "POST"
        request.headers["Content-Type"] = "application/xml; charset=UTF-8"
        request.body = SUBSTITUTION_GETFEATURE_REQUEST

        response = MapservProxy(request).proxy()
        self.assertTrue(response.status_int, 200)
        assert "foo" in response.body.decode("utf-8")
        assert "bar" not in response.body.decode("utf-8")
        assert "éàè" not in response.body.decode("utf-8")
        assert "123" not in response.body.decode("utf-8")

        request.params.update(dict(s_name="bar"))
        response = MapservProxy(request).proxy()
        self.assertTrue(response.status_int, 200)
        assert "foo" in response.body.decode("utf-8")
        assert "bar" not in response.body.decode("utf-8")
        assert "éàè" not in response.body.decode("utf-8")
        assert "123" not in response.body.decode("utf-8")

        request = self._create_dummy_request()
        request.method = "POST"
        request.body = SUBSTITUTION_GETFEATURE_REQUEST
        request.params.update(dict(S_NAME="bar"))
        response = MapservProxy(request).proxy()
        self.assertTrue(response.status_int, 200)
        assert "foo" in response.body.decode("utf-8")
        assert "bar" not in response.body.decode("utf-8")
        assert "éàè" not in response.body.decode("utf-8")
        assert "123" not in response.body.decode("utf-8")

        request = self._create_dummy_request()
        request.method = "POST"
        request.body = SUBSTITUTION_GETFEATURE_REQUEST
        request.registry.settings["functionalities"]["anonymous"] = {
            "mapserver_substitution": ["name=bar"]
        }
        response = MapservProxy(request).proxy()
        self.assertTrue(response.status_int, 200)
        assert "foo" not in response.body.decode("utf-8")
        assert "bar" in response.body.decode("utf-8")
        assert "éàè" not in response.body.decode("utf-8")
        assert "123" not in response.body.decode("utf-8")

        request.body = COLUMN_RESTRICTION_GETFEATURE_REQUEST
        request.registry.settings["functionalities"]["anonymous"] = {
            "mapserver_substitution": ["cols=name", "cols=city", "cols=country"]
        }
        response = MapservProxy(request).proxy()
        self.assertTrue(response.status_int, 200)
        assert "Lausanne" in response.body.decode("utf-8")
        assert "Swiss" in response.body.decode("utf-8")

        request.registry.settings["functionalities"]["anonymous"] = {
            "mapserver_substitution": ["cols=name", "cols=city"]
        }
        response = MapservProxy(request).proxy()
        self.assertTrue(response.status_int, 200)
        assert "Lausanne" in response.body.decode("utf-8")
        assert "Swiss" not in response.body.decode("utf-8")

        request.registry.settings["functionalities"]["anonymous"] = {
            "mapserver_substitution": ["cols=name", "cols=country"]
        }
        response = MapservProxy(request).proxy()
        self.assertTrue(response.status_int, 200)
        assert "Lausanne" not in response.body.decode("utf-8")
        assert "Swiss" in response.body.decode("utf-8")

        request.registry.settings["functionalities"]["anonymous"] = {
            "mapserver_substitution": ["cols=name"]
        }
        response = MapservProxy(request).proxy()
        self.assertTrue(response.status_int, 200)
        assert "Lausanne" not in response.body.decode("utf-8")
        assert "Swiss" not in response.body.decode("utf-8")

        request = self._create_dummy_request()
        request.registry.settings["admin_interface"] = {"available_functionalities": [
            "mapserver_substitution"
        ]}
        request.method = "POST"
        request.body = SUBSTITUTION_GETFEATURE_REQUEST
        request.registry.settings["functionalities"]["anonymous"] = {
            "mapserver_substitution": ["foo_bar"]
        }
        request.params.update(dict(
            s_test1="to be removed", S_TEST2="to be removed"
        ))
        # just pass in the log message
        response = MapservProxy(request).proxy()

    def test_geoserver(self):
        from c2cgeoportal_geoportal.views.mapserverproxy import MapservProxy

        request = self._create_getcap_request(username="__test_user1", additional_settings={
            "mapserverproxy": {
                "default_ogc_server": "__test_ogc_server_geoserver",
            }
        })
        request.params.update(dict(
            service="wms", version="1.1.1", request="getcapabilities",
        ))
        response = MapservProxy(request).proxy()
        assert "<Name>testpoint_protected</Name>" in response.body.decode("utf-8")
