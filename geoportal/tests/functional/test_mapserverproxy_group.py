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


from unittest import TestCase

from geoalchemy2 import WKTElement
import transaction

from tests.functional import (  # noqa
    teardown_common as teardown_module,
    setup_common as setup_module,
    create_dummy_request, mapserv_url, create_default_ogcserver,
)


class TestMapserverproxyViewGroup(TestCase):

    def setup_method(self, _):
        from c2cgeoportal.models import User, Role, LayerWMS, RestrictionArea, \
            Interface, DBSession

        ogc_server_internal, _ = create_default_ogcserver()

        user1 = User(username="__test_user1", password="__test_user1")
        role1 = Role(name="__test_role1", description="__test_role1")
        user1.role_name = role1.name
        user1.email = "Tarenpion"

        main = Interface(name="main")

        layer1 = LayerWMS("testpoint_group_name", public=False)
        layer1.layer = "testpoint_group"
        layer1.ogc_server = ogc_server_internal
        layer1.interfaces = [main]

        layer2 = LayerWMS("testpoint_protected_2_name", public=False)
        layer2.layer = "testpoint_protected_2"
        layer2.ogc_server = ogc_server_internal
        layer2.interfaces = [main]

        area = "POLYGON((-100 30, -100 50, 100 50, 100 30, -100 30))"
        area = WKTElement(area, srid=21781)
        restricted_area1 = RestrictionArea("__test_ra1", "", [layer1, layer2], [role1], area)

        DBSession.add_all([user1, role1, layer1, layer2, restricted_area1])
        DBSession.flush()

        transaction.commit()

    def teardown_method(self, _):
        from c2cgeoportal.models import User, Role, LayerWMS, RestrictionArea, \
            Interface, DBSession, OGCServer

        DBSession.query(User).filter(User.username == "__test_user1").delete()

        ra = DBSession.query(RestrictionArea).filter(
            RestrictionArea.name == "__test_ra1"
        ).one()
        ra.roles = []
        ra.layers = []
        DBSession.delete(ra)

        r = DBSession.query(Role).filter(Role.name == "__test_role1").one()
        DBSession.delete(r)

        for layer in DBSession.query(LayerWMS).filter(
                LayerWMS.name.in_(["testpoint_group_name", "testpoint_protected_2_name"])
        ).all():
            DBSession.delete(layer)
        DBSession.query(Interface).filter(
            Interface.name == "main"
        ).delete()
        DBSession.query(OGCServer).delete()

        transaction.commit()

    @staticmethod
    def _create_getcap_request(username=None):
        from c2cgeoportal.models import DBSession, User

        request = create_dummy_request()
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

        assert "<Name>testpoint_protected</Name>" not in response.body.decode("utf-8")
        assert "<Name>testpoint_protected_2</Name>" not in response.body.decode("utf-8")
        # testpoint_group is not public so even unprotected layers are hidden:
        assert "<Name>testpoint_unprotected</Name>" not in response.body.decode("utf-8")
        assert "<Name>testpoint_group</Name>" not in response.body.decode("utf-8")
        # testpoint_group_2 is a standard group containing only protected layers
        assert "<Name>testpoint_group_2</Name>" not in response.body.decode("utf-8")

        request = self._create_getcap_request(username="__test_user1")
        request.params.update(dict(
            service="wms", version="1.1.1", request="getcapabilities",
        ))
        response = MapservProxy(request).proxy()
        assert "<Name>testpoint_protected</Name>" in response.body.decode("utf-8")
        assert "<Name>testpoint_protected_2</Name>" in response.body.decode("utf-8")
        assert "<Name>testpoint_unprotected</Name>" in response.body.decode("utf-8")
        assert "<Name>testpoint_group</Name>" in response.body.decode("utf-8")
        assert "<Name>testpoint_group_2</Name>" in response.body.decode("utf-8")

    def test_wfs_get_capabilities(self):
        from c2cgeoportal.views.mapserverproxy import MapservProxy

        request = self._create_getcap_request()
        request.params.update(dict(
            service="wfs", version="1.1.1", request="getcapabilities",
        ))
        response = MapservProxy(request).proxy()

        assert "<Name>testpoint_protected</Name>" not in response.body.decode("utf-8")
        # testpoint_group is not public so even unprotected layers are hidden:
        assert "<Name>testpoint_unprotected</Name>" not in response.body.decode("utf-8")
        assert "<Name>testpoint_group</Name>" not in response.body.decode("utf-8")

        request = self._create_getcap_request(username="__test_user1")
        request.params.update(dict(
            service="wfs", version="1.1.1", request="getcapabilities",
        ))
        response = MapservProxy(request).proxy()
        assert "<Name>testpoint_protected</Name>" in response.body.decode("utf-8")
        assert "<Name>testpoint_unprotected</Name>" in response.body.decode("utf-8")
        assert "<Name>testpoint_group</Name>" not in response.body.decode("utf-8")
