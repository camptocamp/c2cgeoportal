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
from geoalchemy2 import WKTElement
from pyramid import testing

from tests.functional import (
    cleanup_db,
    create_default_ogcserver,
    create_dummy_request,
    mapserv_url,
    setup_db,
)
from tests.functional import setup_common as setup_module  # noqa
from tests.functional import teardown_common as teardown_module  # noqa


class TestThemeEditing(TestCase):
    def setup_method(self, _) -> None:
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None
        self._tables = []

        from geoalchemy2 import Geometry
        from sqlalchemy import Column, Table, types
        from sqlalchemy.ext.declarative import declarative_base

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import (
            Interface,
            LayerGroup,
            LayerWMS,
            RestrictionArea,
            Role,
            Theme,
        )
        from c2cgeoportal_commons.models.static import User

        setup_db()

        ogcserver = create_default_ogcserver(DBSession)

        role1 = Role(name="__test_role1")
        user1 = User(username="__test_user1", password="__test_user1", settings_role=role1, roles=[role1])
        user1.email = "__test_user1@example.com"

        role2 = Role(name="__test_role2", extent=WKTElement("POLYGON((1 2, 1 4, 3 4, 3 2, 1 2))", srid=21781))
        user2 = User(username="__test_user2", password="__test_user2", settings_role=role2, roles=[role2])

        main = Interface(name="main")

        engine = DBSession.c2c_rw_bind
        a_geo_table = Table(
            "a_geo_table",
            declarative_base().metadata,
            Column("id", types.Integer, primary_key=True),
            Column("geom", Geometry("POINT", srid=21781)),
            schema="geodata",
        )

        self._tables = [a_geo_table]
        a_geo_table.drop(checkfirst=True, bind=engine)
        a_geo_table.create(bind=engine)

        private_layer = LayerWMS(name="__test_private_layer", public=False)
        private_layer.layer = "__test_private_layer"
        private_layer.geo_table = "geodata.a_geo_table"
        private_layer.interfaces = [main]
        private_layer.ogc_server = ogcserver

        group = LayerGroup(name="__test_layer_group")
        group.children = [private_layer]

        theme = Theme(name="__test_theme")
        theme.children = [group]
        theme.interfaces = [main]

        DBSession.add(
            RestrictionArea(name="__test_ra1", description="", layers=[private_layer], roles=[role1]),
        )
        DBSession.add(
            RestrictionArea(
                name="__test_ra2",
                description="",
                layers=[private_layer],
                roles=[role2],
                readwrite=True,
            ),
        )

        DBSession.add_all([user1, user2, role1, role2, theme, group, private_layer])

        transaction.commit()

    def teardown_method(self, _) -> None:
        testing.tearDown()

        cleanup_db()

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import Layer, LayerGroup, Theme

        for t in DBSession.query(Theme).filter(Theme.name == "__test_theme").all():
            DBSession.delete(t)
        for g in DBSession.query(LayerGroup).all():
            DBSession.delete(g)
        for layer in DBSession.query(Layer).all():
            DBSession.delete(layer)

        for table in self._tables[::-1]:
            table.drop(checkfirst=True, bind=DBSession.c2c_rw_bind)

        transaction.commit()

    @staticmethod
    def _create_request_obj(username=None, params=None, **kwargs):
        if params is None:
            params = {}
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User

        request = create_dummy_request(**kwargs)
        request.route_url = lambda url, **kwargs: mapserv_url
        request.interface_name = "main"
        request.params = params

        if username is not None:
            request.user = DBSession.query(User).filter_by(username=username).one()

        return request

    def test_themev2_noauth_edit_permission(self) -> None:
        from c2cgeoportal_geoportal.views.theme import Theme

        request = self._create_request_obj()
        request.params = {"interface": "main"}
        theme_view = Theme(request)
        themes = theme_view.themes()
        assert set(themes["errors"]) == set()
        assert [t["name"] for t in themes["themes"]] == []

    def test_themev2_auth_no_edit_permission(self) -> None:
        from c2cgeoportal_geoportal.views.theme import Theme

        request = self._create_request_obj(username="__test_user1")
        request.params = {"interface": "main"}
        theme_view = Theme(request)
        themes = theme_view.themes()
        assert set(themes["errors"]) == set()
        assert [t["name"] for t in themes["themes"]] == ["__test_theme"]
        assert [c["name"] for c in themes["themes"][0]["children"]] == ["__test_layer_group"]

        layers = themes["themes"][0]["children"][0]["children"]
        assert [l["name"] for l in layers] == ["__test_private_layer"]
        assert "editable" not in layers[0]

    def test_themev2_auth_edit_permission(self) -> None:
        from c2cgeoportal_geoportal.views.theme import Theme

        request = self._create_request_obj(username="__test_user2", params={"min_levels": "0"})
        request.params = {"interface": "main"}

        theme_view = Theme(request)
        themes = theme_view.themes()
        assert set(themes["errors"]) == set()
        assert [t["name"] for t in themes["themes"]] == ["__test_theme"]
        assert [c["name"] for c in themes["themes"][0]["children"]] == ["__test_layer_group"]

        layers = themes["themes"][0]["children"][0]["children"]
        assert [l["name"] for l in layers] == ["__test_private_layer"]
        assert "editable" in layers[0]
        assert layers[0]["editable"] is True
