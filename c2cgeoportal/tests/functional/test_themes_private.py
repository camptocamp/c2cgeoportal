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


import transaction

from unittest2 import TestCase
from nose.plugins.attrib import attr

from pyramid import testing

from c2cgeoportal.tests.functional import (  # noqa
    tear_down_common as tearDownModule,
    set_up_common as setUpModule,
    mapserv_url, create_dummy_request, create_default_ogcserver,
)


import logging
log = logging.getLogger(__name__)


@attr(functional=True)
class TestThemesPrivateView(TestCase):

    def setUp(self):  # noqa
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None

        self.clean()

        from c2cgeoportal.models import DBSession, \
            Theme, LayerGroup, Interface, LayerWMS, LayerWMTS, User, Role, RestrictionArea

        main = Interface(name=u"desktop")
        role = Role(name=u"__test_role")
        user = User(username=u"__test_user", password=u"__test_user", role=role)
        user.email = "__test_user@example.com"
        ogc_server_internal, _ = create_default_ogcserver()

        layer_wms = LayerWMS(name=u"__test_layer_wms", public=True)
        layer_wms.layer = "__test_public_layer"
        layer_wms.interfaces = [main]
        layer_wms.ogc_server = ogc_server_internal

        layer_wms_private = LayerWMS(name=u"__test_layer_wms_private", public=True)
        layer_wms_private.layer = "__test_private_layer"
        layer_wms_private.public = False
        layer_wms_private.interfaces = [main]
        layer_wms_private.ogc_server = ogc_server_internal

        layer_wmts = LayerWMTS(name=u"__test_layer_wmts", public=True)
        layer_wmts.url = "http://example.com/1.0.0/WMTSCapabilities.xml"
        layer_wmts.layer = "map"
        layer_wmts.interfaces = [main]

        layer_wmts_private = LayerWMTS(name=u"__test_layer_wmts_private", public=True)
        layer_wmts_private.url = "http://example.com/1.0.0/WMTSCapabilities.xml"
        layer_wmts_private.layer = "map"
        layer_wmts_private.public = False
        layer_wmts_private.interfaces = [main]

        layer_group = LayerGroup(name=u"__test_layer_group")
        layer_group.children = [layer_wms, layer_wms_private, layer_wmts, layer_wmts_private]

        theme = Theme(name=u"__test_theme")
        theme.interfaces = [main]
        theme.children = [layer_group]

        restriction_area = RestrictionArea(
            name=u"__test_ra1", layers=[layer_wms_private, layer_wmts_private], roles=[role]
        )

        DBSession.add_all([theme, restriction_area, user])

        transaction.commit()

    def tearDown(self):  # noqa
        self.clean()
        testing.tearDown()

    @staticmethod
    def clean():
        from c2cgeoportal.models import DBSession, TreeItem, Interface, User, Role, RestrictionArea, \
            OGCServer

        for o in DBSession.query(RestrictionArea).all():
            o.roles = []
            o.layers = []
            DBSession.delete(o)
        for item in DBSession.query(TreeItem).all():
            DBSession.delete(item)
        DBSession.query(OGCServer).delete()
        DBSession.query(Interface).filter(
            Interface.name == "main"
        ).delete()
        DBSession.query(User).filter(
            User.username == "__test_user"
        ).delete()
        DBSession.query(Role).filter(
            Role.name == "__test_role"
        ).delete()

        transaction.commit()

    #
    # viewer view tests
    #

    @staticmethod
    def _create_request_obj(params=None, user=None, **kwargs):
        if params is None:
            params = {}
        request = create_dummy_request(**kwargs)
        request.user = user
        request.static_url = lambda url: "/dummy/static/url"

        def route_url(name, _query=None, **kwargs):
            if _query is None:
                return "http://localhost/travis/mapserv"
            else:
                return "http://localhost/travis/mapserv?" + "&".join(["=".join(i) for i in _query.items()])

        request.route_url = route_url
        request.params = params

        return request

    def _create_entry_obj(self, **kwargs):
        from c2cgeoportal.views.entry import Entry

        return Entry(self._create_request_obj(**kwargs))

    def _only_name(self, item, attribute="name"):
        result = {}

        if attribute in item:
            result[attribute] = item[attribute]

        if "children" in item:
            result["children"] = [
                self._only_name(i, attribute) for i in item["children"]
            ]

        return result

    @staticmethod
    def _get_filtered_errors(themes):
        return {
            e for e in themes["errors"]
            if e != "The layer '' (__test_layer_external_wms) is not defined in WMS capabilities"
        }

    def test_public(self):
        entry = self._create_entry_obj(params={
            "version": "2"
        })
        themes = entry.themes()
        self.assertEquals(themes["errors"], [])
        self.assertEquals(
            [self._only_name(t) for t in themes["themes"]],
            [{
                "name": "__test_theme",
                "children": [{
                    "name": u"__test_layer_group",
                    "children": [{
                        "name": u"__test_layer_wms"
                    }, {
                        "name": u"__test_layer_wmts"
                    }]
                }]
            }]
        )

    def test_private(self):
        from c2cgeoportal.models import DBSession, User
        entry = self._create_entry_obj(params={
            "version": "2"
        }, user=DBSession.query(User).filter_by(username=u"__test_user").one())
        themes = entry.themes()
        self.assertEquals(themes["errors"], [])
        self.assertEquals(
            [self._only_name(t) for t in themes["themes"]],
            [{
                "name": u"__test_theme",
                "children": [{
                    "name": u"__test_layer_group",
                    "children": [{
                        "name": u"__test_layer_wms"
                    }, {
                        "name": u"__test_layer_wms_private"
                    }, {
                        "name": u"__test_layer_wmts"
                    }, {
                        "name": u"__test_layer_wmts_private"
                    }]
                }]
            }]
        )
