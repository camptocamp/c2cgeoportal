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
from nose.plugins.attrib import attr

from sqlalchemy import Column, types
from geoalchemy2 import Geometry, WKTElement
import transaction
import sqlahelper

from c2cgeoportal.lib import functionality
from c2cgeoportal.tests.functional import (  # noqa
    tear_down_common as tearDownModule,
    set_up_common as setUpModule,
    create_dummy_request, mapserv_url, create_default_ogcserver,
)

Base = sqlahelper.get_base()

# GetMap hash for MapServer 6.0 and 7.0
FOUR_POINTS = ["61cbb0a6d18b72e4a28c1087019de245", "e2fe30a8085b0db4040c9ad0d331b6b8"]
TWO_POINTS = ["0a4fac2209d06c6fa36048c125b1679a", "0469e20ee04f22ab7ccdfebaa125f203"]
NO_POINT = ["ef33223235b26c782736c88933b35331", "aaa27d9450664d34fd8f53b6e76af1e1"]


class TestPoint(Base):
    __tablename__ = "testpoint"
    __table_args__ = {"schema": "geodata"}
    id = Column(types.Integer, primary_key=True)
    geom = Column(Geometry("POINT", srid=21781))
    name = Column(types.Unicode)
    city = Column(types.Unicode)
    country = Column(types.Unicode)


GETFEATURE_REQUEST = u"""<?xml version='1.0' encoding="UTF-8" ?>
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
    "feature": u"testpoint_substitution",
    "function": u"NotEqualTo",
    "arguments": u"",
    "property": u"name",
    "value": "toto",
}).encode("utf-8")

COLUMN_RESTRICTION_GETFEATURE_REQUEST = (GETFEATURE_REQUEST % {
    "feature": u"testpoint_column_restriction",
    "function": u"NotEqualTo",
    "arguments": u"",
    "property": u"name",
    "value": "bar",
}).encode("utf-8")


@attr(functional=True)
class TestMapserverproxyView(TestCase):

    def setUp(self):  # noqa
        self.maxDiff = None

        from c2cgeoportal.models import User, Role, LayerWMS, RestrictionArea, \
            Functionality, Interface, DBSession, OGCServer, \
            OGCSERVER_TYPE_GEOSERVER, OGCSERVER_AUTH_GEOSERVER

        ogc_server_internal, _ = create_default_ogcserver()
        ogcserver_geoserver = OGCServer(name="__test_ogc_server_geoserver")
        ogcserver_geoserver.url = mapserv_url
        ogcserver_geoserver.type = OGCSERVER_TYPE_GEOSERVER
        ogcserver_geoserver.auth = OGCSERVER_AUTH_GEOSERVER

        TestPoint.__table__.create(bind=DBSession.bind, checkfirst=True)

        geom = WKTElement("POINT(599910 199955)", srid=21781)
        p1 = TestPoint(geom=geom, name=u"foo", city=u"Lausanne", country=u"Swiss")
        geom = WKTElement("POINT(599910 200045)", srid=21781)
        p2 = TestPoint(geom=geom, name=u"bar", city=u"Chambéry", country=u"France")
        geom = WKTElement("POINT(600090 200045)", srid=21781)
        p3 = TestPoint(geom=geom, name=u"éàè", city=u"Paris", country=u"France")
        geom = WKTElement("POINT(600090 199955)", srid=21781)
        p4 = TestPoint(geom=geom, name=u"123", city=u"Londre", country=u"UK")

        pt1 = Functionality(name=u"print_template", value=u"1 Wohlen A4 portrait")
        pt2 = Functionality(name=u"print_template", value=u"2 Wohlen A3 landscape")
        user1 = User(username=u"__test_user1", password=u"__test_user1")
        role1 = Role(name=u"__test_role1", description=u"__test_role1", functionalities=[pt1, pt2])
        user1.role_name = role1.name
        user1.email = u"Tarenpion"

        user2 = User(username=u"__test_user2", password=u"__test_user2")
        role2 = Role(name=u"__test_role2", description=u"__test_role2", functionalities=[pt1, pt2])
        user2.role_name = role2.name
        user2.email = u"Tarenpion"

        user3 = User(username=u"__test_user3", password=u"__test_user3")
        role3 = Role(name=u"__test_role3", description=u"__test_role3", functionalities=[pt1, pt2])
        user3.role_name = role3.name

        main = Interface(name=u"main")

        layer2 = LayerWMS(u"testpoint_protected", public=False)
        layer2.layer = u"testpoint_protected"
        layer2.ogc_server = ogc_server_internal
        layer2.interfaces = [main]

        layer3 = LayerWMS(u"testpoint_protected_query_with_collect", public=False)
        layer3.layer = u"testpoint_protected_query_with_collect"
        layer3.ogc_server = ogc_server_internal
        layer3.interfaces = [main]

        area = "POLYGON((599900 200030, 599900 200050, 600100 200050, 600100 200030, 599900 200030))"
        area = WKTElement(area, srid=21781)
        restricted_area1 = RestrictionArea(u"__test_ra1", u"", [layer2, layer3], [role1], area)

        area = "POLYGON((599900 200000, 599900 200020, 600100 200020, 600100 200000, 599900 200000))"
        area = WKTElement(area, srid=21781)
        restricted_area2 = RestrictionArea(u"__test_ra2", u"", [layer2, layer3], [role2, role3], area)

        area = "POLYGON((599905 200043, 599905 200047, 600095 200047, 600095 200043, 599905 200043))"
        area = WKTElement(area, srid=21781)
        restricted_area3 = RestrictionArea(u"__test_ra3", u"", [layer3], [role3], area, readwrite=True)

        DBSession.add_all([
            p1, p2, p3, p4, user1, user2, user3, role1, role2, role3,
            restricted_area1, restricted_area2, restricted_area3, ogcserver_geoserver
        ])
        DBSession.flush()

        self.id_lausanne = p1.id
        self.id_paris = p3.id

        transaction.commit()

    @staticmethod
    def tearDown():  # noqa
        from c2cgeoportal.models import User, Role, LayerWMS, RestrictionArea, \
            Functionality, Interface, DBSession, OGCServer

        functionality.FUNCTIONALITIES_TYPES = None

        DBSession.query(User).filter(User.username == "__test_user1").delete()
        DBSession.query(User).filter(User.username == "__test_user2").delete()
        DBSession.query(User).filter(User.username == "__test_user3").delete()

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
        ra = DBSession.query(RestrictionArea).filter(
            RestrictionArea.name == "__test_ra3"
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
        r = DBSession.query(Role).filter(Role.name == "__test_role3").one()
        r.functionalities = []
        DBSession.delete(r)

        DBSession.query(Functionality).filter(Functionality.value == u"1 Wohlen A4 portrait").delete()
        DBSession.query(Functionality).filter(Functionality.value == u"2 Wohlen A3 landscape").delete()
        for layer in DBSession.query(LayerWMS).filter(LayerWMS.name == "testpoint_unprotected").all():
            DBSession.delete(layer)  # pragma: no cover
        for layer in DBSession.query(LayerWMS).filter(LayerWMS.name == "testpoint_protected").all():
            DBSession.delete(layer)
        for layer in DBSession.query(LayerWMS).filter(LayerWMS.name == "testpoint_protected_query_with_collect").all():
            DBSession.delete(layer)
        DBSession.query(Interface).filter(
            Interface.name == "main"
        ).delete()
        DBSession.query(OGCServer).delete()

        transaction.commit()
        DBSession.query(TestPoint).delete()

    def assert_contains(self, body, text):
        decoded_body = unicode(body.decode("utf-8"))
        self.assertTrue(decoded_body.find(text) >= 0, u"Unable to find '{}' in:\n{}".format(text, decoded_body))

    def assert_not_contains(self, body, text):
        decoded_body = unicode(body.decode("utf-8"))
        self.assertTrue(decoded_body.find(text) < 0, u"Find unexpected text '{}' in:\n{}".format(text, decoded_body))

    @staticmethod
    def _create_dummy_request(username=None):
        from c2cgeoportal.models import DBSession, User

        request = create_dummy_request({
            "admin_interface": {
                "available_functionalities": [
                    "mapserver_substitution",
                    "print_template",
                ]
            }
        })
        request.user = None if username is None else \
            DBSession.query(User).filter_by(username=username).one()
        return request

    def test_no_params(self):
        from c2cgeoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request()
        response = MapservProxy(request).proxy()
        self.assertEqual(response.status_code, 200)

    def test_get_legend_graphic(self):
        from c2cgeoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request()
        request.params.update(dict(
            service="wms", version="1.1.1",
            request="getlegendgraphic",
            layer="testpoint_unprotected",
            srs="EPSG:21781",
            format="image/png",
            extraparam=u"with spéciàl chârs"
        ))
        response = MapservProxy(request).proxy()
        self.assertTrue(response.cache_control.public)
        self.assertEqual(response.cache_control.max_age, 3600)

    def test_getlegendgraphic_custom_nocache(self):
        from c2cgeoportal.views.mapserverproxy import MapservProxy

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
            extraparam=u"with spéciàl chârs"
        ))
        response = MapservProxy(request).proxy()
        self.assertTrue(response.cache_control.public)
        self.assertTrue(response.cache_control.no_cache)

    def test_get_feature_info(self):
        from c2cgeoportal.views.mapserverproxy import MapservProxy

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
            re.sub(pattern, "", l) for l in response.body.splitlines()
        )
        self.assertEqual(response_body, expected_response)
        self.assertEqual(str(response.cache_control), "max-age=0, no-cache")

    def test_get_feature_info_jsonp(self):
        from c2cgeoportal.views.mapserverproxy import MapservProxy

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
            re.sub(pattern, "", l) for l in response.body.splitlines()
        )
        self.assertEqual(response_body, expected_response)
        self.assertFalse(response.cache_control.public)
        self.assertEqual(str(response.cache_control), "max-age=0, no-cache")

    def test_get_map_unprotected_layer_anonymous(self):
        from c2cgeoportal.views.mapserverproxy import MapservProxy

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
        from c2cgeoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request(username=u"__test_user1")
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
        from c2cgeoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request(username=u"__test_user2")
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
        from c2cgeoportal.views.mapserverproxy import MapservProxy

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
        from c2cgeoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request(username=u"__test_user1")
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
        from c2cgeoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request(username=u"__test_user2")
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
        from c2cgeoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request(username=u"__test_user1")
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
        from c2cgeoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request(username=u"__test_user2")
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
        from c2cgeoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request(username=u"__test_user3")
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
        from c2cgeoportal.models import DBSession, User

        request = create_dummy_request(additional_settings)
        request.user = None if username is None else \
            DBSession.query(User).filter_by(username=username).one()
        return request

    def test_wms_get_capabilities(self):
        from c2cgeoportal.views.mapserverproxy import MapservProxy

        request = self._create_getcap_request()
        request.params.update(dict(
            service="wms", version="1.1.1", request="getcapabilities",
        ))
        response = MapservProxy(request).proxy()
        self.assert_not_contains(response.body, "<Name>testpoint_protected</Name>")

        request = self._create_getcap_request(username=u"__test_user1")
        request.params.update(dict(
            service="wms", version="1.1.1", request="getcapabilities",
        ))
        response = MapservProxy(request).proxy()
        self.assert_contains(response.body, "<Name>testpoint_protected</Name>")

    def test_wfs_get_capabilities(self):
        from c2cgeoportal.views.mapserverproxy import MapservProxy

        request = self._create_getcap_request()
        request.params.update(dict(
            service="wfs", version="1.1.1", request="getcapabilities",
        ))
        response = MapservProxy(request).proxy()
        self.assert_not_contains(response.body, "<Name>testpoint_protected</Name>")

        request = self._create_getcap_request(username=u"__test_user1")
        request.params.update(dict(
            service="wfs", version="1.1.1", request="getcapabilities",
        ))
        response = MapservProxy(request).proxy()
        self.assert_contains(response.body, "<Name>testpoint_protected</Name>")

    def _get_feature_is_equal_to(self, value):
        from c2cgeoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request()

        request.method = "POST"
        request.body = (GETFEATURE_REQUEST % {
            "feature": u"testpoint_unprotected",
            "function": u"EqualTo",
            "arguments": u"",
            "property": u"name",
            "value": value,
        }).encode("utf-8")
        return MapservProxy(request).proxy()

    def test_get_feature_is_equal_to(self):
        response = self._get_feature_is_equal_to(u"foo")
        self.assertTrue(response.status_int, 200)
        self.assert_contains(response.body, u"foo")
        self.assert_not_contains(response.body, u"bar")
        self.assert_not_contains(response.body, u"éàè")
        self.assert_not_contains(response.body, u"123")

        response = self._get_feature_is_equal_to(u"éàè")
        self.assertTrue(response.status_int, 200)  # 500)
        self.assert_not_contains(response.body, u"foo")
        self.assert_not_contains(response.body, u"bar")
        self.assert_contains(response.body, u"éàè")
        self.assert_not_contains(response.body, u"123")

        response = self._get_feature_is_equal_to(u"123")
        self.assertTrue(response.status_int, 200)
        self.assert_not_contains(response.body, u"foo")
        self.assert_not_contains(response.body, u"bar")
        self.assert_not_contains(response.body, u"éàè")
        self.assert_contains(response.body, u"123")

    def _get_feature_is_not_equal_to(self, value):
        from c2cgeoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request()
        request.headers["Content-Type"] = "application/xml; charset=UTF-8"

        request.method = "POST"
        request.body = (GETFEATURE_REQUEST % {
            "feature": u"testpoint_unprotected",
            "function": u"NotEqualTo",
            "arguments": u"",
            "property": u"name",
            "value": value,
        }).encode("utf-8")
        return MapservProxy(request).proxy()

    def test_get_feature_is_not_equal_to(self):
        response = self._get_feature_is_not_equal_to(u"foo")
        self.assertTrue(response.status_int, 200)
        self.assert_not_contains(response.body, u"foo")
        self.assert_contains(response.body, u"bar")
        self.assert_contains(response.body, u"éàè")
        self.assert_contains(response.body, u"123")

        response = self._get_feature_is_not_equal_to(u"éàè")
        self.assertTrue(response.status_int, 200)
        self.assert_contains(response.body, u"foo")
        self.assert_contains(response.body, u"bar")
        self.assert_not_contains(response.body, u"éàè")
        self.assert_contains(response.body, u"123")

        response = self._get_feature_is_not_equal_to(u"123")
        self.assertTrue(response.status_int, 200)
        self.assert_contains(response.body, u"foo")
        self.assert_contains(response.body, u"bar")
        self.assert_contains(response.body, u"éàè")
        self.assert_not_contains(response.body, u"123")

    def _get_feature_is_like(self, value):
        from c2cgeoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request()

        request.method = "POST"
        request.body = (GETFEATURE_REQUEST % {
            "feature": u"testpoint_unprotected",
            "function": u"Like",
            "arguments": u'wildCard="*" singleChar="." escapeChar="!"',
            "property": u"name",
            "value": value,
        }).encode("utf-8")
        return MapservProxy(request).proxy()

    def test_get_feature_is_like(self):
        response = self._get_feature_is_like(u"*o*")
        self.assertTrue(response.status_int, 200)
        self.assert_contains(response.body, u"foo")
        self.assert_not_contains(response.body, u"bar")
        self.assert_not_contains(response.body, u"éàè")
        self.assert_not_contains(response.body, u"123")

        response = self._get_feature_is_like(u"*à*")
        self.assertTrue(response.status_int, 200)
        self.assert_not_contains(response.body, u"foo")
        self.assert_not_contains(response.body, u"bar")
        self.assert_contains(response.body, u"éàè")
        self.assert_not_contains(response.body, u"123")

        response = self._get_feature_is_like(u"*2*")
        self.assertTrue(response.status_int, 200)
        self.assert_not_contains(response.body, u"foo")
        self.assert_not_contains(response.body, u"bar")
        self.assert_not_contains(response.body, u"éàè")
        self.assert_contains(response.body, u"123")

    def test_get_feature_feature_id_get(self):
        from c2cgeoportal.views.mapserverproxy import MapservProxy

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
        self.assert_contains(response.body, u"Lausanne")
        self.assert_contains(response.body, u"Paris")
        self.assert_not_contains(response.body, u"Londre")
        self.assert_not_contains(response.body, u"Chambéry")
        self.assertEqual(response.content_type, "text/xml")

    def test_get_feature_feature_id_get_jsonp(self):
        from c2cgeoportal.views.mapserverproxy import MapservProxy

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
        self.assert_contains(response.body, u"Lausanne")
        self.assert_contains(response.body, u"Paris")
        self.assert_not_contains(response.body, u"Londre")
        self.assert_not_contains(response.body, u"Chambéry")
        self.assertEqual(response.content_type, "application/javascript")

    def test_get_feature_wfs_url(self):
        from c2cgeoportal.views.mapserverproxy import MapservProxy

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
        from c2cgeoportal.views.mapserverproxy import MapservProxy

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
        from c2cgeoportal.views.mapserverproxy import MapservProxy

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
        from c2cgeoportal.views.mapserverproxy import MapservProxy

        request = self._create_dummy_request()
        request.method = "POST"
        request.headers["Content-Type"] = "application/xml; charset=UTF-8"
        request.body = SUBSTITUTION_GETFEATURE_REQUEST

        response = MapservProxy(request).proxy()
        self.assertTrue(response.status_int, 200)
        self.assert_contains(response.body, u"foo")
        self.assert_not_contains(response.body, u"bar")
        self.assert_not_contains(response.body, u"éàè")
        self.assert_not_contains(response.body, u"123")

        request.params.update(dict(s_name="bar"))
        response = MapservProxy(request).proxy()
        self.assertTrue(response.status_int, 200)
        self.assert_contains(response.body, u"foo")
        self.assert_not_contains(response.body, u"bar")
        self.assert_not_contains(response.body, u"éàè")
        self.assert_not_contains(response.body, u"123")

        request = self._create_dummy_request()
        request.method = "POST"
        request.body = SUBSTITUTION_GETFEATURE_REQUEST
        request.params.update(dict(S_NAME="bar"))
        response = MapservProxy(request).proxy()
        self.assertTrue(response.status_int, 200)
        self.assert_contains(response.body, u"foo")
        self.assert_not_contains(response.body, u"bar")
        self.assert_not_contains(response.body, u"éàè")
        self.assert_not_contains(response.body, u"123")

        request = self._create_dummy_request()
        request.method = "POST"
        request.body = SUBSTITUTION_GETFEATURE_REQUEST
        request.registry.settings["functionalities"]["anonymous"] = {
            "mapserver_substitution": ["name=bar"]
        }
        response = MapservProxy(request).proxy()
        self.assertTrue(response.status_int, 200)
        self.assert_not_contains(response.body, u"foo")
        self.assert_contains(response.body, u"bar")
        self.assert_not_contains(response.body, u"éàè")
        self.assert_not_contains(response.body, u"123")

        request.body = COLUMN_RESTRICTION_GETFEATURE_REQUEST
        request.registry.settings["functionalities"]["anonymous"] = {
            "mapserver_substitution": ["cols=name", "cols=city", "cols=country"]
        }
        response = MapservProxy(request).proxy()
        self.assertTrue(response.status_int, 200)
        self.assert_contains(response.body, u"Lausanne")
        self.assert_contains(response.body, u"Swiss")

        request.registry.settings["functionalities"]["anonymous"] = {
            "mapserver_substitution": ["cols=name", "cols=city"]
        }
        response = MapservProxy(request).proxy()
        self.assertTrue(response.status_int, 200)
        self.assert_contains(response.body, u"Lausanne")
        self.assert_not_contains(response.body, u"Swiss")

        request.registry.settings["functionalities"]["anonymous"] = {
            "mapserver_substitution": ["cols=name", "cols=country"]
        }
        response = MapservProxy(request).proxy()
        self.assertTrue(response.status_int, 200)
        self.assert_not_contains(response.body, u"Lausanne")
        self.assert_contains(response.body, u"Swiss")

        request.registry.settings["functionalities"]["anonymous"] = {
            "mapserver_substitution": ["cols=name"]
        }
        response = MapservProxy(request).proxy()
        self.assertTrue(response.status_int, 200)
        self.assert_not_contains(response.body, u"Lausanne")
        self.assert_not_contains(response.body, u"Swiss")

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
        from c2cgeoportal.views.mapserverproxy import MapservProxy

        request = self._create_getcap_request(username=u"__test_user1", additional_settings={
            "mapserverproxy": {
                "default_ogc_server": "__test_ogc_server_geoserver",
            }
        })
        request.params.update(dict(
            service="wms", version="1.1.1", request="getcapabilities",
        ))
        response = MapservProxy(request).proxy()
        self.assert_contains(response.body, u"<Name>testpoint_protected</Name>")
