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


import os
from unittest2 import TestCase
import transaction
from c2cgeoportal.tests.functional import (  # noqa
    tear_down_common as tearDownModule,
    set_up_common as setUpModule,
    create_dummy_request, mapserv, create_default_ogcserver, cleanup_db,
)


class TestMapserverproxyCapabilities(TestCase):

    def setUp(self):  # noqa
        self.maxDiff = None

        from c2cgeoportal.models import User, Role, LayerWMS, RestrictionArea, \
            Interface, DBSession, OGCServer, \
            OGCSERVER_TYPE_MAPSERVER, OGCSERVER_AUTH_STANDARD

        cleanup_db()
        create_default_ogcserver()

        ogcserver_jpeg = OGCServer(name="__test_ogc_server_jpeg")
        ogcserver_jpeg.url = mapserv
        ogcserver_jpeg.image_type = "image/jpeg"
        ogcserver_jpeg.type = OGCSERVER_TYPE_MAPSERVER
        ogcserver_jpeg.auth = OGCSERVER_AUTH_STANDARD

        ogcserver_png = OGCServer(name="__test_ogc_server_png")
        ogcserver_png.url = mapserv
        ogcserver_png.image_type = "image/png"
        ogcserver_png.type = OGCSERVER_TYPE_MAPSERVER
        ogcserver_png.auth = OGCSERVER_AUTH_STANDARD

        ogcserver_wfs1 = OGCServer(name="__test_ogc_server_wfs1")
        ogcserver_wfs1.url = mapserv
        ogcserver_wfs1.url_wfs = "config://srv"
        ogcserver_wfs1.image_type = "image/png"
        ogcserver_wfs1.type = OGCSERVER_TYPE_MAPSERVER
        ogcserver_wfs1.auth = OGCSERVER_AUTH_STANDARD

        ogcserver_wfs2 = OGCServer(name="__test_ogc_server_wfs2")
        ogcserver_wfs2.url = "config://srv"
        ogcserver_wfs2.url_wfs = mapserv
        ogcserver_wfs2.image_type = "image/png"
        ogcserver_wfs2.type = OGCSERVER_TYPE_MAPSERVER
        ogcserver_wfs2.auth = OGCSERVER_AUTH_STANDARD

        role = Role(name=u"__test_role", description=u"__test_role")
        user = User(username=u"__test_user", password=u"__test_user")
        user.role_name = u"__test_role"

        main = Interface(name=u"main")

        layer1 = LayerWMS(u"__test_layer1", public=False)
        layer1.layer = u"__test_private_layer1"
        layer1.ogc_server = ogcserver_jpeg
        layer1.interfaces = [main]

        layer2 = LayerWMS(u"__test_layer2", public=False)
        layer2.layer = u"__test_private_layer2"
        layer2.ogc_server = ogcserver_png
        layer2.interfaces = [main]

        layer3 = LayerWMS(u"__test_layer3", public=False)
        layer3.layer = u"__test_private_layer3"
        layer3.ogc_server = ogcserver_wfs1
        layer3.interfaces = [main]

        layer4 = LayerWMS(u"__test_layer4", public=False)
        layer4.layer = u"__test_private_layer4"
        layer4.ogc_server = ogcserver_wfs2
        layer4.interfaces = [main]

        restricted_area = RestrictionArea(u"__test_ra", u"", [layer1, layer2, layer3, layer4], [role])

        DBSession.add_all([
            user, restricted_area
        ])
        transaction.commit()

    @staticmethod
    def tearDown():  # noqa
        cleanup_db()

    @staticmethod
    def _wms_get_capabilities(ogcserver, service="wms", username=None):
        from c2cgeoportal.models import DBSession, User
        from c2cgeoportal.views.mapserverproxy import MapservProxy

        request = create_dummy_request({
            "admin_interface": {
                "available_functionalities": [
                    "mapserver_substitution",
                    "print_template",
                ]
            },
            "servers": {
                "srv": "http://example.com"
            }
        })
        request.params = {"map": os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "c2cgeoportal_test.map"
        )}
        request.user = None if username is None else \
            DBSession.query(User).filter_by(username=username).one()
        request.params.update(dict(
            service=service,
            version="1.1.1",
            request="getcapabilities",
            ogcserver=ogcserver
        ))
        return MapservProxy(request).proxy()

    @staticmethod
    def _wms_get_capabilities_config(ogcserver, service="wms", username=None):
        from c2cgeoportal.models import DBSession, User
        from c2cgeoportal.views.mapserverproxy import MapservProxy

        request = create_dummy_request({
            "admin_interface": {
                "available_functionalities": [
                    "mapserver_substitution",
                    "print_template",
                ]
            },
            "servers": {
                "srv": "http://example.com"
            },
            "mapserverproxy": {
                "default_ogc_server": ogcserver,
            },
        })
        request.params = {"map": os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "c2cgeoportal_test.map"
        )}
        request.user = None if username is None else \
            DBSession.query(User).filter_by(username=username).one()
        request.params.update(dict(
            service=service,
            version="1.1.1",
            request="getcapabilities",
        ))
        return MapservProxy(request).proxy()

    def test_wms_osjpeg(self):
        response = self._wms_get_capabilities("__test_ogc_server_jpeg")
        self.assertTrue(response.body.find("<Name>__test_private_layer1</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer2</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer3</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer4</Name>") < 0)

    def test_wms_osjpeg_auth(self):
        response = self._wms_get_capabilities("__test_ogc_server_jpeg", username="__test_user")
        self.assertTrue(response.body.find("<Name>__test_private_layer1</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer2</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer3</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer4</Name>") < 0)

    def test_wfs_osjpeg(self):
        response = self._wms_get_capabilities("__test_ogc_server_jpeg", "wfs")
        self.assertTrue(response.body.find("<Name>__test_private_layer1</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer2</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer3</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer4</Name>") < 0)

    def test_wfs_osjpeg_auth(self):
        response = self._wms_get_capabilities("__test_ogc_server_jpeg", "wfs", username="__test_user")
        self.assertTrue(response.body.find("<Name>__test_private_layer1</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer2</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer3</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer4</Name>") < 0)

    def test_wms_ospng(self):
        response = self._wms_get_capabilities("__test_ogc_server_png")
        self.assertTrue(response.body.find("<Name>__test_private_layer1</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer2</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer3</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer4</Name>") < 0)

    def test_wms_ospng_auth(self):
        response = self._wms_get_capabilities("__test_ogc_server_png", username="__test_user")
        self.assertTrue(response.body.find("<Name>__test_private_layer1</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer2</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer3</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer4</Name>") < 0)

    def test_wfs_ospng(self):
        response = self._wms_get_capabilities("__test_ogc_server_png", "wfs")
        self.assertTrue(response.body.find("<Name>__test_private_layer1</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer2</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer3</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer4</Name>") < 0)

    def test_wfs_ospng_auth(self):
        response = self._wms_get_capabilities("__test_ogc_server_png", "wfs", username="__test_user")
        self.assertTrue(response.body.find("<Name>__test_private_layer1</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer2</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer3</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer4</Name>") < 0)

    def test_wms_oswfs1(self):
        response = self._wms_get_capabilities("__test_ogc_server_wfs1")
        self.assertTrue(response.body.find("<Name>__test_private_layer1</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer2</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer3</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer4</Name>") < 0)

    def test_wms_oswfs1_auth(self):
        response = self._wms_get_capabilities("__test_ogc_server_wfs1", username="__test_user")
        self.assertTrue(response.body.find("<Name>__test_private_layer1</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer2</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer3</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer4</Name>") < 0)

    def test_wfs_oswfs2(self):
        response = self._wms_get_capabilities("__test_ogc_server_wfs2", "wfs")
        self.assertTrue(response.body.find("<Name>__test_private_layer1</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer2</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer3</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer4</Name>") < 0)

    def test_wfs_oswfs2_auth(self):
        response = self._wms_get_capabilities("__test_ogc_server_wfs2", "wfs", username="__test_user")
        self.assertTrue(response.body.find("<Name>__test_private_layer1</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer2</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer3</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer4</Name>") < 0)

    # # # CONFIG # # #

    def test_wms_osjpeg_config(self):
        response = self._wms_get_capabilities_config("__test_ogc_server_jpeg")
        self.assertTrue(response.body.find("<Name>__test_private_layer1</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer2</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer3</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer4</Name>") < 0)

    def test_wms_osjpeg_auth_config(self):
        response = self._wms_get_capabilities_config("__test_ogc_server_jpeg", username="__test_user")
        self.assertTrue(response.body.find("<Name>__test_private_layer1</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer2</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer3</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer4</Name>") < 0)

    def test_wfs_osjpeg_config(self):
        response = self._wms_get_capabilities_config("__test_ogc_server_jpeg", "wfs")
        self.assertTrue(response.body.find("<Name>__test_private_layer1</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer2</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer3</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer4</Name>") < 0)

    def test_wfs_osjpeg_auth_config(self):
        response = self._wms_get_capabilities_config("__test_ogc_server_jpeg", "wfs", username="__test_user")
        self.assertTrue(response.body.find("<Name>__test_private_layer1</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer2</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer3</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer4</Name>") < 0)

    def test_wms_ospng_config(self):
        response = self._wms_get_capabilities_config("__test_ogc_server_png")
        self.assertTrue(response.body.find("<Name>__test_private_layer1</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer2</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer3</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer4</Name>") < 0)

    def test_wms_ospng_auth_config(self):
        response = self._wms_get_capabilities_config("__test_ogc_server_png", username="__test_user")
        self.assertTrue(response.body.find("<Name>__test_private_layer1</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer2</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer3</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer4</Name>") < 0)

    def test_wfs_ospng_config(self):
        response = self._wms_get_capabilities_config("__test_ogc_server_png", "wfs")
        self.assertTrue(response.body.find("<Name>__test_private_layer1</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer2</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer3</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer4</Name>") < 0)

    def test_wfs_ospng_auth_config(self):
        response = self._wms_get_capabilities_config("__test_ogc_server_png", "wfs", username="__test_user")
        self.assertTrue(response.body.find("<Name>__test_private_layer1</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer2</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer3</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer4</Name>") < 0)

    def test_wms_oswfs1_config(self):
        response = self._wms_get_capabilities_config("__test_ogc_server_wfs1")
        self.assertTrue(response.body.find("<Name>__test_private_layer1</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer2</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer3</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer4</Name>") < 0)

    def test_wms_oswfs1_auth_config(self):
        response = self._wms_get_capabilities_config("__test_ogc_server_wfs1", username="__test_user")
        self.assertTrue(response.body.find("<Name>__test_private_layer1</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer2</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer3</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer4</Name>") < 0)

    def test_wfs_oswfs2_config(self):
        response = self._wms_get_capabilities_config("__test_ogc_server_wfs2", "wfs")
        self.assertTrue(response.body.find("<Name>__test_private_layer1</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer2</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer3</Name>") < 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer4</Name>") < 0)

    def test_wfs_oswfs2_auth_config(self):
        response = self._wms_get_capabilities_config("__test_ogc_server_wfs2", "wfs", username="__test_user")
        self.assertTrue(response.body.find("<Name>__test_private_layer1</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer2</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer3</Name>") > 0)
        self.assertTrue(response.body.find("<Name>__test_private_layer4</Name>") < 0)
