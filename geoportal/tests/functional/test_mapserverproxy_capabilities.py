# Copyright (c) 2013-2025, Camptocamp SA
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

import transaction

from tests.functional import (
    cleanup_db,
    create_default_ogcserver,
    create_dummy_request,
    mapserv_url,
    setup_db,
)
from tests.functional import setup_common as setup_module  # noqa
from tests.functional import teardown_common as teardown_module  # noqa


class TestMapserverproxyCapabilities(TestCase):
    def setup_method(self, _) -> None:
        self.maxDiff = None

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import (
            OGCSERVER_AUTH_STANDARD,
            OGCSERVER_TYPE_MAPSERVER,
            Interface,
            LayerWMS,
            OGCServer,
            RestrictionArea,
            Role,
        )
        from c2cgeoportal_commons.models.static import User

        setup_db()
        create_default_ogcserver(DBSession)

        ogcserver_jpeg = OGCServer(name="__test_ogc_server_jpeg")
        ogcserver_jpeg.url = mapserv_url
        ogcserver_jpeg.image_type = "image/jpeg"
        ogcserver_jpeg.type = OGCSERVER_TYPE_MAPSERVER
        ogcserver_jpeg.auth = OGCSERVER_AUTH_STANDARD

        ogcserver_png = OGCServer(name="__test_ogc_server_png")
        ogcserver_png.url = mapserv_url
        ogcserver_png.image_type = "image/png"
        ogcserver_png.type = OGCSERVER_TYPE_MAPSERVER
        ogcserver_png.auth = OGCSERVER_AUTH_STANDARD

        ogcserver_wfs1 = OGCServer(name="__test_ogc_server_wfs1")
        ogcserver_wfs1.url = mapserv_url
        ogcserver_wfs1.url_wfs = "config://srv"
        ogcserver_wfs1.image_type = "image/png"
        ogcserver_wfs1.type = OGCSERVER_TYPE_MAPSERVER
        ogcserver_wfs1.auth = OGCSERVER_AUTH_STANDARD

        ogcserver_wfs2 = OGCServer(name="__test_ogc_server_wfs2")
        ogcserver_wfs2.url = "config://srv"
        ogcserver_wfs2.url_wfs = mapserv_url
        ogcserver_wfs2.image_type = "image/png"
        ogcserver_wfs2.type = OGCSERVER_TYPE_MAPSERVER
        ogcserver_wfs2.auth = OGCSERVER_AUTH_STANDARD

        role = Role(name="__test_role", description="__test_role")
        user = User(username="__test_user", password="__test_user", settings_role=role, roles=[role])

        main = Interface(name="main")

        layer1 = LayerWMS("__test_layer1", public=False)
        layer1.layer = "__test_private_layer1"
        layer1.ogc_server = ogcserver_jpeg
        layer1.interfaces = [main]

        layer2 = LayerWMS("__test_layer2", public=False)
        layer2.layer = "__test_private_layer2"
        layer2.ogc_server = ogcserver_png
        layer2.interfaces = [main]

        layer3 = LayerWMS("__test_layer3", public=False)
        layer3.layer = "__test_private_layer3"
        layer3.ogc_server = ogcserver_wfs1
        layer3.interfaces = [main]

        layer4 = LayerWMS("__test_layer4", public=False)
        layer4.layer = "__test_private_layer4"
        layer4.ogc_server = ogcserver_wfs2
        layer4.interfaces = [main]

        restricted_area = RestrictionArea("__test_ra", "", [layer1, layer2, layer3, layer4], [role])

        DBSession.add_all([user, restricted_area])
        transaction.commit()

    def teardown_method(self, _) -> None:
        cleanup_db()

    @staticmethod
    def _wms_get_capabilities(ogcserver, service="wms", username=None):
        from c2cgeoportal_geoportal.views.mapserverproxy import MapservProxy

        request = create_dummy_request(
            {
                "admin_interface": {
                    "available_functionalities": [
                        {"name": "mapserver_substitution"},
                        {"name": "print_template"},
                    ],
                },
                "servers": {"srv": "http://example.com"},
            },
            user=username,
        )
        request.params.update(
            dict(service=service, version="1.1.1", request="getcapabilities", ogcserver=ogcserver),
        )
        return MapservProxy(request).proxy()

    @staticmethod
    def _wms_get_capabilities_config(ogcserver, service="wms", username=None):
        from c2cgeoportal_geoportal.views.mapserverproxy import MapservProxy

        request = create_dummy_request(
            {
                "admin_interface": {
                    "available_functionalities": [
                        {"name": "mapserver_substitution"},
                        {"name": "print_template"},
                    ],
                },
                "servers": {"srv": "http://example.com"},
            },
            user=username,
        )
        request.params.update(
            dict(service=service, version="1.1.1", request="getcapabilities", ogcserver=ogcserver),
        )
        return MapservProxy(request).proxy()

    def test_wms_osjpeg(self) -> None:
        response = self._wms_get_capabilities("__test_ogc_server_jpeg")
        assert "<Name>__test_private_layer1</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer2</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer3</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer4</Name>" in response.body.decode("utf-8")

    def test_wms_osjpeg_auth(self) -> None:
        response = self._wms_get_capabilities("__test_ogc_server_jpeg", username="__test_user")
        assert "<Name>__test_private_layer1</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer2</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer3</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer4</Name>" in response.body.decode("utf-8")

    def test_wfs_osjpeg(self) -> None:
        response = self._wms_get_capabilities("__test_ogc_server_jpeg", "wfs")
        assert "<Name>__test_private_layer1</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer2</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer3</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer4</Name>" not in response.body.decode("utf-8")

    def test_wfs_osjpeg_auth(self) -> None:
        response = self._wms_get_capabilities("__test_ogc_server_jpeg", "wfs", username="__test_user")
        assert "<Name>__test_private_layer1</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer2</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer3</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer4</Name>" in response.body.decode("utf-8")

    def test_wms_ospng(self) -> None:
        response = self._wms_get_capabilities("__test_ogc_server_png")
        assert "<Name>__test_private_layer1</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer2</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer3</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer4</Name>" in response.body.decode("utf-8")

    def test_wms_ospng_auth(self) -> None:
        response = self._wms_get_capabilities("__test_ogc_server_png", username="__test_user")
        assert "<Name>__test_private_layer1</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer2</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer3</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer4</Name>" in response.body.decode("utf-8")

    def test_wfs_ospng(self) -> None:
        response = self._wms_get_capabilities("__test_ogc_server_png", "wfs")
        assert "<Name>__test_private_layer1</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer2</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer3</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer4</Name>" not in response.body.decode("utf-8")

    def test_wfs_ospng_auth(self) -> None:
        response = self._wms_get_capabilities("__test_ogc_server_png", "wfs", username="__test_user")
        assert "<Name>__test_private_layer1</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer2</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer3</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer4</Name>" in response.body.decode("utf-8")

    def test_wms_oswfs1(self) -> None:
        response = self._wms_get_capabilities("__test_ogc_server_wfs1")
        assert "<Name>__test_private_layer1</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer2</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer3</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer4</Name>" in response.body.decode("utf-8")

    def test_wms_oswfs1_auth(self) -> None:
        response = self._wms_get_capabilities("__test_ogc_server_wfs1", username="__test_user")
        assert "<Name>__test_private_layer1</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer2</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer3</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer4</Name>" in response.body.decode("utf-8")

    def test_wfs_oswfs2(self) -> None:
        response = self._wms_get_capabilities("__test_ogc_server_wfs2", "wfs")
        assert "<Name>__test_private_layer1</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer2</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer3</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer4</Name>" not in response.body.decode("utf-8")

    def test_wfs_oswfs2_auth(self) -> None:
        response = self._wms_get_capabilities("__test_ogc_server_wfs2", "wfs", username="__test_user")
        assert "<Name>__test_private_layer1</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer2</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer3</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer4</Name>" in response.body.decode("utf-8")

    # # # CONFIG # # #

    def test_wms_osjpeg_config(self) -> None:
        response = self._wms_get_capabilities_config("__test_ogc_server_jpeg")
        assert "<Name>__test_private_layer1</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer2</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer3</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer4</Name>" in response.body.decode("utf-8")

    def test_wms_osjpeg_auth_config(self) -> None:
        response = self._wms_get_capabilities_config("__test_ogc_server_jpeg", username="__test_user")
        assert "<Name>__test_private_layer1</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer2</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer3</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer4</Name>" in response.body.decode("utf-8")

    def test_wfs_osjpeg_config(self) -> None:
        response = self._wms_get_capabilities_config("__test_ogc_server_jpeg", "wfs")
        assert "<Name>__test_private_layer1</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer2</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer3</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer4</Name>" not in response.body.decode("utf-8")

    def test_wfs_osjpeg_auth_config(self) -> None:
        response = self._wms_get_capabilities_config("__test_ogc_server_jpeg", "wfs", username="__test_user")
        assert "<Name>__test_private_layer1</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer2</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer3</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer4</Name>" in response.body.decode("utf-8")

    def test_wms_ospng_config(self) -> None:
        response = self._wms_get_capabilities_config("__test_ogc_server_png")
        assert "<Name>__test_private_layer1</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer2</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer3</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer4</Name>" in response.body.decode("utf-8")

    def test_wms_ospng_auth_config(self) -> None:
        response = self._wms_get_capabilities_config("__test_ogc_server_png", username="__test_user")
        assert "<Name>__test_private_layer1</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer2</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer3</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer4</Name>" in response.body.decode("utf-8")

    def test_wfs_ospng_config(self) -> None:
        response = self._wms_get_capabilities_config("__test_ogc_server_png", "wfs")
        assert "<Name>__test_private_layer1</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer2</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer3</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer4</Name>" not in response.body.decode("utf-8")

    def test_wfs_ospng_auth_config(self) -> None:
        response = self._wms_get_capabilities_config("__test_ogc_server_png", "wfs", username="__test_user")
        assert "<Name>__test_private_layer1</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer2</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer3</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer4</Name>" in response.body.decode("utf-8")

    def test_wms_oswfs1_config(self) -> None:
        response = self._wms_get_capabilities_config("__test_ogc_server_wfs1")
        assert "<Name>__test_private_layer1</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer2</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer3</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer4</Name>" in response.body.decode("utf-8")

    def test_wms_oswfs1_auth_config(self) -> None:
        response = self._wms_get_capabilities_config("__test_ogc_server_wfs1", username="__test_user")
        assert "<Name>__test_private_layer1</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer2</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer3</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer4</Name>" in response.body.decode("utf-8")

    def test_wfs_oswfs2_config(self) -> None:
        response = self._wms_get_capabilities_config("__test_ogc_server_wfs2", "wfs")
        assert "<Name>__test_private_layer1</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer2</Name>" not in response.body.decode("utf-8")
        assert "<Name>__test_private_layer3</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer4</Name>" not in response.body.decode("utf-8")

    def test_wfs_oswfs2_auth_config(self) -> None:
        response = self._wms_get_capabilities_config("__test_ogc_server_wfs2", "wfs", username="__test_user")
        assert "<Name>__test_private_layer1</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer2</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer3</Name>" in response.body.decode("utf-8")
        assert "<Name>__test_private_layer4</Name>" in response.body.decode("utf-8")
