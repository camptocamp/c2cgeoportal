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


from urllib.parse import urlencode
from nose.plugins.attrib import attr
from unittest import TestCase

import sqlahelper
from tests.functional import (  # noqa
    tear_down_common as tearDownModule,
    set_up_common as setUpModule,
    create_dummy_request, create_default_ogcserver, cleanup_db,
)


@attr(functional=True)
class TestThemesEditColumns(TestCase):

    _table_index = 0

    def setUp(self):
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None

        cleanup_db()

        self._tables = []

        import transaction
        from c2cgeoportal.models import DBSession, Role, User, Interface, TreeItem, Theme, \
            LayerGroup, OGCSERVER_AUTH_NOAUTH
        from c2cgeoportal.lib.dbreflection import init

        for treeitem in DBSession.query(TreeItem).all():
            DBSession.delete(treeitem)

        self.role = Role(name="__test_role")
        self.user = User(
            username="__test_user",
            password="__test_user",
            role=self.role
        )
        self.main = Interface(name="main")

        self.ogc_server, external_ogc_server = create_default_ogcserver()
        self.ogc_server.auth = OGCSERVER_AUTH_NOAUTH
        external_ogc_server.auth = OGCSERVER_AUTH_NOAUTH

        self.metadata = None
        self.layer_ids = []

        self.layer_group_1 = LayerGroup(name="__test_layer_group_1")

        theme = Theme(name="__test_theme")
        theme.interfaces = [self.main]
        theme.children = [self.layer_group_1]

        DBSession.add_all([self.main, self.user, self.role, theme, self.layer_group_1])

        transaction.commit()

        engine = sqlahelper.get_engine()
        init(engine)

    def tearDown(self):  # noqa
        import transaction

        cleanup_db()

        for table in self._tables[::-1]:
            table.drop(checkfirst=True)

        transaction.commit()

    def _create_layer(self, exclude_properties=False, metadatas=None, geom_type=False):
        """ This function is central for this test class. It creates
        a layer with two features, and associates a restriction area
        to it. """
        import transaction
        import sqlahelper
        from sqlalchemy import Column, Table, types, ForeignKey
        from sqlalchemy.ext.declarative import declarative_base
        from geoalchemy2 import Geometry
        from c2cgeoportal.models import DBSession, RestrictionArea, LayerWMS

        self.__class__._table_index += 1
        id = self.__class__._table_index

        engine = sqlahelper.get_engine()
        connection = engine.connect()

        if not self.metadata:
            self.metadata = declarative_base(bind=engine).metadata

        tablename = "geo_table_{0:d}".format(id)
        schemaname = "geodata"

        table1 = Table(
            "{0!s}_child".format(tablename), self.metadata,
            Column("id", types.Integer, primary_key=True),
            Column("name", types.Unicode),
            schema=schemaname
        )

        self._tables.append(table1)

        table2 = Table(
            tablename, self.metadata,
            Column("id", types.Integer, primary_key=True),
            Column("child_id", types.Integer,
                   ForeignKey("{0!s}.{1!s}_child.id".format(schemaname, tablename))),
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
            schema=schemaname
        )
        if geom_type:
            table2.append_column(
                Column("geom", Geometry("POINT", srid=21781))
            )
        else:
            table2.append_column(
                Column("geom", Geometry(srid=21781))
            )

        self._tables.append(table2)

        table2.drop(checkfirst=True)
        table1.drop(checkfirst=True)
        table1.create()
        table2.create()

        ins = table1.insert().values(name="c1é")
        connection.execute(ins).inserted_primary_key[0]
        ins = table1.insert().values(name="c2é")
        connection.execute(ins).inserted_primary_key[0]

        layer = LayerWMS(name="test_WMS_1", public=True)
        layer.layer = "test_wms"
        layer.id = id
        layer.geo_table = "{0!s}.{1!s}".format(schemaname, tablename)
        layer.interfaces = [self.main]
        layer.ogc_server = self.ogc_server

        if exclude_properties:
            layer.exclude_properties = "name"

        if metadatas:
            layer.metadatas = metadatas

        DBSession.add(self.layer_group_1)
        self.layer_group_1.children = self.layer_group_1.children + [layer]

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
    def _get_request(layerid, username=None, params=None):
        if params is None:
            params = {}

        request = create_dummy_request(user=username)
        request.static_url = lambda url: "/dummy/static/url"
        request.route_url = lambda name, _query: "http://server/{}?{}".format(name, urlencode(_query))
        request.matchdict = {"layer_id": str(layerid)}
        request.params = params
        return request

    def test_themes_edit_columns(self):
        from c2cgeoportal.views.entry import Entry

        layer_id = self._create_layer(geom_type=True)
        entry = Entry(self._get_request(layer_id, username="__test_user", params={
            "version": "2",
            "interface": "main"
        }))

        themes = entry.themes()
        layers = themes["themes"][0]["children"][0]["children"]

        self.assertEqual(
            [layer["edit_columns"] for layer in layers],
            [[{
                "nillable": True,
                "type": "xsd:integer",
                "name": "child_id"
            }, {
                "type": "xsd:string",
                "name": "name"
            }, {
                "nillable": True,
                "type": "xsd:boolean",
                "name": "deleted"
            }, {
                "nillable": True,
                "type": "xsd:string",
                "name": "last_update_user"
            }, {
                "nillable": True,
                "type": "xsd:dateTime",
                "name": "last_update_date"
            }, {
                "nillable": True,
                "type": "xsd:date",
                "name": "date"
            }, {
                "nillable": True,
                "type": "xsd:time",
                "name": "start_time"
                # }, {
                #     "nillable": True,
                #     "type": "xsd:duration",
                #     "name": "interval"
            }, {
                "nillable": True,
                "type": "xsd:string",
                "name": "short_name1"
            }, {
                "nillable": True,
                "type": "xsd:string",
                "name": "short_name2",
                "maxLength": 50
            }, {
                "nillable": True,
                "type": "xsd:integer",
                "name": "short_number"
            }, {
                "nillable": True,
                "type": "xsd:double",
                "name": "double_number"
            }, {
                "nillable": True,
                "type": "xsd:base64Binary",
                "name": "large_binary"
            }, {
                "enumeration": [
                    "one",
                    "two",
                    "three",
                ],
                "type": "xsd:string",
                "name": "value",
                "nillable": True,
                "restriction": "enumeration"
            }, {
                "fractionDigits": 2,
                "nillable": True,
                "type": "xsd:decimal",
                "name": "numeric",
                "totalDigits": 5
            }, {
                "nillable": True,
                "type": "xsd:decimal",
                "name": "numeric2"
            }, {
                "srid": 21781,
                "nillable": True,
                "type": "gml:PointPropertyType",
                "name": "geom"
            }, {
                "restriction": "enumeration",
                "nillable": True,
                "type": "xsd:string",
                "name": "child",
                "enumeration": [
                    "c1\xe9",
                    "c2\xe9"
                ]
            }]]
        )

    def test_themes_edit_columns_extras(self):
        from c2cgeoportal.views.entry import Entry
        from c2cgeoportal.models import Metadata

        metadatas = [
            Metadata("lastUpdateDateColumn", "last_update_date"),
            Metadata("lastUpdateUserColumn", "last_update_user"),
        ]
        layer_id = self._create_layer(geom_type=False, exclude_properties=True, metadatas=metadatas)
        entry = Entry(self._get_request(layer_id, username="__test_user", params={
            "version": "2",
            "interface": "main"
        }))

        themes = entry.themes()
        layers = themes["themes"][0]["children"][0]["children"]

        self.assertEqual(
            [layer["edit_columns"] for layer in layers],
            [[{
                "nillable": True,
                "type": "xsd:integer",
                "name": "child_id"
            }, {
                "nillable": True,
                "type": "xsd:boolean",
                "name": "deleted"
            }, {
                "nillable": True,
                "type": "xsd:date",
                "name": "date"
            }, {
                "nillable": True,
                "type": "xsd:time",
                "name": "start_time"
                # }, {
                #     "nillable": True,
                #     "type": "xsd:duration",
                #     "name": "interval"
            }, {
                "nillable": True,
                "type": "xsd:string",
                "name": "short_name1"
            }, {
                "nillable": True,
                "type": "xsd:string",
                "name": "short_name2",
                "maxLength": 50
            }, {
                "nillable": True,
                "type": "xsd:integer",
                "name": "short_number"
            }, {
                "nillable": True,
                "type": "xsd:double",
                "name": "double_number"
            }, {
                "nillable": True,
                "type": "xsd:base64Binary",
                "name": "large_binary"
            }, {
                "enumeration": [
                    "one",
                    "two",
                    "three",
                ],
                "type": "xsd:string",
                "name": "value",
                "nillable": True,
                "restriction": "enumeration"
            }, {
                "fractionDigits": 2,
                "nillable": True,
                "type": "xsd:decimal",
                "name": "numeric",
                "totalDigits": 5,
            }, {
                "name": "numeric2",
                "type": "xsd:decimal",
                "nillable": True
            }, {
                "srid": 21781,
                "nillable": True,
                "type": "gml:GeometryPropertyType",
                "name": "geom"
            }, {
                "restriction": "enumeration",
                "nillable": True,
                "type": "xsd:string",
                "name": "child",
                "enumeration": [
                    "c1\xe9",
                    "c2\xe9"
                ]
            }]]
        )
