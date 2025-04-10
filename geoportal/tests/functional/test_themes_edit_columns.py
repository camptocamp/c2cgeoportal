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

# pylint: disable=missing-docstring,attribute-defined-outside-init,protected-access,no-value-for-parameter


from typing import TYPE_CHECKING, Any
from unittest import TestCase
from urllib.parse import urlencode

from tests.functional import (
    cleanup_db,
    create_default_ogcserver,
    create_dummy_request,
    setup_db,
)
from tests.functional import setup_common as setup_module  # noqa
from tests.functional import teardown_common as teardown_module  # noqa

if TYPE_CHECKING:
    from c2cgeoportal_commons.models.main import Metadata


class TestThemesEditColumns(TestCase):
    _table_index = 0

    def setup_method(self, _: Any) -> None:
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None

        setup_db()

        self._tables = []

        import transaction
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import (
            OGCSERVER_AUTH_NOAUTH,
            Interface,
            LayerGroup,
            Role,
            Theme,
            TreeItem,
        )
        from c2cgeoportal_commons.models.static import User

        for treeitem in DBSession.query(TreeItem).all():
            DBSession.delete(treeitem)

        self.role = Role(name="__test_role")
        self.user = User(
            username="__test_user",
            password="__test_user",
            settings_role=self.role,
            roles=[self.role],
        )
        self.main = Interface(name="main")

        self.ogc_server = create_default_ogcserver(DBSession)
        self.ogc_server.auth = OGCSERVER_AUTH_NOAUTH

        self.metadata = None
        self.layer_ids = []

        self.layer_group_1 = LayerGroup(name="__test_layer_group_1")

        theme = Theme(name="__test_theme")
        theme.interfaces = [self.main]
        theme.children = [self.layer_group_1]

        DBSession.add_all([self.main, self.user, self.role, theme, self.layer_group_1])

        transaction.commit()

    def teardown_method(self, _: Any) -> None:
        import transaction
        from c2cgeoportal_commons.models import DBSession

        cleanup_db()

        for table in self._tables[::-1]:
            table.drop(checkfirst=True, bind=DBSession.c2c_rw_bind)

        transaction.commit()

    def _create_layer(
        self,
        exclude_properties: bool = False,
        metadatas: list["Metadata"] | None = None,
        geom_type: bool = False,
    ) -> int:
        """
        This function is central for this test class.

        It creates a layer with two features, and associates a restriction area to it.
        """
        import transaction
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import LayerWMS, RestrictionArea
        from geoalchemy2 import Geometry
        from sqlalchemy import Column, ForeignKey, Table, types
        from sqlalchemy.ext.declarative import declarative_base

        self.__class__._table_index += 1
        id = self.__class__._table_index

        engine = DBSession.c2c_rw_bind
        with engine.begin() as connection:
            if not self.metadata:
                self.metadata = declarative_base().metadata

            tablename = f"geo_table_{id}"
            schemaname = "geodata"

            table1 = Table(
                f"{tablename!s}_child",
                self.metadata,
                Column("id", types.Integer, primary_key=True),
                Column("name", types.Unicode),
                schema=schemaname,
            )

            self._tables.append(table1)

            table2 = Table(
                tablename,
                self.metadata,
                Column("id", types.Integer, primary_key=True),
                Column("child_id", types.Integer, ForeignKey(f"{schemaname}.{tablename}_child.id")),
                Column("name", types.Unicode, nullable=False),
                Column("deleted", types.Boolean),
                Column("last_update_user", types.Unicode),
                Column("last_update_date", types.DateTime),
                Column("date", types.Date),
                Column("start_time", types.Time),
                # Column("interval", Interval()),
                Column("short_name1", types.String, nullable=True),
                Column("short_name2", types.String(50), nullable=True),
                Column("short_number", types.Integer, nullable=True),
                Column("double_number", types.Float(precision=4)),
                Column("large_binary", types.LargeBinary(length=60), nullable=True),
                Column("value", types.Enum("one", "two", "three", name="an_enum_value")),
                Column("numeric", types.Numeric(precision=5, scale=2), nullable=True),
                Column("numeric2", types.Numeric(), nullable=True),
                schema=schemaname,
            )
            if geom_type:
                table2.append_column(Column("geom", Geometry("POINT", srid=21781)))
            else:
                table2.append_column(Column("geom", Geometry(srid=21781)))

            self._tables.append(table2)

            table2.drop(checkfirst=True, bind=engine)
            table1.drop(checkfirst=True, bind=engine)
            table1.create(bind=engine)
            table2.create(bind=engine)

            ins = table1.insert().values(name="c1é")
            print(connection.execute(ins).inserted_primary_key[0])
            ins = table1.insert().values(name="c2é")
            print(connection.execute(ins).inserted_primary_key[0])

            layer = LayerWMS(name="test_WMS_1", public=True)
            layer.layer = "testpoint_unprotected"
            layer.id = id
            layer.geo_table = f"{schemaname}.{tablename}"
            layer.interfaces = [self.main]
            layer.ogc_server = self.ogc_server

            if exclude_properties:
                layer.exclude_properties = "name"

            if metadatas:
                layer.metadatas = metadatas

            DBSession.add(self.layer_group_1)
            self.layer_group_1.children = [*self.layer_group_1.children, layer]

            DBSession.add(self.layer_group_1)

            ra = RestrictionArea()
            ra.name = "__test_ra"
            ra.layers = [layer]
            ra.roles = [self.role]
            ra.readwrite = True
            DBSession.add(ra)

            transaction.commit()

            self.layer_ids.append(id)
            return id

    @staticmethod
    def _get_request(layerid, username=None, params=None) -> None:
        if params is None:
            params = {}

        request = create_dummy_request(user=username)
        request.route_url = lambda name, _query: f"http://server/{name}?{urlencode(_query)}"
        request.matchdict = {"layer_id": str(layerid)}
        request.params = params
        return request

    def test_themes_edit_columns(self) -> None:
        from c2cgeoportal_geoportal.views.theme import Theme

        layer_id = self._create_layer(geom_type=True)

        theme_view = Theme(self._get_request(layer_id, username="__test_user", params={"interface": "main"}))

        themes = theme_view.themes()
        layers = themes["themes"][0]["children"][0]["children"]

        self.assertEqual(
            [layer["edit_columns"] for layer in layers],
            [
                [
                    {"nillable": True, "type": "xsd:integer", "name": "child_id"},
                    {"type": "xsd:string", "name": "name"},
                    {"nillable": True, "type": "xsd:boolean", "name": "deleted"},
                    {"nillable": True, "type": "xsd:string", "name": "last_update_user"},
                    {"nillable": True, "type": "xsd:dateTime", "name": "last_update_date"},
                    {"nillable": True, "type": "xsd:date", "name": "date"},
                    {
                        "nillable": True,
                        "type": "xsd:time",
                        "name": "start_time",
                        # }, {
                        #     "nillable": True,
                        #     "type": "xsd:duration",
                        #     "name": "interval"
                    },
                    {"nillable": True, "type": "xsd:string", "name": "short_name1"},
                    {"nillable": True, "type": "xsd:string", "name": "short_name2", "maxLength": 50},
                    {"nillable": True, "type": "xsd:integer", "name": "short_number"},
                    {"nillable": True, "type": "xsd:double", "name": "double_number"},
                    {"nillable": True, "type": "xsd:base64Binary", "name": "large_binary"},
                    {
                        "enumeration": ["one", "two", "three"],
                        "type": "xsd:string",
                        "name": "value",
                        "nillable": True,
                        "restriction": "enumeration",
                    },
                    {
                        "fractionDigits": 2,
                        "nillable": True,
                        "type": "xsd:decimal",
                        "name": "numeric",
                        "totalDigits": 5,
                    },
                    {"nillable": True, "type": "xsd:decimal", "name": "numeric2"},
                    {"srid": 21781, "nillable": True, "type": "gml:PointPropertyType", "name": "geom"},
                    {
                        "restriction": "enumeration",
                        "nillable": True,
                        "type": "xsd:string",
                        "name": "child",
                        "enumeration": ["c1\xe9", "c2\xe9"],
                    },
                ],
            ],
        )

    def test_themes_edit_columns_extras(self) -> None:
        from c2cgeoportal_commons.models.main import Metadata
        from c2cgeoportal_geoportal.views.theme import Theme

        metadatas = [
            Metadata("lastUpdateDateColumn", "last_update_date"),
            Metadata("lastUpdateUserColumn", "last_update_user"),
        ]
        layer_id = self._create_layer(geom_type=False, exclude_properties=True, metadatas=metadatas)
        theme_view = Theme(self._get_request(layer_id, username="__test_user", params={"interface": "main"}))

        themes = theme_view.themes()
        assert themes["errors"] == []
        layers = themes["themes"][0]["children"][0]["children"]

        self.assertEqual(
            [layer["edit_columns"] for layer in layers],
            [
                [
                    {"nillable": True, "type": "xsd:integer", "name": "child_id"},
                    {"nillable": True, "type": "xsd:boolean", "name": "deleted"},
                    {"nillable": True, "type": "xsd:date", "name": "date"},
                    {
                        "nillable": True,
                        "type": "xsd:time",
                        "name": "start_time",
                        # }, {
                        #     "nillable": True,
                        #     "type": "xsd:duration",
                        #     "name": "interval"
                    },
                    {"nillable": True, "type": "xsd:string", "name": "short_name1"},
                    {"nillable": True, "type": "xsd:string", "name": "short_name2", "maxLength": 50},
                    {"nillable": True, "type": "xsd:integer", "name": "short_number"},
                    {"nillable": True, "type": "xsd:double", "name": "double_number"},
                    {"nillable": True, "type": "xsd:base64Binary", "name": "large_binary"},
                    {
                        "enumeration": ["one", "two", "three"],
                        "type": "xsd:string",
                        "name": "value",
                        "nillable": True,
                        "restriction": "enumeration",
                    },
                    {
                        "fractionDigits": 2,
                        "nillable": True,
                        "type": "xsd:decimal",
                        "name": "numeric",
                        "totalDigits": 5,
                    },
                    {"name": "numeric2", "type": "xsd:decimal", "nillable": True},
                    {"srid": 21781, "nillable": True, "type": "gml:GeometryPropertyType", "name": "geom"},
                    {
                        "restriction": "enumeration",
                        "nillable": True,
                        "type": "xsd:string",
                        "name": "child",
                        "enumeration": ["c1\xe9", "c2\xe9"],
                    },
                ],
            ],
        )
