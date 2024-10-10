# Copyright (c) 2022-2024, Camptocamp SA
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

import asyncio
from unittest import TestCase

import pyramid.httpexceptions
import pytest
import responses
import transaction
from pyramid import testing
from tests.functional import create_default_ogcserver, create_dummy_request
from tests.functional import setup_common as setup_module  # noqa
from tests.functional import teardown_common as teardown_module  # noqa

from c2cgeoportal_geoportal.lib import caching

CAP = """<?xml version="1.0" encoding="utf-8"?>
<WMT_MS_Capabilities version="1.1.1">
<Service></Service>
<Capability>
  <Request></Request>
  <Layer queryable="1">
    <Name>demo</Name>
    <SRS>EPSG:2056</SRS>
    <LatLonBoundingBox minx="5.03255" miny="45.4755" maxx="10.6348" maxy="47.9095"></LatLonBoundingBox>
    <BoundingBox SRS="EPSG:2056" minx="2.42e+06" miny="1.0405e+06" maxx="2.839e+06" maxy="1.3064e+06"></BoundingBox>

    <Layer queryable="1" opaque="0" cascaded="0">
        <Name>__test_layer_internal_wms</Name>
        <SRS>EPSG:2056</SRS>
        <LatLonBoundingBox minx="5.75095" miny="45.7775" maxx="10.6348" maxy="47.9095"></LatLonBoundingBox>
        <BoundingBox SRS="EPSG:2056" minx="2.47374e+06" miny="1.0741e+06" maxx="2.839e+06" maxy="1.3064e+06"></BoundingBox>
        <MetadataURL type="TC211">
          <Format>text/xml</Format>
          <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:type="simple" xlink:href="https://geomapfish-demo-2-7.camptocamp.com/mapserv_proxy?ogcserver=Main+PNG&amp;request=GetMetadata&amp;layer=police"></OnlineResource>
        </MetadataURL>
        <Style>
          <Name>default</Name>
          <Title>default</Title>
          <LegendURL width="117" height="35">
             <Format>image/png</Format>
             <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:type="simple" xlink:href="https://geomapfish-demo-2-7.camptocamp.com/mapserv_proxy?ogcserver=Main+PNG&amp;version=1.1.1&amp;service=WMS&amp;request=GetLegendGraphic&amp;layer=police&amp;format=image/png&amp;STYLE=default"></OnlineResource>
          </LegendURL>
        </Style>
      <Layer queryable="1" opaque="0" cascaded="0">
          <Name>{name2}</Name>
          <SRS>EPSG:2056</SRS>
          <LatLonBoundingBox minx="5.75095" miny="45.7775" maxx="10.6348" maxy="47.9095"></LatLonBoundingBox>
          <BoundingBox SRS="EPSG:2056" minx="2.47374e+06" miny="1.0741e+06" maxx="2.839e+06" maxy="1.3064e+06"></BoundingBox>
          <MetadataURL type="TC211">
            <Format>text/xml</Format>
            <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:type="simple" xlink:href="https://geomapfish-demo-2-7.camptocamp.com/mapserv_proxy?ogcserver=Main+PNG&amp;request=GetMetadata&amp;layer=post_office"></OnlineResource>
          </MetadataURL>
          <Style>
            <Name>default</Name>
            <Title>default</Title>
            <LegendURL width="116" height="35">
               <Format>image/png</Format>
               <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:type="simple" xlink:href="https://geomapfish-demo-2-7.camptocamp.com/mapserv_proxy?ogcserver=Main+PNG&amp;version=1.1.1&amp;service=WMS&amp;request=GetLegendGraphic&amp;layer=post_office&amp;format=image/png&amp;STYLE=default"></OnlineResource>
            </LegendURL>
          </Style>
      </Layer>
    </Layer>
  </Layer>
</Capability>
</WMT_MS_Capabilities>"""

DFT = """<?xml version='1.0' encoding="UTF-8" ?>
<schema
   targetNamespace="http://mapserver.gis.umn.edu/mapserver"
   xmlns:ms="http://mapserver.gis.umn.edu/mapserver"
   xmlns:ogc="http://www.opengis.net/ogc"
   xmlns:xsd="http://www.w3.org/2001/XMLSchema"
   xmlns="http://www.w3.org/2001/XMLSchema"
   xmlns:gml="http://www.opengis.net/gml"
   elementFormDefault="qualified" version="0.1" >

  <import namespace="http://www.opengis.net/gml"
          schemaLocation="http://schemas.opengis.net/gml/2.1.2/feature.xsd" />

  <element name="hotel_label"
           type="ms:Character"
           substitutionGroup="gml:_Feature" />

  <complexType name="hotel_labelType">
    <complexContent>
      <extension base="gml:AbstractFeatureType">
        <sequence>
          <element name="way" type="gml:PointPropertyType" minOccurs="0" maxOccurs="1"/>
          <element name="display_name" minOccurs="0" type="string"/>
          <element name="name" minOccurs="0" type="string"/>
          <element name="osm_id" minOccurs="0" type="long"/>
          <element name="access" minOccurs="0" type="string"/>
          <element name="aerialway" minOccurs="0" type="string"/>
          <element name="amenity" minOccurs="0" type="string"/>
          <element name="barrier" minOccurs="0" type="string"/>
          <element name="bicycle" minOccurs="0" type="string"/>
          <element name="brand" minOccurs="0" type="string"/>
          <element name="building" minOccurs="0" type="string"/>
          <element name="covered" minOccurs="0" type="string"/>
          <element name="denomination" minOccurs="0" type="string"/>
          <element name="ele" minOccurs="0" type="string"/>
          <element name="foot" minOccurs="0" type="string"/>
          <element name="highway" minOccurs="0" type="string"/>
          <element name="layer" minOccurs="0" type="string"/>
          <element name="leisure" minOccurs="0" type="string"/>
          <element name="man_made" minOccurs="0" type="string"/>
          <element name="motorcar" minOccurs="0" type="string"/>
          <element name="natural" minOccurs="0" type="string"/>
          <element name="operator" minOccurs="0" type="string"/>
          <element name="population" minOccurs="0" type="string"/>
          <element name="power" minOccurs="0" type="string"/>
          <element name="place" minOccurs="0" type="string"/>
          <element name="railway" minOccurs="0" type="string"/>
          <element name="ref" minOccurs="0" type="string"/>
          <element name="religion" minOccurs="0" type="string"/>
          <element name="shop" minOccurs="0" type="string"/>
          <element name="sport" minOccurs="0" type="string"/>
          <element name="surface" minOccurs="0" type="string"/>
          <element name="tourism" minOccurs="0" type="string"/>
          <element name="waterway" minOccurs="0" type="string"/>
          <element name="wood" minOccurs="0" type="string"/>
        </sequence>
      </extension>
    </complexContent>
  </complexType>

  <element name="{name2}"
           type="ms:Character"
           substitutionGroup="gml:_Feature" />

  <complexType name="{name2}Type">
    <complexContent>
      <extension base="gml:AbstractFeatureType">
        <sequence>
          <element name="way" type="gml:PointPropertyType" minOccurs="0" maxOccurs="1"/>
          <element name="name" minOccurs="0" type="string"/>
          <element name="osm_id" minOccurs="0" type="long"/>
        </sequence>
      </extension>
    </complexContent>
  </complexType>
</schema>
"""


class TestThemesView(TestCase):
    def setup_method(self, _):
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import Interface, LayerWMS, Theme

        main = Interface(name="desktop")

        ogc_server_internal = create_default_ogcserver(DBSession)

        layer_internal_wms = LayerWMS(name="__test_layer_internal_wms", public=True)
        layer_internal_wms.layer = "__test_layer_internal_wms"
        layer_internal_wms.interfaces = [main]
        layer_internal_wms.ogc_server = ogc_server_internal

        theme = Theme(name="__test_theme")
        theme.interfaces = [
            main,
        ]
        theme.children = [layer_internal_wms]

        DBSession.add_all([theme])

        self.std_cache = {}
        self.ogc_cache = {}
        caching.MEMORY_CACHE_DICT.clear()

        caching.init_region(
            {"backend": "dogpile.cache.memory", "arguments": {"cache_dict": self.std_cache}}, "std"
        )
        caching.init_region({"backend": "dogpile.cache.memory"}, "obj")
        caching.init_region(
            {"backend": "dogpile.cache.memory", "arguments": {"cache_dict": self.ogc_cache}}, "ogc-server"
        )

        transaction.commit()

    def teardown_method(self, _):
        testing.tearDown()

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import Dimension, Interface, Metadata, OGCServer, TreeItem

        for item in DBSession.query(TreeItem).all():
            DBSession.delete(item)
        DBSession.query(Interface).filter(Interface.name == "main").delete()
        DBSession.query(OGCServer).delete()

        transaction.commit()

    @responses.activate
    def test_ogc_server_cache_clean(self) -> None:
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import OGCServer
        from c2cgeoportal_geoportal.views.theme import Theme

        ogc_server = DBSession.query(OGCServer).one()

        request = create_dummy_request()
        theme = Theme(request)
        all_errors = set()
        url_internal_wfs, _, _ = theme.get_url_internal_wfs(ogc_server, all_errors)

        responses.get(
            "http://mapserver:8080/?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetCapabilities&ROLE_IDS=0&USER_ID=0",
            content_type="application/vnd.ogc.wms_xml",
            body=CAP.format(name2="__test_layer_internal_wms2"),
        )
        responses.get(
            "http://mapserver:8080/?SERVICE=WFS&VERSION=1.0.0&REQUEST=DescribeFeatureType&ROLE_IDS=0&USER_ID=0",
            content_type="application/vnd.ogc.wms_xml",
            body=DFT.format(name2="police1"),
        )
        asyncio.run(theme._preload(set()))
        responses.reset()

        layers, err = asyncio.run(theme._wms_getcap(ogc_server))
        assert err == set()
        assert set(layers["layers"].keys()) == {
            "__test_layer_internal_wms",
            "__test_layer_internal_wms2",
            "demo",
        }
        attributes, namespace, err = asyncio.run(theme._get_features_attributes(url_internal_wfs, ogc_server))
        assert err == set()
        assert namespace == "http://mapserver.gis.umn.edu/mapserver"
        assert set(attributes.keys()) == {"hotel_label", "police1"}

        assert set(self.std_cache.keys()) == set()
        assert set(caching.MEMORY_CACHE_DICT.keys()) == {
            "c2cgeoportal_geoportal.lib.oauth2|_get_oauth_client_cache|10|60",
            "c2cgeoportal_geoportal.lib.functionality|_get_role|anonymous",
            "c2cgeoportal_geoportal.lib.functionality|_get_functionalities_type",
            "c2cgeoportal_geoportal.lib|_get_intranet_networks",
        }
        assert set(self.ogc_cache.keys()) == {
            "c2cgeoportal_geoportal.views.theme|_get_features_attributes_cache|http://mapserver:8080/?SERVICE=WFS&VERSION=1.0.0&REQUEST=DescribeFeatureType&ROLE_IDS=0&USER_ID=0|__test_ogc_server",
            f"c2cgeoportal_geoportal.views.theme|build_web_map_service|{ogc_server.id}",
            "c2cgeoportal_geoportal.views.theme|do_get_http_cached|http://mapserver:8080/?SERVICE=WFS&VERSION=1.0.0&REQUEST=DescribeFeatureType&ROLE_IDS=0&USER_ID=0",
            "c2cgeoportal_geoportal.views.theme|do_get_http_cached|http://mapserver:8080/?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetCapabilities&ROLE_IDS=0&USER_ID=0",
        }

        responses.get(
            "http://mapserver:8080/?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetCapabilities&ROLE_IDS=0&USER_ID=0",
            content_type="application/vnd.ogc.wms_xml",
            body=CAP.format(name2="__test_layer_internal_wms3"),
        )
        responses.get(
            "http://mapserver:8080/?SERVICE=WFS&VERSION=1.0.0&REQUEST=DescribeFeatureType&ROLE_IDS=0&USER_ID=0",
            content_type="application/vnd.ogc.wms_xml",
            body=DFT.format(name2="police2"),
        )
        theme._ogc_server_clear_cache(ogc_server)
        responses.reset()

        layers, err = asyncio.run(theme._wms_getcap(ogc_server))
        assert err == set()
        assert set(layers["layers"].keys()) == {
            "__test_layer_internal_wms",
            "__test_layer_internal_wms3",
            "demo",
        }

        attributes, namespace, err = asyncio.run(theme._get_features_attributes(url_internal_wfs, ogc_server))
        assert err == set()
        assert namespace == "http://mapserver.gis.umn.edu/mapserver"
        assert set(attributes.keys()) == {"hotel_label", "police2"}

        assert set(self.std_cache.keys()) == set()
        assert set(caching.MEMORY_CACHE_DICT.keys()) == {
            "c2cgeoportal_geoportal.lib.oauth2|_get_oauth_client_cache|10|60",
            "c2cgeoportal_geoportal.lib.functionality|_get_role|anonymous",
            "c2cgeoportal_geoportal.lib.functionality|_get_functionalities_type",
            "c2cgeoportal_geoportal.lib|_get_intranet_networks",
        }
        assert set(self.ogc_cache.keys()) == {
            "c2cgeoportal_geoportal.views.theme|_get_features_attributes_cache|http://mapserver:8080/?SERVICE=WFS&VERSION=1.0.0&REQUEST=DescribeFeatureType&ROLE_IDS=0&USER_ID=0|__test_ogc_server",
            f"c2cgeoportal_geoportal.views.theme|build_web_map_service|{ogc_server.id}",
            "c2cgeoportal_geoportal.views.theme|do_get_http_cached|http://mapserver:8080/?SERVICE=WFS&VERSION=1.0.0&REQUEST=DescribeFeatureType&ROLE_IDS=0&USER_ID=0",
            "c2cgeoportal_geoportal.views.theme|do_get_http_cached|http://mapserver:8080/?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetCapabilities&ROLE_IDS=0&USER_ID=0",
        }


@pytest.mark.parametrize(
    "came_from,host,allowed_hosts,expected",
    [
        ("http://example.com", "example.com", [], True),
        ("http://example.com", "other.com", ["example.com"], True),
        ("http://example.com", "other.com", [], False),
    ],
)
def test_ogc_server_cache_clean_wrong_host(
    default_ogcserver, admin_user, came_from, host, allowed_hosts, expected
):
    from c2cgeoportal_geoportal.views.theme import Theme

    request = create_dummy_request(user=admin_user.username)

    request.params["came_from"] = came_from
    request.matchdict["id"] = default_ogcserver.id
    request.host = host
    request.registry.settings.setdefault("admin_interface", {})["allowed_hosts"] = allowed_hosts

    theme = Theme(request)

    responses.get(
        "http://mapserver:8080/?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetCapabilities&ROLE_IDS=0&USER_ID=0",
        content_type="application/vnd.ogc.wms_xml",
        body=CAP.format(name2="__test_layer_internal_wms3"),
    )
    responses.get(
        "http://mapserver:8080/?SERVICE=WFS&VERSION=1.0.0&REQUEST=DescribeFeatureType&ROLE_IDS=0&USER_ID=0",
        content_type="application/vnd.ogc.wms_xml",
        body=DFT.format(name2="police2"),
    )
    with pytest.raises(
        pyramid.httpexceptions.HTTPFound if expected else pyramid.httpexceptions.HTTPBadRequest
    ):
        theme.ogc_server_clear_cache_view()


def test_ogc_server_cache_clean_wrong_host_non_admin_user(some_user):
    from c2cgeoportal_geoportal.views.theme import Theme

    request = create_dummy_request(user=some_user.username)
    theme = Theme(request)

    with pytest.raises(pyramid.httpexceptions.HTTPForbidden):
        theme.ogc_server_clear_cache_view()


def test_ogc_server_cache_clean_wrong_host_no_user():
    from c2cgeoportal_geoportal.views.theme import Theme

    request = create_dummy_request()
    theme = Theme(request)

    with pytest.raises(pyramid.httpexceptions.HTTPForbidden):
        theme.ogc_server_clear_cache_view()
