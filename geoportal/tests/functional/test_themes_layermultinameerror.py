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

# pylint: disable=missing-docstring,attribute-defined-outside-init,protected-access


from unittest import TestCase

import transaction
from pyramid import testing
from tests.functional import create_default_ogcserver, create_dummy_request, mapserv_url
from tests.functional import setup_common as setup_module  # noqa
from tests.functional import teardown_common as teardown_module  # noqa


class TestLayerMultiNameErrorView(TestCase):
    def setup_method(self, _):
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import Interface, LayerGroup, LayerWMS, Theme

        main = Interface(name="desktop")

        ogc_server = create_default_ogcserver()

        layer_wms_1 = LayerWMS(name="__test_layer_wms_1", public=True)
        layer_wms_1.layer = "testpoint_unprotected"
        layer_wms_1.interfaces = [main]
        layer_wms_1.ogc_server = ogc_server

        layer_wms_2 = LayerWMS(name="__test_layer_wms_2", public=True)
        layer_wms_2.layer = "testpoint_substitution"
        layer_wms_2.interfaces = [main]
        layer_wms_2.ogc_server = ogc_server

        layer_wms_3 = LayerWMS(name="__test_layer_wms_3", public=True)
        layer_wms_3.layer = "testpoint_unprotected,testpoint_substitution"
        layer_wms_3.interfaces = [main]
        layer_wms_3.ogc_server = ogc_server

        layer_group_1 = LayerGroup(name="__test_layer_group_1")
        layer_group_1.children = [layer_wms_1, layer_wms_2]

        layer_group_2 = LayerGroup(name="__test_layer_group_2")
        layer_group_2.children = [layer_wms_1, layer_wms_3]

        theme = Theme(name="__test_theme")
        theme.interfaces = [main]
        theme.children = [layer_group_1, layer_group_2]

        DBSession.add(theme)
        transaction.commit()

    def teardown_method(self, _):
        testing.tearDown()

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import Interface, OGCServer, TreeItem

        for item in DBSession.query(TreeItem).all():
            DBSession.delete(item)
        DBSession.query(OGCServer).delete()
        DBSession.query(Interface).filter(Interface.name == "main").delete()

        transaction.commit()

    @staticmethod
    def _create_request_obj(params=None, **kwargs):
        if params is None:
            params = {}
        request = create_dummy_request(**kwargs)
        request.static_url = lambda url: "/dummy/static/url"
        request.route_url = lambda url, **kwargs: mapserv_url
        request.params = params

        return request

    def _create_theme_obj(self, **kwargs):
        from c2cgeoportal_geoportal.views.theme import Theme

        return Theme(self._create_request_obj(**kwargs))
