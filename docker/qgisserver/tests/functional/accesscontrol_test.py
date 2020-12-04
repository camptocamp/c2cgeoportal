# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020, Camptocamp SA
# All rights reserved.

# This program is free software; you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.

from unittest.mock import Mock

import pytest
from geoalchemy2.shape import from_shape
from geomapfish_qgisserver.accesscontrol import (
    Access,
    GeoMapFishAccessControl,
    GMFException,
    OGCServerAccessControl,
)
from qgis.core import QgsProject, QgsVectorLayer
from shapely.geometry import box

area1 = box(485869.5728, 76443.1884, 837076.5648, 299941.7864)


def set_request_parameters(server_iface, params):
    server_iface.configure_mock(
        **{
            "requestHandler.return_value": Mock(
                **{"parameterMap.return_value": params, "parameter.side_effect": lambda key: params[key]}
            )
        }
    )


def add_node_in_qgis_project(project, parent_node, node_def):

    if node_def["type"] == "layer":
        vlayer = QgsVectorLayer("Point", node_def["name"], "memory")
        if "shortName" in node_def:
            vlayer.setShortName(node_def["shortName"])
        project.addMapLayer(vlayer)
        node = project.layerTreeRoot().findLayer(vlayer)
        clone = node.clone()
        parent_node.addChildNode(clone)
        node.parent().takeChild(node)

    if node_def["type"] == "group":
        node = parent_node.addGroup(node_def["name"])
        if "shortName" in node_def:
            node.setCustomProperty("wmsShortName", node_def["shortName"])
        for child_def in node_def["children"]:
            add_node_in_qgis_project(project, node, child_def)


@pytest.fixture(scope="module")
def test_data(clean_dbsession):
    from c2cgeoportal_commons.models.main import (
        OGCSERVER_AUTH_STANDARD,
        OGCSERVER_TYPE_QGISSERVER,
        LayerWMS,
        OGCServer,
        RestrictionArea,
        Role,
    )
    from c2cgeoportal_commons.models.static import User

    DBSession = clean_dbsession  # noqa: N806

    dbsession = DBSession()

    ogc_server1 = OGCServer(
        name="qgisserver1",
        type_=OGCSERVER_TYPE_QGISSERVER,
        image_type="image/png",
        auth=OGCSERVER_AUTH_STANDARD,
    )
    ogc_server2 = OGCServer(
        name="qgisserver2",
        type_=OGCSERVER_TYPE_QGISSERVER,
        image_type="image/png",
        auth=OGCSERVER_AUTH_STANDARD,
    )
    dbsession.add_all((ogc_server1, ogc_server2))

    role1 = Role("role1")
    role2 = Role("role2")
    dbsession.add_all((role1, role2))

    root = User("root")
    root.id = 0
    user1 = User("user1", roles=[role1])
    user2 = User("user12", roles=[role1, role2])
    dbsession.add_all((root, user1, user2))

    project = QgsProject.instance()

    for node in [
        {
            "name": "root",
            "type": "group",
            "children": [
                {
                    "name": "public_group",
                    "type": "group",
                    "children": [{"name": "public_layer", "type": "layer"}],
                },
                {
                    "name": "private_group1",
                    "type": "group",
                    "children": [{"name": "private_layer1", "type": "layer"}],
                },
                {
                    "name": "private_group2",
                    "type": "group",
                    "children": [{"name": "private_layer2", "type": "layer"}],
                },
                # For group and layer short names
                {
                    "name": "private_group3",
                    "type": "group",
                    "shortName": "pg3",
                    "children": [{"name": "private_layer3", "type": "layer", "shortName": "pl3"}],
                },
            ],
        }
    ]:
        add_node_in_qgis_project(project, project.layerTreeRoot(), node)

    public_group = LayerWMS(name="public_group", layer="public_group", public=True)
    public_group.ogc_server = ogc_server1

    public_layer = LayerWMS(name="public_layer", layer="public_layer", public=True)
    public_layer.ogc_server = ogc_server1

    private_layer1 = LayerWMS(name="private_layer1", layer="private_layer1", public=False)
    private_layer1.ogc_server = ogc_server1

    private_layer2 = LayerWMS(name="private_layer2", layer="private_layer2", public=False)
    private_layer2.ogc_server = ogc_server1

    private_group3 = LayerWMS(name="private_group3", layer="pg3", public=False)
    private_group3.ogc_server = ogc_server1

    private_layer3 = LayerWMS(name="private_layer3", layer="pl3", public=False)
    private_layer3.ogc_server = ogc_server1

    dbsession.add_all(
        (
            public_group,
            public_layer,
            private_layer1,
            private_layer2,
            private_group3,
            private_layer3,
        )
    )

    ra1 = RestrictionArea(
        "restriction_area1",
        layers=[private_layer1, private_layer3],
        roles=[role1],
        area=from_shape(area1, srid=21781),
    )
    ra2 = RestrictionArea("restriction_area2", layers=[private_layer2], roles=[role2], readwrite=True)
    dbsession.add_all((ra1, ra2))

    dbsession.flush()

    users = {
        user.username: {"id": user.id, "role_ids": [r.id for r in user.roles]}
        for user in (root, user1, user2)
    }
    roles = {role.name: {"id": role.id} for role in (role1, role2)}

    dbsession.commit()
    dbsession.close()

    yield {
        # "ogc_servers": ogc_servers,
        "roles": roles,
        "users": users,
        # "layers": layers,
        # "restriction_areas": restriction_areas,
        "project": project,
    }


@pytest.fixture(scope="function")
def wms_use_layer_ids(test_data):
    """
    Activate WMSUseLayerIDs
    """
    project = test_data["project"]
    try:
        project.writeEntry("WMSUseLayerIDs", "/", True)
        yield
    finally:
        project.writeEntry("WMSUseLayerIDs", "/", False)


@pytest.mark.usefixtures("server_iface", "qgs_access_control_filter", "test_data")
class TestOGCServerAccessControl:
    def test_init(self, server_iface, DBSession, test_data):  # noqa: N803
        dbsession = DBSession()
        ogcserver_accesscontrol = OGCServerAccessControl(
            server_iface, "qgisserver1", "no_project", 21781, lambda: dbsession
        )
        assert ogcserver_accesscontrol.ogcserver.name == "qgisserver1"

    def test_ogc_layer_name(self, server_iface, DBSession, test_data):  # noqa: N803
        dbsession = DBSession()
        ogcserver_accesscontrol = OGCServerAccessControl(
            server_iface, "qgisserver1", "no_project", 21781, lambda: dbsession
        )
        ogcserver_accesscontrol.project = test_data["project"]
        for layer_name, expected in (
            ("private_layer1", "private_layer1"),
            ("private_layer3", "pl3"),
        ):
            layer = test_data["project"].mapLayersByName(layer_name)[0]
            assert expected == ogcserver_accesscontrol.ogc_layer_name(layer)

    @pytest.mark.usefixtures("wms_use_layer_ids")
    def test_ogc_layer_with_wms_use_layer_ids(self, server_iface, DBSession, test_data):  # noqa: N803
        dbsession = DBSession()
        ogcserver_accesscontrol = OGCServerAccessControl(
            server_iface, "qgisserver1", "no_project", 21781, lambda: dbsession
        )
        ogcserver_accesscontrol.project = test_data["project"]
        layer = test_data["project"].mapLayersByName("private_layer1")[0]
        assert layer.id() == ogcserver_accesscontrol.ogc_layer_name(layer)

    def test_get_layers(self, server_iface, DBSession, test_data):  # noqa: N803
        dbsession = DBSession()
        ogcserver_accesscontrol = OGCServerAccessControl(
            server_iface, "qgisserver1", "no_project", 21781, lambda: dbsession
        )
        ogcserver_accesscontrol.project = test_data["project"]

        expected = {
            "public_group": ["public_group"],
            "public_layer": ["public_group", "public_layer"],
            "private_layer1": ["private_layer1"],
            "private_layer2": ["private_layer2"],
            "pg3": ["private_group3"],
            "pl3": ["private_group3", "private_layer3"],
        }

        layers = ogcserver_accesscontrol.get_layers(dbsession)

        assert set(expected.keys()) == set(layers.keys())
        for key in expected.keys():
            assert set(expected[key]) == {layer.name for layer in layers[key]}

    def test_get_roles(self, server_iface, DBSession, test_data):  # noqa: N803
        dbsession = DBSession()
        ogcserver_accesscontrol = OGCServerAccessControl(
            server_iface, "qgisserver1", "no_project", 21781, lambda: dbsession
        )

        set_request_parameters(server_iface, {"USER_ID": "0"})
        assert "ROOT" == ogcserver_accesscontrol.get_roles(dbsession)

        test_users = test_data["users"]
        test_roles = test_data["roles"]

        for user_name, expected_role_names in (
            ("user1", ("role1",)),
            ("user12", ("role1", "role2")),
        ):
            set_request_parameters(
                server_iface,
                {
                    "USER_ID": str(test_users[user_name]["id"]),
                    "ROLE_IDS": ",".join([str(test_roles[r]["id"]) for r in expected_role_names]),
                },
            )
            expected_roles = {
                test_roles[expected_role_name]["id"] for expected_role_name in expected_role_names
            }
            assert expected_roles == {role.id for role in ogcserver_accesscontrol.get_roles(dbsession)}

    def test_get_restriction_areas(self, server_iface, DBSession, test_data):  # noqa: N803
        from c2cgeoportal_commons.models.main import LayerWMS, Role

        dbsession = DBSession()
        ogcserver_accesscontrol = OGCServerAccessControl(
            server_iface, "qgisserver1", "no_project", 21781, lambda: dbsession
        )

        assert (Access.FULL, None) == ogcserver_accesscontrol.get_restriction_areas(
            dbsession.query(LayerWMS).filter(LayerWMS.name == "private_layer1").one(),
            read_write=True,
            roles="ROOT",
        )

        for layer_names, rw, role_names, expected in (
            (("private_layer1",), False, ("role1",), (Access.AREA, [area1])),
            (("private_layer3",), False, ("role1",), (Access.AREA, [area1])),
        ):
            layers = [
                dbsession.query(LayerWMS).filter(LayerWMS.name == layer_name).one()
                for layer_name in layer_names
            ]
            roles = [dbsession.query(Role).filter(Role.name == role_name).one() for role_name in role_names]
            ras = ogcserver_accesscontrol.get_restriction_areas(layers, rw, roles)
            assert expected == ras, "get_restriction_areas with {} should return {}".format(
                (layer_names, rw, role_names), expected
            )

    def test_get_area(self, server_iface, DBSession, test_data):  # noqa: N803
        dbsession = DBSession()
        ogcserver_accesscontrol = OGCServerAccessControl(
            server_iface, "qgisserver1", "no_project", 21781, lambda: dbsession
        )
        ogcserver_accesscontrol.project = test_data["project"]

        for user_name, layer_name, expected in [
            ("root", layer_name, (Access.FULL, None))
            for layer_name in ("public_layer", "private_layer1", "private_layer2", "private_layer3")
        ] + [
            ("user1", "public_layer", (Access.FULL, None)),
            ("user1", "private_layer1", (Access.AREA, area1.wkt)),
            ("user1", "private_layer2", (Access.NO, None)),
            ("user1", "private_layer3", (Access.AREA, area1.wkt)),
        ]:
            user = test_data["users"][user_name]
            set_request_parameters(
                server_iface,
                {"USER_ID": str(user["id"]), "ROLE_IDS": ",".join([str(r) for r in user["role_ids"]])},
            )
            layer = test_data["project"].mapLayersByName(layer_name)[0]
            access, area = ogcserver_accesscontrol.get_area(layer, dbsession)
            assert expected == (
                access,
                area.wkt if area else None,
            ), 'get_area with "{}", "{}" should return {}'.format(user_name, layer_name, expected)

    @staticmethod
    def test_layer_permissions(server_iface, DBSession, test_data):  # noqa: N803
        dbsession = DBSession()
        ogcserver_accesscontrol = OGCServerAccessControl(
            server_iface, "qgisserver1", "no_project", 21781, lambda: dbsession
        )
        ogcserver_accesscontrol.project = test_data["project"]

        for user_name, layer_name, expected in (
            (
                "user1",
                "public_layer",
                {"canDelete": False, "canInsert": False, "canRead": True, "canUpdate": False},
            ),
            (
                "user1",
                "private_layer1",
                {"canDelete": False, "canInsert": False, "canRead": True, "canUpdate": False},
            ),
            (
                "user12",
                "private_layer2",
                {"canDelete": True, "canInsert": True, "canRead": True, "canUpdate": True},
            ),
        ):
            user = test_data["users"][user_name]
            set_request_parameters(
                server_iface,
                {"USER_ID": str(user["id"]), "ROLE_IDS": ",".join([str(r) for r in user["role_ids"]])},
            )
            layer = test_data["project"].mapLayersByName(layer_name)[0]
            permissions = ogcserver_accesscontrol.layerPermissions(layer)
            for key, value in expected.items():
                assert value == getattr(permissions, key)

    @staticmethod
    def test_cache_key(server_iface, DBSession, test_data):  # noqa: N803
        dbsession = DBSession()
        ogcserver_accesscontrol = OGCServerAccessControl(
            server_iface, "qgisserver1", "no_project", 21781, lambda: dbsession
        )

        set_request_parameters(server_iface, {"Host": "example.com", "USER_ID": "0"})
        assert "0" == server_iface.requestHandler().parameter("USER_ID")
        assert "example.com" == server_iface.requestHandler().parameter("Host")
        assert "example.com--1" == ogcserver_accesscontrol.cacheKey()

        user = test_data["users"]["user12"]
        role1 = test_data["roles"]["role1"]
        role2 = test_data["roles"]["role2"]
        set_request_parameters(
            server_iface,
            {
                "Host": "example.com",
                "USER_ID": str(user["id"]),
                "ROLE_IDS": "{},{}".format(role1["id"], role2["id"]),
            },
        )
        expected = "example.com-{},{}".format(role1["id"], role2["id"])
        assert expected == ogcserver_accesscontrol.cacheKey()


@pytest.mark.usefixtures(
    "server_iface",
    "qgs_access_control_filter",
    "test_data",
)
class TestUnavailableOGCServerAccessControl:
    def test_init(self, server_iface, DBSession):  # noqa: N803
        dbsession = DBSession()
        ogcserver_accesscontrol = OGCServerAccessControl(
            server_iface, "unavailable", "no_project", 21781, lambda: dbsession
        )
        assert ogcserver_accesscontrol.ogcserver is None

    def test_get_layers(self, server_iface, DBSession):  # noqa: N803
        dbsession = DBSession()
        ogcserver_accesscontrol = OGCServerAccessControl(
            server_iface, "unavailable", "no_project", 21781, lambda: dbsession
        )

        assert ogcserver_accesscontrol.get_layers(dbsession) == {}

    def test_layer_permissions(self, server_iface, DBSession, test_data):  # noqa: N803
        dbsession = DBSession()
        ogcserver_accesscontrol = OGCServerAccessControl(
            server_iface, "unavailable", "no_project", 21781, lambda: dbsession
        )

        for user_name, layer_name, expected in (
            (
                "user1",
                "public_layer",
                {"canDelete": False, "canInsert": False, "canRead": False, "canUpdate": False},
            ),
            (
                "user12",
                "private_layer2",
                {"canDelete": False, "canInsert": False, "canRead": False, "canUpdate": False},
            ),
        ):
            user = test_data["users"][user_name]
            set_request_parameters(server_iface, {"USER_ID": str(user["id"])})
            layer = test_data["project"].mapLayersByName(layer_name)[0]

            permissions = ogcserver_accesscontrol.layerPermissions(layer)
            for key, value in expected.items():
                assert value == getattr(permissions, key)

    def test_layer_filter_subset_string(self, server_iface, DBSession, test_data):  # noqa: N803
        dbsession = DBSession()
        ogcserver_accesscontrol = OGCServerAccessControl(
            server_iface, "unavailable", "no_project", 21781, lambda: dbsession
        )

        for user_name, layer_name, expected in (
            ("user1", "public_layer", "FALSE"),
            ("user12", "private_layer2", "FALSE"),
        ):
            user = test_data["users"][user_name]
            set_request_parameters(server_iface, {"USER_ID": str(user["id"])})
            layer = test_data["project"].mapLayersByName(layer_name)[0]
            assert ogcserver_accesscontrol.layerFilterSubsetString(layer) == expected

    def test_layer_filter_expression(self, server_iface, DBSession, test_data):  # noqa: N803
        dbsession = DBSession()
        ogcserver_accesscontrol = OGCServerAccessControl(
            server_iface, "unavailable", "no_project", 21781, lambda: dbsession
        )

        for user_name, layer_name, expected in (
            ("user1", "public_layer", "FALSE"),
            ("user12", "private_layer2", "FALSE"),
        ):
            user = test_data["users"][user_name]
            set_request_parameters(server_iface, {"USER_ID": str(user["id"])})

            layer = test_data["project"].mapLayersByName(layer_name)[0]
            assert ogcserver_accesscontrol.layerFilterExpression(layer) == expected


@pytest.mark.usefixtures("server_iface", "qgs_access_control_filter", "single_ogc_server_env", "test_data")
class TestGeoMapFishAccessControlSingleOGCServer:
    def test_init(self, server_iface):
        plugin = GeoMapFishAccessControl(server_iface)
        assert plugin.single is True
        assert isinstance(plugin.ogcserver_accesscontrol, OGCServerAccessControl)


@pytest.mark.usefixtures(
    "qgs_access_control_filter",
    "multiple_ogc_server_env",
    "test_data",
)
class TestGeoMapFishAccessControlMultipleOGCServer:
    @pytest.mark.usefixtures()
    def test_init(self, server_iface, test_data):
        plugin = GeoMapFishAccessControl(server_iface)
        assert plugin.single is False

        assert plugin.serverInterface() is server_iface

        set_request_parameters(server_iface, {"MAP": "qgsproject1"})
        assert plugin.serverInterface().requestHandler().parameterMap()["MAP"] == "qgsproject1"
        assert plugin.get_ogcserver_accesscontrol().ogcserver.name == "qgisserver1"

        set_request_parameters(server_iface, {"MAP": "qgsproject2"})
        assert plugin.serverInterface().requestHandler().parameterMap()["MAP"] == "qgsproject2"
        assert plugin.get_ogcserver_accesscontrol().ogcserver.name == "qgisserver2"

        set_request_parameters(server_iface, {"MAP": "unavailable"})
        assert plugin.serverInterface().requestHandler().parameterMap()["MAP"] == "unavailable"
        with pytest.raises(GMFException):
            plugin.get_ogcserver_accesscontrol()
